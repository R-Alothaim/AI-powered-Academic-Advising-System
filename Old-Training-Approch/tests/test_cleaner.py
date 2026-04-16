"""Tests for the data cleaning pipeline."""

from advisor.data.cleaner import (
    clean_dataset,
    deduplicate,
    fix_credit_hours,
    fix_grammar,
    normalize_prerequisite,
)


class TestFixGrammar:
    def test_what_is_how_long(self):
        assert "how long does" in fix_grammar("what is how long the program lasts?")

    def test_what_are_how_many(self):
        result = fix_grammar("what are how many courses in semester 1?")
        assert result.startswith("how many")

    def test_what_is_duration_of(self):
        assert "the duration of" in fix_grammar("what is duration of study?")

    def test_clean_text_unchanged(self):
        text = "What is the program duration and total credits?"
        assert fix_grammar(text) == text


class TestNormalizePrerequisite:
    def test_dash_end(self):
        result = normalize_prerequisite("The prerequisite for COMM001 is -.")
        assert "no prerequisite" in result
        assert "-." not in result

    def test_normal_unchanged(self):
        text = "The prerequisite for CS240 is CS230."
        assert normalize_prerequisite(text) == text


class TestFixCreditHours:
    def test_eng001_corrected(self):
        text = "English language Skills (ENG001) carries 8 credit hours."
        result = fix_credit_hours(text)
        assert "carries 3 credit hours" in result

    def test_eng002_corrected(self):
        text = "English language Skills 2 (ENG002) carries 8 credit hours."
        result = fix_credit_hours(text)
        assert "carries 3 credit hours" in result

    def test_normal_unchanged(self):
        text = "Statistics (STAT101) carries 3 credit hours."
        assert fix_credit_hours(text) == text


class TestDeduplicate:
    def test_removes_exact_dupes(self):
        rec = {"messages": [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "same"},
            {"role": "assistant", "content": "same"},
        ]}
        assert len(deduplicate([rec, rec, rec])) == 1

    def test_keeps_different(self):
        def make(q):
            return {"messages": [
                {"role": "system", "content": "sys"},
                {"role": "user", "content": q},
                {"role": "assistant", "content": "ans"},
            ]}
        assert len(deduplicate([make("a"), make("b")])) == 2


class TestCleanDataset:
    def test_grammar_fixed(self, grammar_records):
        cleaned = clean_dataset(grammar_records)
        for rec in cleaned:
            u = rec["messages"][1]["content"]
            assert "what is how" not in u.lower()
            assert "what are how" not in u.lower()

    def test_prerequisites_normalized(self, prereq_dash_records):
        cleaned = clean_dataset(prereq_dash_records)
        for rec in cleaned:
            a = rec["messages"][2]["content"]
            assert "is -." not in a
            assert "no prerequisite" in a

    def test_credit_hours_fixed(self, bad_credit_records):
        cleaned = clean_dataset(bad_credit_records)
        for rec in cleaned:
            a = rec["messages"][2]["content"]
            assert "carries 3 credit hours" in a
            assert "carries 8 credit hours" not in a
