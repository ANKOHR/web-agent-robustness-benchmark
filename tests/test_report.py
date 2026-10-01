import json
import pytest
from web_agent_robustness_benchmark.core import evaluate
from web_agent_robustness_benchmark.fixtures import fixture_records, expectations
from web_agent_robustness_benchmark.report import render


def test_report_matches_ground_truth_exact():
    result = json.loads(render(evaluate(fixture_records()), "json"))
    for key in ("totals", "by_mutation", "regression_ids"):
        assert result[key] == expectations()[key]


def test_report_zero_false_positives():
    assert json.loads(render(evaluate(fixture_records()), "json"))["totals"]["false_positives"] == 0


@pytest.mark.parametrize("format", ["md", "json"])
def test_report_carries_provenance_banner(format):
    text = render(evaluate(fixture_records()), format)
    assert "Data provenance: 200 synthetic fixture records; 0 user-declared real records" in text


@pytest.mark.parametrize("format", ["md", "json"])
def test_hypothetical_figures_labelled(format):
    result = evaluate(fixture_records())
    assert result["savings"]["value"] is None
    text = render(result, format)
    assert "hypothetical" in text and "unmeasured" in text


@pytest.mark.parametrize("format", ["md", "json"])
def test_no_em_dashes_in_outputs(format):
    assert "\u2014" not in render(evaluate(fixture_records()), format)


def test_determinism_byte_identical():
    records = fixture_records()
    assert render(evaluate(records), "json").encode() == render(evaluate(list(reversed(records))), "json").encode()
