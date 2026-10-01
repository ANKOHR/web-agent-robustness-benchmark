# Web Agent Robustness Benchmark

`warb` evaluates recorded agent outcomes before and after an interface change. It computes regressions, improvements, stable outcomes, and agreement with optional hand-checked regression labels. CPU only, standard-library runtime, local files only. No browser automation, model calls, network requests, or GPU dependencies.

Hypothesis: deterministic evaluation of explicit paired outcomes can provide trustworthy, reproducible counts for interface robustness reviews. The synthetic acceptance test establishes arithmetic correctness and CLI reliability. It does not establish the robustness of any real agent.

## Quickstart

Python 3.10 or later and setuptools 68 or later are required. From the repository, with build dependencies already installed:

```powershell
$env:PIP_NO_INDEX = "1"
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
python -m pip install --no-deps --no-build-isolation -e .
warb fixtures --out demo
warb run --input demo
warb report --format md
python -m pytest -q
```

These three `warb` commands are the end-to-end demo. In shells supporting `&&`, they can be chained as `warb fixtures --out demo && warb run --input demo && warb report --format md`. If your Python Scripts directory is absent from PATH, replace `warb` with `python -m web_agent_robustness_benchmark.cli` or add your Python Scripts directory to PATH. pytest is a development prerequisite, not a runtime dependency. No package download is needed by the CLI.

The smallest hand-written synthetic example is also shipped:

```powershell
warb run --input examples/five
warb report --format json
```

It has five trials: one regression, one improvement, two stable successes, one stable failure. It is illustrative input, not measured browser behavior. The 200-record generator extends this workflow.

## Input format reference

An input directory contains UTF-8 `.jsonl` files (one trial per line) or `.json` files (an array of trial objects). JSONL permits blank lines and full-line `#` comments. JSON does not permit comments. Files and records are sorted for deterministic results. Other file extensions are rejected with a named schema error. CSV and YAML are not supported. `expectations.json` and `results.json` are reserved output names and are not treated as trials. Keep reports and auxiliary documentation outside the input directory.

Each record is a single paired trial on the same agent and task, under a baseline and one declared interface mutation. Outcomes must be recorded by the user, using the same success criterion in both versions. Repeat runs require distinct IDs. Failed baseline trials remain in the denominator and cannot be regressions.

```json
{
  "id": "illustrative-001",
  "agent": "synthetic-example-agent",
  "task": "Complete checkout after a button rename",
  "mutation": "wording",
  "baseline_success": true,
  "changed_success": false,
  "expected_regression": true,
  "synthetic": true,
  "observed_on": "2026-09-30",
  "as_of": "2026-09-30",
  "source": "Illustrative synthetic example, not executed"
}
```

| Field | Rule |
| --- | --- |
| id | Required unique string across all files |
| agent, task | Required descriptive strings |
| mutation | Required: selector, layout, wording, navigation, or control |
| baseline_success, changed_success | Required JSON booleans, not numbers or strings |
| synthetic | Required boolean; true for all invented or fixture outcomes |
| observed_on, as_of | Required ISO dates; observed_on <= as_of <= 2026-09-30 |
| expected_regression | Optional boolean from independent hand checking |
| source, notes | Optional descriptive strings; source should identify the user's trial evidence |

Strings must be nonempty, at most 10,000 characters, and have no control characters except tabs. Unicode and Windows paths are supported; JSON backslashes must be escaped. U+2014 is rejected to keep outputs within the brief's character constraint. Unknown fields, including amounts, are rejected rather than silently ignored. Negative amounts therefore fail schema validation. Duplicate IDs are rejected across files. Dates use a fixed evaluation cutoff of 2026-09-30, the brief's reference date, rather than the wall clock. This prevents future observations and makes validation reproducible. For later real trials, deliberately revise the cutoff and tests in a new version.

Henry's real-data path: manually record actual baseline and changed-interface trial outcomes, use `synthetic: false`, identify his evidence in `source`, and optionally supply independently checked labels. Real observations are not shipped. The tool calls these records user-declared real data; it cannot verify ownership or authenticity. Do not relabel synthetic records as real.

## Computation and acceptance criteria

A regression is `baseline_success and not changed_success`; improvement is the opposite. Stable successes pass both versions, stable failures fail both. These four outcome counts sum exactly to the record count. Baseline successes equal regressions plus stable successes; changed successes equal improvements plus stable successes.

Label agreement uses a confusion matrix: true positives are observed regressions labelled true; false positives are observed regressions labelled false; false negatives are non-regressions labelled true; true negatives are non-regressions labelled false. Unlabelled records receive no presumed ground truth and are counted separately. This measures consistency with supplied labels, not causal attribution or independently established agent accuracy.

The generator uses no randomness. Each block of four outcomes contains one regression, stable success, improvement, and stable failure. Five mutation categories cycle independently. The hand arithmetic is 200 / 4 = 50 per outcome and 200 / 5 = 40 per mutation, with 10 regressions per mutation. Expected totals are 100 baseline successes, 100 changed successes, 50 true positives, 150 true negatives, and zero false positives or false negatives. Fifty regression IDs are explicitly recorded in expectations. The engine never reads that expectations file.

