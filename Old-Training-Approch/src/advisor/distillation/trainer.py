"""Knowledge distillation training loop.

Loads the teacher in inference mode, trains the student against the combined
hard-label + soft-label objective.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    get_scheduler,
)

from advisor.distillation.losses import distillation_loss

logger = logging.getLogger(__name__)


class ChatDataset(Dataset):
    """Tokenize chat records into input_ids and labels for causal LM training."""

    def __init__(
        self,
        records: list[dict[str, Any]],
        tokenizer: AutoTokenizer,
        max_length: int = 2048,
    ) -> None:
        self.examples: list[dict[str, torch.Tensor]] = []
        for rec in records:
            msgs = rec["messages"]
            # Build the full conversation text
            text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
            encoded = tokenizer(
                text,
                max_length=max_length,
                truncation=True,
                padding="max_length",
                return_tensors="pt",
            )
            input_ids = encoded["input_ids"].squeeze(0)
            attention_mask = encoded["attention_mask"].squeeze(0)

            # Labels: mask everything except the assistant turn
            labels = input_ids.clone()
            labels[attention_mask == 0] = -100

            # Mask system + user tokens (only train on assistant response)
            asst_text = msgs[2]["content"]
            asst_tokens = tokenizer(asst_text, add_special_tokens=False)["input_ids"]
            asst_len = len(asst_tokens)
            # Mask all tokens before the assistant response
            labels[: labels.size(0) - asst_len] = -100

            self.examples.append({
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": labels,
            })

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        return self.examples[idx]


class DistillationTrainer:
    """Orchestrates the knowledge distillation training loop."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _load_teacher(self) -> tuple[AutoModelForCausalLM, AutoTokenizer]:
        cfg = self.config["teacher"]
        logger.info("Loading teacher model: %s", cfg["model_name"])
        tokenizer = AutoTokenizer.from_pretrained(cfg["model_name"])
        model = AutoModelForCausalLM.from_pretrained(
            cfg["model_name"],
            torch_dtype=getattr(torch, cfg["torch_dtype"]),
            device_map=cfg["device_map"],
        )
        model.eval()
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        return model, tokenizer

    def _load_student(self) -> AutoModelForCausalLM:
        cfg = self.config["student"]
        logger.info("Loading student model: %s", cfg["model_name"])
        model = AutoModelForCausalLM.from_pretrained(
            cfg["model_name"],
            torch_dtype=getattr(torch, cfg["torch_dtype"]),
            device_map=cfg["device_map"],
        )
        model.train()
        return model

    def train(
        self,
        train_records: list[dict[str, Any]],
        val_records: list[dict[str, Any]],
    ) -> Path:
        """Run the distillation loop. Returns path to best checkpoint."""
        teacher, tokenizer = self._load_teacher()
        student = self._load_student()

        t_cfg = self.config["training"]
        d_cfg = self.config["distillation"]
        max_len = self.config["teacher"]["max_length"]

        train_ds = ChatDataset(train_records, tokenizer, max_len)
        val_ds = ChatDataset(val_records, tokenizer, max_len)

        train_loader = DataLoader(
            train_ds,
            batch_size=t_cfg["per_device_train_batch_size"],
            shuffle=True,
        )
        val_loader = DataLoader(
            val_ds,
            batch_size=t_cfg["per_device_eval_batch_size"],
            shuffle=False,
        )

        optimizer = torch.optim.AdamW(
            student.parameters(),
            lr=t_cfg["learning_rate"],
            weight_decay=t_cfg["weight_decay"],
        )

        num_training_steps = len(train_loader) * t_cfg["epochs"] // t_cfg["gradient_accumulation_steps"]
        scheduler = get_scheduler(
            t_cfg["lr_scheduler_type"],
            optimizer=optimizer,
            num_warmup_steps=int(num_training_steps * t_cfg["warmup_ratio"]),
            num_training_steps=num_training_steps,
        )

        output_dir = Path(t_cfg["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        best_val_loss = float("inf")
        best_checkpoint = output_dir / "best"

        global_step = 0
        for epoch in range(t_cfg["epochs"]):
            student.train()
            epoch_loss = 0.0

            for step, batch in enumerate(train_loader):
                batch = {k: v.to(self.device) for k, v in batch.items()}

                with torch.no_grad():
                    teacher_out = teacher(
                        input_ids=batch["input_ids"],
                        attention_mask=batch["attention_mask"],
                    )

                student_out = student(
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                )

                loss, loss_dict = distillation_loss(
                    student_logits=student_out.logits,
                    teacher_logits=teacher_out.logits,
                    labels=batch["labels"],
                    temperature=d_cfg["temperature"],
                    alpha_ce=d_cfg["alpha_ce"],
                    alpha_kd=d_cfg["alpha_kd"],
                    label_smoothing=d_cfg.get("label_smoothing", 0.0),
                )

                loss = loss / t_cfg["gradient_accumulation_steps"]
                loss.backward()
                epoch_loss += loss.item()

                if (step + 1) % t_cfg["gradient_accumulation_steps"] == 0:
                    torch.nn.utils.clip_grad_norm_(student.parameters(), t_cfg["max_grad_norm"])
                    optimizer.step()
                    scheduler.step()
                    optimizer.zero_grad()
                    global_step += 1

                    if global_step % t_cfg["logging_steps"] == 0:
                        logger.info(
                            "epoch %d | step %d | loss_ce=%.4f loss_kd=%.4f total=%.4f lr=%.2e",
                            epoch + 1, global_step,
                            loss_dict["loss_ce"], loss_dict["loss_kd"], loss_dict["loss_total"],
                            scheduler.get_last_lr()[0],
                        )

                    if global_step % t_cfg["save_steps"] == 0:
                        ckpt_path = output_dir / f"checkpoint-{global_step}"
                        student.save_pretrained(ckpt_path)
                        tokenizer.save_pretrained(ckpt_path)
                        logger.info("Saved checkpoint to %s", ckpt_path)

            # Validation
            val_loss = self._validate(student, teacher, val_loader, d_cfg)
            logger.info("epoch %d | val_loss=%.4f", epoch + 1, val_loss)

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                student.save_pretrained(best_checkpoint)
                tokenizer.save_pretrained(best_checkpoint)
                logger.info("New best model saved to %s (val_loss=%.4f)", best_checkpoint, val_loss)

        logger.info("Training complete. Best val_loss=%.4f", best_val_loss)
        return best_checkpoint

    @torch.no_grad()
    def _validate(
        self,
        student: AutoModelForCausalLM,
        teacher: AutoModelForCausalLM,
        loader: DataLoader,
        d_cfg: dict[str, Any],
    ) -> float:
        student.eval()
        total_loss = 0.0
        for batch in loader:
            batch = {k: v.to(self.device) for k, v in batch.items()}
            teacher_out = teacher(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"])
            student_out = student(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"])
            loss, _ = distillation_loss(
                student_logits=student_out.logits,
                teacher_logits=teacher_out.logits,
                labels=batch["labels"],
                temperature=d_cfg["temperature"],
                alpha_ce=d_cfg["alpha_ce"],
                alpha_kd=d_cfg["alpha_kd"],
            )
            total_loss += loss.item()
        student.train()
        return total_loss / max(len(loader), 1)
