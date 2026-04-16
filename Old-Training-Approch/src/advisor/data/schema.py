"""Pydantic schemas for validating chat-format JSONL records."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator

_VALID_ROLES = ("system", "user", "assistant")


class ChatMessage(BaseModel):
    role: str
    content: str

    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, v: str) -> str:
        if v not in _VALID_ROLES:
            raise ValueError(f"Invalid role '{v}', expected one of {_VALID_ROLES}")
        return v

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message content must not be empty")
        return v


class ChatRecord(BaseModel):
    messages: list[ChatMessage]
    meta: dict[str, Any] = {}

    @field_validator("messages")
    @classmethod
    def valid_turn_structure(cls, v: list[ChatMessage]) -> list[ChatMessage]:
        if len(v) < 3:
            raise ValueError(f"Need >= 3 turns (system/user/assistant), got {len(v)}")
        expected = ("system", "user", "assistant")
        for i, role in enumerate(expected):
            if v[i].role != role:
                raise ValueError(f"Turn {i} must be '{role}', got '{v[i].role}'")
        return v


def validate_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate a list of raw dicts. Returns (valid, errors)."""
    valid: list[dict[str, Any]] = []
    errors: list[str] = []
    for idx, rec in enumerate(records):
        try:
            ChatRecord(**rec)
            valid.append(rec)
        except Exception as exc:
            errors.append(f"record {idx}: {exc}")
    return valid, errors
