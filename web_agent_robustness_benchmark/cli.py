"""Local-file CLI. run evaluates recorded trials, never executes an agent."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import SchemaError, evaluate, validate
from .fixtures import expectations, fixture_records
from .report import render


class InputError(ValueError):
    pass


def read_records(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}: supply an existing directory with --input")
    records = []
    seen_ids = set()
    paths = sorted(directory.iterdir())
    for path in paths:
        if not path.is_file() or path.name in {"expectations.json", "results.json"}:
            continue
        if path.suffix.lower() not in {".json", ".jsonl"}:
            raise InputError(f"SchemaError: {path}: line 1: unsupported input format; use JSON or JSONL")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError as exc:
            raise InputError(f"ParseError: {path}: line 1: invalid UTF-8: {exc}") from None
        if path.suffix.lower() == ".jsonl":
            entries = []
            for line_number, line in enumerate(text.splitlines(), 1):
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                try:
                    entries.append((line_number, json.loads(line)))
                except json.JSONDecodeError as exc:
                    raise InputError(f"ParseError: {path}: line {line_number}: {exc.msg}") from None
        else:
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                raise InputError(f"ParseError: {path}: line {exc.lineno}: {exc.msg}") from None
            if not isinstance(payload, list):
                raise InputError(f"SchemaError: {path}: line 1: JSON input must be an array of trial objects")
            entries = [(1, entry) for entry in payload]
        for line_number, entry in entries:
            try:
                validate([entry])
                if entry["id"] in seen_ids:
                    raise SchemaError("field id duplicates " + repr(entry["id"]))
                seen_ids.add(entry["id"])
            except SchemaError as exc:
                raise InputError(f"SchemaError: {path}: line {line_number}: {exc}") from None
            records.append(entry)
    return records


def atomic_write(path, content):
    path = Path(path)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                dir=path.parent, prefix=".warb-write-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def parser():
    p = argparse.ArgumentParser(prog="warb", description="Evaluate recorded paired trials against changing interfaces. Local files only.")
    sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fixtures", help="Generate 200 labelled synthetic trials", epilog="Example: warb fixtures --out demo")
    f.add_argument("--out", required=True)
    r = sub.add_parser("run", help="Evaluate recorded outcomes and save deterministic results", epilog="Example: warb run --input demo")
    r.add_argument("--input", required=True)
    r.add_argument("--results", default=".warb/results.json")
    rep = sub.add_parser("report", help="Render a provenance-labelled report", epilog="Example: warb report --format md --out report.md")
    rep.add_argument("--format", choices=("md", "json"), default="md")
    rep.add_argument("--results", default=".warb/results.json")
    rep.add_argument("--out")
    for command, help_text, example in (("validate", "Validate trial schema, dates and unique IDs", "warb validate --input demo"),
                                        ("compare", "Compare observed regressions by interface mutation", "warb compare --input demo")):
        child = sub.add_parser(command, help=help_text, epilog="Example: " + example)
        child.add_argument("--input", required=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "fixtures":
            out = Path(args.out)
            out.mkdir(parents=True, exist_ok=True)
            header = "# synthetic: true; planted outcomes, not real browser runs\n"
            atomic_write(out / "trials.jsonl", header + "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in fixture_records()))
            atomic_write(out / "expectations.json", json.dumps(expectations(), sort_keys=True, indent=2) + "\n")
            print("Generated 200 synthetic fixture records and synthetic hand-computed expectations.")
        elif args.command in {"run", "validate", "compare"}:
            result = evaluate(read_records(args.input))
            result["input_files"] = [
                {"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                for path in sorted(Path(args.input).iterdir())
                if path.is_file() and path.suffix.lower() in {".json", ".jsonl"}
                and path.name not in {"expectations.json", "results.json"}]
            if args.command == "run":
                atomic_write(args.results, json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2) + "\n")
                print(f"Computed {result['totals']['records']} recorded trials; {result['totals']['regressions']} regressions. Synthetic: {result['provenance']['synthetic_records']}; user-declared real: {result['provenance']['real_records']}. Results: {args.results}")
            elif args.command == "compare":
                print(render(result, "md"), end="")
            else:
                print(f"Valid: {result['totals']['records']} recorded trials. Synthetic: {result['provenance']['synthetic_records']}; user-declared real: {result['provenance']['real_records']}.")
        else:
            path = Path(args.results)
            if not path.is_file():
                raise InputError(f"MissingInput: {path}: run warb run --input <dir> first")
            try:
                result = json.loads(path.read_text(encoding="utf-8"))
                if result.get("schema_version") != 1:
                    raise ValueError("unsupported results schema_version")
                content = render(result, args.format)
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                raise InputError(f"ResultError: {path}: {exc}; regenerate with warb run") from None
            if args.out:
                atomic_write(args.out, content)
            else:
                print(content, end="")
        return 0
    except (InputError, SchemaError, OSError) as exc:
        name = "WriteError" if isinstance(exc, OSError) else "InputError"
        print(f"{name}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
