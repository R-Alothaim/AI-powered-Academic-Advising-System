"""Tests for evaluation metrics."""

from advisor.evaluation.metrics import (
    compute_metrics,
    exact_match,
    refusal_detected,
    token_f1,
)


class TestExactMatch:
    def test_identical(self):
        assert exact_match("CS230", "CS230")

    def test_case_insensitive(self):
        assert exact_match("cs230", "CS230")

    def test_whitespace(self):
        assert exact_match("  3 credit  hours ", "3 credit hours")

    def test_different(self):
        assert not exact_match("CS230", "CS240")


class TestRefusal:
    def test_detected(self):
        assert refusal_detected("I don't know based on the provided study plan.")

    def test_not_detected(self):
        assert not refusal_detected("The prerequisite is CS230.")


class TestF1:
    def test_perfect(self):
        assert token_f1("hello world", "hello world") == 1.0

    def test_partial(self):
        assert 0.5 < token_f1("the cat sat", "the dog sat") < 1.0

    def test_zero(self):
        assert token_f1("abc", "xyz") == 0.0

    def test_empty(self):
        assert token_f1("", "") == 1.0


class TestComputeMetrics:
    def test_all_correct(self):
        preds = [
            {"predicted": "CS230", "expected": "CS230",
             "eval_label": "control", "category": "prereq_lookup"},
            {"predicted": "I don't know.", "expected": "I don't know.",
             "eval_label": "refusal", "category": "invented_course"},
        ]
        r = compute_metrics(preds)
        assert r["control_accuracy"] == 1.0
        assert r["refusal_accuracy"] == 1.0

    def test_empty(self):
        assert "error" in compute_metrics([])
