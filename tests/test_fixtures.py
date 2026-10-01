import json
from web_agent_robustness_benchmark.cli import main, read_records
from web_agent_robustness_benchmark.core import evaluate
from web_agent_robustness_benchmark.fixtures import expectations


def test_fixtures_labelled_synthetic(tmp_path):
    assert main(["fixtures", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "trials.jsonl").read_text().startswith("# synthetic: true")
    assert all(r["synthetic"] is True for r in read_records(tmp_path))
    assert json.loads((tmp_path / "expectations.json").read_text())["synthetic"] is True


def test_fixture_ground_truth_matches_hand_computed(tmp_path):
    main(["fixtures", "--out", str(tmp_path)])
    actual = evaluate(read_records(tmp_path))
    expected = expectations()
    for key in ("totals", "by_mutation", "regression_ids"):
        assert actual[key] == expected[key]
    assert sum(g["records"] for g in actual["by_mutation"].values()) == 200


def test_fixture_generation_deterministic(tmp_path):
    main(["fixtures", "--out", str(tmp_path)])
    first = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    main(["fixtures", "--out", str(tmp_path)])
    assert first == {p.name: p.read_bytes() for p in tmp_path.iterdir()}
