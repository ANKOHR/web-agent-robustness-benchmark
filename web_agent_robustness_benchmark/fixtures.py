"""Synthetic planted fixtures; no randomness, seed is not applicable."""
MUTATIONS = ("selector", "layout", "wording", "navigation", "control")


def fixture_records(count=200):
    """Each block of four contains regression, stable success, improvement, failure."""
    records = []
    for i in range(count):
        baseline, changed = ((True, False), (True, True), (False, True), (False, False))[i % 4]
        records.append({"id": f"trial-{i + 1:03d}", "agent": "synthetic-agent",
            "task": f"Synthetic checkout task {i + 1}", "mutation": MUTATIONS[i % 5],
            "baseline_success": baseline, "changed_success": changed,
            "expected_regression": i % 4 == 0, "synthetic": True,
            "observed_on": "2026-09-30", "as_of": "2026-09-30",
            "source": "Synthetic planted outcomes, not an executed browser trial"})
    return records


def expectations():
    """Hand arithmetic: 200 / 4 = 50 per outcome; 200 / 5 = 40 per mutation.
    The coprime cycles put 10 regressions in each mutation. Never calls core.
    """
    return {"synthetic": True, "description": "Synthetic hand-computed ground truth",
        "totals": {"records": 200, "baseline_successes": 100, "changed_successes": 100,
        "regressions": 50, "improvements": 50, "stable_successes": 50,
        "stable_failures": 50, "labelled": 200, "unlabelled": 0,
        "true_positives": 50, "false_positives": 0, "true_negatives": 150, "false_negatives": 0},
        "by_mutation": {name: {"records": 40, "regressions": 10} for name in MUTATIONS},
        "regression_ids": [f"trial-{i:03d}" for i in range(1, 201, 4)]}
