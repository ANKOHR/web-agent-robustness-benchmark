"""Deterministic reports with explicit data provenance."""
import json


def banner(result):
    p = result["provenance"]
    return (f"Data provenance: {p['synthetic_records']} synthetic fixture records; "
            f"{p['real_records']} user-declared real records. " + p["real_data_claim"])


def render(result, format="md"):
    if format == "json":
        return json.dumps({"provenance_banner": banner(result), **result},
                          ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if format != "md":
        raise ValueError("format must be md or json")
    lines = ["# Web Agent Robustness Benchmark", "", banner(result), "",
             "Counts computed from supplied recorded outcomes. Synthetic counts do not measure real agent performance.", "",
             "| Metric | Count |", "| --- | ---: |"]
    lines += [f"| {key} | {value} |" for key, value in sorted(result["totals"].items())]
    lines += ["", "## Interface changes", "", "| Mutation | Records | Regressions |", "| --- | ---: | ---: |"]
    lines += [f"| {key} | {value['records']} | {value['regressions']} |" for key, value in result["by_mutation"].items()]
    if result.get("input_files"):
        lines += ["", "Input files (SHA-256):"]
        lines += [f"- {item['name']}: {item['sha256']}" for item in result["input_files"]]
    lines += ["", "Regression IDs: " + (", ".join(result["regression_ids"]) or "none"), "",
              result["limitations"], "", "Savings: unmeasured. " + result["savings"]["note"], ""]
    return "\n".join(lines)
