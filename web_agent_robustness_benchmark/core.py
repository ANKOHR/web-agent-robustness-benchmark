"""Pure validation and metrics for recorded paired interface trials.

No estimated time or money savings are computed. All counts derive from inputs.
"""
from collections import Counter
from datetime import date


class SchemaError(ValueError):
    """An input field violates the documented schema."""


REQUIRED = {"id", "agent", "task", "mutation", "baseline_success", "changed_success",
            "synthetic", "observed_on", "as_of"}
OPTIONAL = {"expected_regression", "source", "notes"}
MUTATIONS = {"selector", "layout", "wording", "navigation", "control"}


def validate(records):
    """Return copied records; reject invalid fields and duplicate IDs."""
    checked, ids = [], set()
    for index, record in enumerate(records, 1):
        prefix = f"record {index}"
        if not isinstance(record, dict):
            raise SchemaError(f"{prefix}: field record must be an object")
        missing, extra = REQUIRED - record.keys(), record.keys() - REQUIRED - OPTIONAL
        if missing or extra:
            raise SchemaError(f"{prefix}: fields missing={sorted(missing)}, unknown={sorted(extra)}")
        for field in ("id", "agent", "task", "mutation", "source", "notes"):
            if field not in record:
                continue
            value = record[field]
            if not isinstance(value, str) or not value.strip() or len(value) > 10000:
                raise SchemaError(f"{prefix}: field {field} must be a nonempty string of at most 10000 characters")
            if any(ord(c) < 32 and c not in "\t" for c in value):
                raise SchemaError(f"{prefix}: field {field} contains a control character")
            if "\u2014" in value:
                raise SchemaError(f"{prefix}: field {field} contains a forbidden U+2014 character; use a hyphen")
        for field in ("baseline_success", "changed_success", "synthetic", "expected_regression"):
            if field in record and type(record[field]) is not bool:
                raise SchemaError(f"{prefix}: field {field} must be boolean")
        if record["mutation"] not in MUTATIONS:
            raise SchemaError(f"{prefix}: field mutation must be one of {sorted(MUTATIONS)}")
        for field in ("observed_on", "as_of"):
            value = record[field]
            try:
                if not isinstance(value, str) or len(value) != 10:
                    raise ValueError()
                date.fromisoformat(value)
            except ValueError:
                raise SchemaError(f"{prefix}: field {field} must be an ISO date YYYY-MM-DD") from None
        if record["as_of"] > "2026-09-30" or record["observed_on"] > record["as_of"]:
            raise SchemaError(f"{prefix}: field observed_on/as_of exceeds the evaluation cutoff 2026-09-30")
        if record["id"] in ids:
            raise SchemaError(f"{prefix}: field id duplicates {record['id']!r}")
        ids.add(record["id"])
        checked.append(dict(record))
    return sorted(checked, key=lambda r: r["id"])


def evaluate(records):
    """Count observed changes and evaluate optional hand labels exactly."""
    records = validate(records)
    totals = Counter({k: 0 for k in ("records", "baseline_successes", "changed_successes",
        "regressions", "improvements", "stable_successes", "stable_failures", "labelled",
        "unlabelled", "true_positives", "false_positives", "true_negatives", "false_negatives")})
    groups = {}
    regression_ids = []
    for r in records:
        baseline, changed = r["baseline_success"], r["changed_success"]
        regression = baseline and not changed
        totals["records"] += 1
        totals["baseline_successes"] += baseline
        totals["changed_successes"] += changed
        outcome = "regressions" if regression else "improvements" if changed and not baseline else "stable_successes" if changed else "stable_failures"
        totals[outcome] += 1
        if regression:
            regression_ids.append(r["id"])
        if "expected_regression" in r:
            totals["labelled"] += 1
            truth = r["expected_regression"]
            category = "true_positives" if regression and truth else "false_positives" if regression else "false_negatives" if truth else "true_negatives"
            totals[category] += 1
        else:
            totals["unlabelled"] += 1
        group = groups.setdefault(r["mutation"], {"records": 0, "regressions": 0})
        group["records"] += 1
        group["regressions"] += regression
    synthetic = sum(r["synthetic"] for r in records)
    return {"schema_version": 1, "provenance": {"synthetic_records": synthetic,
        "real_records": len(records) - synthetic,
        "real_data_claim": "Non-synthetic records are user-declared real observations; ownership and authenticity are not verified."},
        "totals": dict(totals), "by_mutation": dict(sorted(groups.items())),
        "regression_ids": regression_ids, "recorded_trials": records,
        "limitations": "Recorded outcomes only. No live agent execution, causal inference, or estimates of time or money saved.",
        "savings": {"status": "unmeasured", "value": None,
                    "note": "Any proposed savings are hypothetical; no measured baseline was supplied."}}
