"""Tests for record validation."""

from advisor.data.schema import validate_records


def test_valid_record(sample_record):
    valid, errors = validate_records([sample_record])
    assert len(valid) == 1
    assert not errors


def test_missing_messages():
    valid, errors = validate_records([{"meta": {}}])
    assert not valid
    assert len(errors) == 1


def test_wrong_role_order():
    bad = {"messages": [
        {"role": "user", "content": "hi"},
        {"role": "system", "content": "sys"},
        {"role": "assistant", "content": "ok"},
    ]}
    valid, _ = validate_records([bad])
    assert not valid


def test_empty_content():
    bad = {"messages": [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "   "},
        {"role": "assistant", "content": "ok"},
    ]}
    valid, _ = validate_records([bad])
    assert not valid
