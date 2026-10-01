# Web Agent Robustness Benchmark

Data provenance: 200 synthetic fixture records; 0 user-declared real records. Non-synthetic records are user-declared real observations; ownership and authenticity are not verified.

Counts computed from supplied recorded outcomes. Synthetic counts do not measure real agent performance.

| Metric | Count |
| --- | ---: |
| baseline_successes | 100 |
| changed_successes | 100 |
| false_negatives | 0 |
| false_positives | 0 |
| improvements | 50 |
| labelled | 200 |
| records | 200 |
| regressions | 50 |
| stable_failures | 50 |
| stable_successes | 50 |
| true_negatives | 150 |
| true_positives | 50 |
| unlabelled | 0 |

## Interface changes

| Mutation | Records | Regressions |
| --- | ---: | ---: |
| control | 40 | 10 |
| layout | 40 | 10 |
| navigation | 40 | 10 |
| selector | 40 | 10 |
| wording | 40 | 10 |

Input files (SHA-256):
- trials.jsonl: 94cb13957b9c1dc53264fa3a459951f5874e266a358b4b161d7b0eea5a68b16d

Regression IDs: trial-001, trial-005, trial-009, trial-013, trial-017, trial-021, trial-025, trial-029, trial-033, trial-037, trial-041, trial-045, trial-049, trial-053, trial-057, trial-061, trial-065, trial-069, trial-073, trial-077, trial-081, trial-085, trial-089, trial-093, trial-097, trial-101, trial-105, trial-109, trial-113, trial-117, trial-121, trial-125, trial-129, trial-133, trial-137, trial-141, trial-145, trial-149, trial-153, trial-157, trial-161, trial-165, trial-169, trial-173, trial-177, trial-181, trial-185, trial-189, trial-193, trial-197

Recorded outcomes only. No live agent execution, causal inference, or estimates of time or money saved.

Savings: unmeasured. Any proposed savings are hypothetical; no measured baseline was supplied.
