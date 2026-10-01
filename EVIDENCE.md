# Local acceptance evidence

Measured on 2026-10-01, Windows local CPU execution, Python 3.12.10.
The installed warb executable was invoked in three fresh processes:

```text
warb fixtures --out demo
warb run --input demo
warb report --format md
```

Measured elapsed time for the complete three-process demo: 0.817723 seconds, below the five-second criterion. This is one local measurement, not a guarantee on other machines. No GPU, model, browser, or network workload was used by the benchmark.

The 200 inputs are synthetic planted outcomes, not real agent runs. Actual result totals, all mutation counts, and all 50 regression IDs were compared exactly against the independent hand-computed expectations. All matched: 200 records, 100 baseline successes, 100 changed successes, 50 regressions, 50 improvements, 50 stable successes, 50 stable failures, 50 true positives, 150 true negatives, 0 false positives, and 0 false negatives. Each of five mutation categories contains 40 records and 10 regressions.

The pytest suite passed 46 tests. It checks hand-written five-record outcomes, empty input, malformed JSON and invalid UTF-8, unsupported CSV/YAML, schema drift, future dates, numeric booleans, negative amounts, extreme strings, duplicates, Unicode, Windows paths, report write failure without partial files, deterministic bytes, all command help, corrupted outcomes, corrupted labels, provenance, and hypothetical/unmeasured savings labels.

The saved report is [evidence/fixture-report.md](evidence/fixture-report.md). It records SHA-256 of the exact trial input. Recreate it with the commands above. No real-use findings, time savings, money savings, or real agent accuracy are claimed. The final two-week verdict is pending in REVIEW.md.