Acceptance: all planted regression IDs and every count must exactly match the independent expectations, no false positives, and the full fixture demo must finish in under five seconds. See `EVIDENCE.md` for the measured local run, environment, and limitations. Tests deliberately corrupt outcomes and labels to prove results are computed. JSON reports retain validated trial records and file hashes so counts can be traced to inputs.

## Subcommands

| Command | Purpose and example |
| --- | --- |
| fixtures | Generate labelled synthetic input: `warb fixtures --out demo` |
| run | Validate and evaluate recorded outcomes: `warb run --input demo --results .warb/results.json` |
| report | Render last saved results: `warb report --format md --out report.md` or `warb report --format json` |
| validate | Check schema and unique IDs without writing: `warb validate --input examples/five` |
| compare | Compute a provenance-labelled comparison by mutation: `warb compare --input demo` |

Every command has `--help` and an example. `run` evaluates supplied outcomes; it does not launch an agent or execute websites. `report` reads the results selected by `--results`, default `.warb/results.json`. Changing an input requires rerunning `run`. `compare` reports recorded regressions grouped by change type; it does not rank agents or claim statistical significance. Results and reports are atomically replaced. Exit status 0 indicates success and 2 indicates invalid input or an I/O failure.

## Architecture

```text
Local JSON / JSONL recorded trials
             |
       cli.read_records -- parse, file/line errors, hash provenance
             |
       core.validate --> core.evaluate (pure, no I/O)
             |                    |
        validate/compare      atomic results JSON
                                  |
                           report.render
                                  |
                        stdout / atomic MD or JSON

fixtures.fixture_records --> synthetic trials
fixtures.expectations    --> independent hand arithmetic
```

## Honesty boundary and fixture labelling

All performance counts describe supplied outcomes. Synthetic fixtures are labelled in each record (`synthetic: true`), the JSONL header comment, and expectations metadata. JSON cannot carry a legal header comment; its top-level `synthetic: true` and description provide the label. Every report carries synthetic and user-declared real counts and an authenticity caveat. Mixed inputs remain identifiable record by record in JSON output.

Time saved and money saved are unmeasured. The report stores a null savings value, marks it unmeasured, and states proposed savings would be hypothetical. There is no savings estimator. The only measured runtime is local acceptance evidence, never converted into savings. No illustrative percentage or invented revenue is presented as measured. The five-record example and all generated agent outcomes are synthetic. Even zero errors on fixtures is evidence of tested arithmetic, not evidence of real-world accuracy.

## Failure modes and boundaries

| Failure | Behavior |
| --- | --- |
| Malformed JSON / JSONL | ParseError with file and actual parser line |
| Invalid UTF-8 | ParseError naming file and line 1 as the decoding entry point |
| Missing directory or results | MissingInput and a usage hint, nonzero exit |
| Schema drift / negative amounts / duplicate IDs | SchemaError with file, line, and offending field |
| Malformed results file | ResultError with regeneration hint |
| Bad report output path | WriteError; no partial target or temporary file remains |

For JSON arrays, schema errors use line 1 as the document entry point; JSON syntax errors use the exact parser line. Outputs use UTF-8 and LF. JSON reports are canonical with sorted keys; records are sorted by ID. Markdown metrics and mutation groups are sorted. The same inputs at the same paths produce byte-identical results; timestamps and runtime are excluded. Console status text includes the chosen output path. Source paths are descriptive, never opened by the core. Names and inputs are local trusted files, not sandboxed multi-tenant ingestion. Input is read in memory, so this is a small local benchmark, not a large-scale streaming service. Baseline quality, annotation mistakes, mixed task difficulty, nondeterministic agents, and unmatched trials can invalidate real interpretations. The tool does not hide or correct those measurement problems.

Report writes are atomic per file, not transactions over the fixture pair. A failed fixture-generation command may have written one complete fixture file; rerun to regenerate both. No partial report files remain on a failed write. Hashes identify bytes used by a run; do not edit files concurrently during evaluation.

## Evidence-based improvement hook and verdict

After two weeks of actual use, measure the key metric: classification error rate against an independently hand-checked sample, `(false positives + false negatives) / labelled records`. Also record whether the tool was actually used. Zero labelled records means accuracy is unmeasured, not zero error. Use `REVIEW.md` to record the window dates, real sample size, confusion counts, error rate, actual usage, top failure cause, corrective action, and reasoned verdict.

If error exceeds 10 percent, fix the top measured failure cause and rerun the hand check, or kill the project with the reason recorded. If unused, kill it. No two-week use evidence exists at build time. Final verdict is pending, not fabricated. A provisional build-stage verdict is **maintain as portfolio evidence** because the synthetic acceptance criteria pass; this is not a post-window finding. After the window: expand for daily use or revenue; integrate for heavy overlap with a sibling; commercialise if a buyer would pay as-is; maintain for useful portfolio evidence; kill if unused or unable to meet acceptance criteria.

See `LESSONS.md` for the domain lesson and operating rule, `EVIDENCE.md` for local measurements, and `BUILD-DONE.txt` for build completion. Publishing is a separate authorised verification step and is not performed by this build.
