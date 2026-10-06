#!/usr/bin/env python3
"""Replace the embedded data block of a dynamic HTML report.

A dynamic report (see references/dynamic-reports.md) keeps its dataset in

    <script id="report-data" type="application/json">{"meta": {...}, "rows": [...]}</script>

This script swaps that block for fresh data so the report updates without
regenerating the HTML. The file stays a single self-contained page that opens
from file://.

Usage:
    python inject_data.py report.html data.csv
    python inject_data.py report.html data.json --out report-2026-10.html
    python inject_data.py report.html data.csv --id cohort-data

Input:
    .csv   header row + records. Numeric-looking cells become numbers, empty
           cells become null. Values with leading zeros ("007") stay strings so
           IDs are not mangled.
    .json  either a list of records, or an object with a "rows" list (other
           keys besides "meta" are kept as-is).

The "meta" object is always rewritten with source file name, update time and
row count, so the report can show when its data was last refreshed.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

NUMBER_RE = re.compile(r"^-?(0|[1-9]\d*)(\.\d+)?([eE][-+]?\d+)?$")


def parse_cell(value: str):
    text = value.strip()
    if text == "":
        return None
    if not NUMBER_RE.match(text):
        return text
    if "." in text or "e" in text.lower():
        return float(text)
    return int(text)


def load_csv(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = [{k: parse_cell(v or "") for k, v in record.items()} for record in csv.DictReader(f)]
    return {"rows": rows}


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {"rows": data}
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        return {k: v for k, v in data.items() if k != "meta"}
    raise ValueError(f"{path}: JSON must be a list of records or an object with a 'rows' list")


def build_payload(data_path: Path) -> dict:
    loaders = {".csv": load_csv, ".json": load_json}
    loader = loaders.get(data_path.suffix.lower())
    if loader is None:
        raise ValueError(f"{data_path}: unsupported extension (use .csv or .json)")
    body = loader(data_path)
    meta = {
        "source": data_path.name,
        "updated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "n_rows": len(body["rows"]),
    }
    return {"meta": meta, **body}


def to_script_json(payload: dict) -> str:
    # "</script>" or "<!--" inside data would break the <script> element; "<" is the same "<" in JSON.
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def inject(html: str, block_id: str, payload_json: str) -> str:
    pattern = re.compile(
        r'(<script\b[^>]*\bid="' + re.escape(block_id) + r'"[^>]*>)(.*?)(</script>)',
        re.DOTALL,
    )
    found = len(pattern.findall(html))
    if found != 1:
        raise ValueError(f'expected exactly one <script id="{block_id}"> block, found {found}')
    return pattern.sub(lambda m: m.group(1) + payload_json + m.group(3), html)


def write_atomic(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replace the embedded data block of a dynamic HTML report.")
    parser.add_argument("html", type=Path, help="report HTML to update")
    parser.add_argument("data", type=Path, help="new data (.csv or .json)")
    parser.add_argument("--id", default="report-data", help='id of the <script> data block (default: "report-data")')
    parser.add_argument("--out", type=Path, help="write here instead of overwriting the input HTML")
    args = parser.parse_args(argv)

    try:
        payload = build_payload(args.data)
        updated = inject(args.html.read_text(encoding="utf-8"), args.id, to_script_json(payload))
        out = args.out or args.html
        write_atomic(out, updated)
    except (OSError, ValueError) as e:
        print(f"inject_data: {e}", file=sys.stderr)
        return 1

    print(f"inject_data: {payload['meta']['n_rows']} rows from {args.data.name} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
