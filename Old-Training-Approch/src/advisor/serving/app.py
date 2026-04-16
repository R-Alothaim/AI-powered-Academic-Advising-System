"""FastAPI inference endpoint for the distilled student model."""

from __future__ import annotations

import os

import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

CHECKPOINT = os.getenv("MODEL_CHECKPOINT", "outputs/distill/best")
SYSTEM_PROMPT = (
    "You are an academic advisor. Answer questions using only the official "
    "study plan. If the information is not present, reply: "
    "\"I don't have that information in the study plan.\""
)


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    question: str
    answer: str


def create_app() -> FastAPI:
    app = FastAPI(
        title="Academic Advisor",
        version="beta-1.0.9",
        description="AI-powered academic advising — answers study-plan questions via a distilled LLM.",
    )

    _state: dict = {}

    @app.on_event("startup")
    def load_model() -> None:
        tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
        model = AutoModelForCausalLM.from_pretrained(
            CHECKPOINT, torch_dtype=torch.bfloat16, device_map="auto",
        )
        model.eval()
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        _state["tokenizer"] = tokenizer
        _state["model"] = model

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ask", response_model=AskResponse)
    async def ask(req: AskRequest) -> AskResponse:
        tokenizer = _state["tokenizer"]
        model = _state["model"]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": req.question},
        ]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=512, do_sample=False)

        answer = tokenizer.decode(
            out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True,
        ).strip()

        return AskResponse(question=req.question, answer=answer)

    return app
