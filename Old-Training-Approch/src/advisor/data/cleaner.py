"""Data cleaning pipeline.

Fixes known issues in the legacy dataset that caused model hallucinations:

1. GRAMMAR — Automated paraphrasing produced broken English in user prompts
   (e.g. "what is how long the program lasts").  300 affected records.

2. PREREQUISITE NOTATION — Bare-dash answers ("is -.") instead of
   human-readable "has no prerequisite".  6 affected records in eval.

3. CREDIT HOURS — Two courses (ENG001, ENG002) incorrectly listed as
   8 credit hours.  Corrected to 3 (verified against source document).
   120 affected records across both splits.

4. ANSWER INCONSISTENCY — Minor punctuation variance in identical
   canonical answers (missing colon).  Normalized to a single form.

5. DUPLICATES — Exact user+assistant duplicates removed.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ── 1. Grammar fixes ──────────────────────────────────────────────────────────
_GRAMMAR_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bwhat is how long\b", re.I), "how long does"),
    (re.compile(r"\bwhat are how long\b", re.I), "how long does"),
    (re.compile(r"\bwhat is how many\b", re.I), "how many"),
    (re.compile(r"\bwhat are how many\b", re.I), "how many"),
    (re.compile(r"\bwhat is duration of\b", re.I), "what is the duration of"),
    (re.compile(r"\bwhat are duration of\b", re.I), "what is the duration of"),
    (re.compile(r"\bwhat are the program duration\b", re.I), "what is the program duration"),
]

# ── 2. Prerequisite normalization ──────────────────────────────────────────────
_PREREQ_DASH_END = re.compile(r"\bis [-–—]\.\s*$")
_PREREQ_DASH_MID = re.compile(r"\bis [-–—](\s|$)")

# ── 3. Credit-hour corrections (verified against source document) ─────────────
_CREDIT_CORRECTIONS: dict[str, tuple[int, int]] = {
    "ENG001": (8, 3),   # was 8, should be 3
    "ENG002": (8, 3),   # was 8, should be 3
}

# ── 4. Answer normalization ───────────────────────────────────────────────────
_ANSWER_NORMALIZATIONS: list[tuple[str, str]] = [
    (
        "grouped as Knowledge & Understanding",
        "grouped as: Knowledge & Understanding",
    ),
]


def fix_grammar(text: str) -> str:
    for pattern, replacement in _GRAMMAR_RULES:
        text = pattern.sub(replacement, text)
    return text


def normalize_prerequisite(text: str) -> str:
    text = _PREREQ_DASH_END.sub("has no prerequisite.", text)
    text = _PREREQ_DASH_MID.sub("has no prerequisite ", text)
    return text


def fix_credit_hours(text: str) -> str:
    for course_code, (wrong, correct) in _CREDIT_CORRECTIONS.items():
        pattern = f"carries {wrong} credit hours"
        replacement = f"carries {correct} credit hours"
        if course_code in text and pattern in text:
            text = text.replace(pattern, replacement)
    return text


def normalize_answers(text: str) -> str:
    for old, new in _ANSWER_NORMALIZATIONS:
        text = text.replace(old, new)
    return text


def deduplicate(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for rec in records:
        msgs = rec["messages"]
        key = (msgs[1]["content"], msgs[2]["content"])
        if key not in seen:
            seen.add(key)
            unique.append(rec)
    removed = len(records) - len(unique)
    if removed:
        logger.info("Removed %d duplicates", removed)
    return unique


def clean_dataset(
    records: list[dict[str, Any]],
    *,
    apply_grammar: bool = True,
    apply_prereq: bool = True,
    apply_credits: bool = True,
    apply_answer_norm: bool = True,
    apply_dedup: bool = True,
) -> list[dict[str, Any]]:
    """Run the full cleaning pipeline. Returns a new list of cleaned records."""
    stats = {"grammar": 0, "prereq": 0, "credits": 0, "answer_norm": 0}

    cleaned: list[dict[str, Any]] = []
    for rec in records:
        msgs = rec["messages"]
        user_text = msgs[1]["content"]
        asst_text = msgs[2]["content"]

        if apply_grammar:
            new = fix_grammar(user_text)
            if new != user_text:
                stats["grammar"] += 1
            user_text = new

        if apply_prereq:
            new = normalize_prerequisite(asst_text)
            if new != asst_text:
                stats["prereq"] += 1
            asst_text = new

        if apply_credits:
            new = fix_credit_hours(asst_text)
            if new != asst_text:
                stats["credits"] += 1
            asst_text = new

        if apply_answer_norm:
            new = normalize_answers(asst_text)
            if new != asst_text:
                stats["answer_norm"] += 1
            asst_text = new

        msgs[1]["content"] = user_text
        msgs[2]["content"] = asst_text
        cleaned.append(rec)

    logger.info(
        "Cleaning stats — grammar: %d, prerequisites: %d, credits: %d, answer_norm: %d",
        stats["grammar"], stats["prereq"], stats["credits"], stats["answer_norm"],
    )

    if apply_dedup:
        cleaned = deduplicate(cleaned)

    return cleaned
