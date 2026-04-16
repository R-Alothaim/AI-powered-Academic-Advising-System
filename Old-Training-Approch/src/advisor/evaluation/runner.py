"""Run evaluation against a trained student checkpoint."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import torch
from rich.progress import Progress
from transformers import AutoModelForCausalLM, AutoTokenizer

from advisor.evaluation.metrics import compute_metrics

logger = logging.getLogger(__name__)


def run_evaluation(
    config: dict[str, Any],
    eval_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate predictions from the student model and compute metrics."""
    m_cfg = config["model"]
    ckpt = m_cfg.get("checkpoint_dir", m_cfg["model_name"])

    logger.info("Loading model from %s", ckpt)
    tokenizer = AutoTokenizer.from_pretrained(ckpt)
    model = AutoModelForCausalLM.from_pretrained(
        ckpt,
        torch_dtype=getattr(torch, m_cfg["torch_dtype"]),
        device_map=m_cfg["device_map"],
    )
    model.eval()

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    predictions: list[dict[str, Any]] = []

    with Progress() as progress:
        task = progress.add_task("Evaluating...", total=len(eval_records))
        for rec in eval_records:
            msgs = rec["messages"]
            prompt_msgs = msgs[:2]  # system + user
            expected = msgs[2]["content"]
            meta = rec.get("meta", {})

            prompt = tokenizer.apply_chat_template(
                prompt_msgs, tokenize=False, add_generation_prompt=True,
            )
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

            with torch.no_grad():
                output_ids = model.generate(
                    **inputs,
                    max_new_tokens=m_cfg["max_length"],
                    do_sample=False,
                )

            generated = tokenizer.decode(
                output_ids[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
            ).strip()

            predictions.append({
                "user_query": msgs[1]["content"],
                "expected": expected,
                "predicted": generated,
                "eval_label": meta.get("eval_label", ""),
                "category": meta.get("category", ""),
            })
            progress.advance(task)

    results = compute_metrics(predictions)

    # Persist
    out_dir = Path(config["output"]["report_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    if config["output"].get("save_predictions"):
        pred_path = out_dir / "predictions.jsonl"
        with pred_path.open("w") as fh:
            for p in predictions:
                fh.write(json.dumps(p, ensure_ascii=False) + "\n")

    report_path = out_dir / "metrics.json"
    with report_path.open("w") as fh:
        json.dump(results, fh, indent=2)
    logger.info("Report saved to %s", report_path)

    # Threshold checks
    for name, threshold in config.get("thresholds", {}).items():
        actual = results.get(name, 0)
        status = "PASS" if actual >= threshold else "FAIL"
        logger.info("%s: %.3f (>= %.3f) → %s", name, actual, threshold, status)

    return results
