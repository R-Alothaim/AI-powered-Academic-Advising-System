"""Shared test fixtures."""

from __future__ import annotations

import pytest


def _rec(
    user: str = "What is the program duration?",
    assistant: str = "The program spans 4 years.",
    system: str = "Answer using only the study plan.",
    meta: dict | None = None,
) -> dict:
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ],
        "meta": meta or {"canonical_id": "test", "topic": "test"},
    }


@pytest.fixture()
def sample_record():
    return _rec()


@pytest.fixture()
def grammar_records():
    return [
        _rec(user="what is how long the program lasts?"),
        _rec(user="what are how many courses are in semester 1?"),
        _rec(user="what is duration of study?"),
        _rec(user="what are the program duration and credits?"),
    ]


@pytest.fixture()
def prereq_dash_records():
    return [
        _rec(user="What is the prerequisite for COMM001?",
             assistant="The prerequisite for COMM001 (Communication Skills) is -."),
        _rec(user="What is the prerequisite for ENG001?",
             assistant="The prerequisite for ENG001 (English language Skills) is -."),
    ]


@pytest.fixture()
def bad_credit_records():
    return [
        _rec(user="How many credit hours is ENG001?",
             assistant="English language Skills (ENG001) carries 8 credit hours."),
        _rec(user="How many credit hours is ENG002?",
             assistant="English language Skills 2 (ENG002) carries 8 credit hours."),
    ]
