"""Tests for data loading and persistence."""

import json
from pathlib import Path

import pytest

from advisor.data.loader import load_local, save_local


def test_roundtrip(tmp_path, sample_record):
    path = tmp_path / "out.jsonl"
    save_local([sample_record, sample_record], path)
    reloaded = load_local(path)
    assert len(reloaded) == 2
    assert reloaded[0] == sample_record


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_local("/nonexistent/path.jsonl")


def test_bad_json(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text("not json\n")
    with pytest.raises(ValueError, match="bad JSON"):
        load_local(bad)
