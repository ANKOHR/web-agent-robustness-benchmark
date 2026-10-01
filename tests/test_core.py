import copy
import pytest
from web_agent_robustness_benchmark.core import SchemaError, evaluate
from web_agent_robustness_benchmark.fixtures import fixture_records


def test_five_handwritten_outcomes():
    from pathlib import Path
    from web_agent_robustness_benchmark.cli import read_records
    result = evaluate(read_records(Path(__file__).parents[1] / "examples" / "five"))
    assert result["totals"] == dict(records=5, baseline_successes=3, changed_successes=3,
        regressions=1, improvements=1, stable_successes=2, stable_failures=1,
        labelled=5, unlabelled=0, true_positives=1, false_positives=0,
        true_negatives=4, false_negatives=0)


@pytest.mark.parametrize("field,value", [
    ("baseline_success", -1), ("changed_success", "false"), ("synthetic", 1),
    ("observed_on", "2027-01-01"), ("as_of", "2030-01-01"),
    ("observed_on", "2026-02-30"), ("agent", "x" * 10001),
    ("id", ""), ("mutation", "invented"), ("amount", -100),
    ("notes", "bad\nvalue"), ("notes", "bad\u2014value")])
def test_rejects_adversarial_values(field, value):
    record = fixture_records(1)[0]
    record[field] = value
    with pytest.raises(SchemaError, match="field"):
        evaluate([record])


def test_duplicate_ids_rejected():
    r = fixture_records(1)[0]
    with pytest.raises(SchemaError, match="duplicates"):
        evaluate([r, copy.deepcopy(r)])


def test_handles_unicode_and_long_inputs():
    r = fixture_records(1)[0]
    r["task"] = "購入 é 🚀 " + "x" * 9000
    r["source"] = r"C:\Users\Henry\recorded trials\測試.json"
    assert evaluate([r])["totals"]["regressions"] == 1


def test_corrupted_outcome_changes_computed_figures():
    records = fixture_records()
    before = evaluate(records)
    records[0]["changed_success"] = True
    after = evaluate(records)
    assert after["totals"]["regressions"] == before["totals"]["regressions"] - 1
    assert after["totals"]["false_negatives"] == 1
    assert "trial-001" not in after["regression_ids"]


def test_corrupted_ground_truth_changes_scoring():
    records = fixture_records()
    records[0]["expected_regression"] = False
    assert evaluate(records)["totals"]["false_positives"] == 1


def test_unlabelled_is_not_assumed_correct():
    records = fixture_records(1)
    del records[0]["expected_regression"]
    totals = evaluate(records)["totals"]
    assert totals["unlabelled"] == 1
    assert totals["true_positives"] == 0


def test_real_provenance_is_user_declared():
    records = fixture_records(1)
    records[0]["synthetic"] = False
    p = evaluate(records)["provenance"]
    assert p["real_records"] == 1 and p["synthetic_records"] == 0
    assert "not verified" in p["real_data_claim"]
