#!/usr/bin/env python3
"""Validate a row-level visual asset catalog CSV.

The validator checks schema integrity, row completeness, unique identifiers,
path existence, confidence bounds, and common placeholder labels that weaken
visual evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

DEFAULT_FORBIDDEN = ["同上", "正在互动", "姿势自然", "场景普通"]


def parse_csv_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def resolve_path(raw: str, csv_path: Path, image_root: Path | None) -> Path:
    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        return candidate
    if image_root is not None:
        return (image_root / candidate).resolve()
    return (csv_path.parent / candidate).resolve()


def validate(args: argparse.Namespace) -> dict:
    csv_path = Path(args.csv_path).expanduser().resolve()
    expected = parse_csv_list(args.required_header)
    allow_empty = set(parse_csv_list(args.allow_empty))
    forbidden = parse_csv_list(args.forbidden) or DEFAULT_FORBIDDEN
    errors: list[str] = []

    if not csv_path.is_file():
        return {"csv": str(csv_path), "rows": 0, "columns": 0, "errors": [f"CSV not found: {csv_path}"]}

    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            rows = list(reader)
    except Exception as exc:  # pragma: no cover - CLI diagnostic path
        return {"csv": str(csv_path), "rows": 0, "columns": 0, "errors": [f"Could not read CSV: {exc}"]}

    if not rows:
        return {"csv": str(csv_path), "rows": 0, "columns": 0, "errors": ["CSV is empty"]}

    header = rows[0]
    if expected and header != expected:
        errors.append(f"Header mismatch. Expected {expected!r}, got {header!r}")
    if len(header) != len(set(header)):
        errors.append("Header contains duplicate field names")

    expected_width = len(header)
    data_rows = rows[1:]
    if not data_rows:
        errors.append("CSV has no data rows")

    image_root = Path(args.image_root).expanduser().resolve() if args.image_root else None
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    confidence_field = "整体置信度"

    for row_num, row in enumerate(data_rows, start=2):
        if len(row) != expected_width:
            errors.append(f"Row {row_num} has {len(row)} columns; expected {expected_width}")
            continue

        asset_id = row[0].strip()
        image_path_raw = row[1].strip()
        if not asset_id:
            errors.append(f"Row {row_num}: asset_id is empty")
        elif asset_id in seen_ids:
            errors.append(f"Row {row_num}: duplicate asset_id {asset_id!r}")
        seen_ids.add(asset_id)

        if not image_path_raw:
            errors.append(f"Row {row_num}: 图片路径 is empty")
        else:
            normalized = str(resolve_path(image_path_raw, csv_path, image_root))
            if normalized in seen_paths:
                errors.append(f"Row {row_num}: duplicate 图片路径 {image_path_raw!r}")
            seen_paths.add(normalized)
            if args.check_paths and not Path(normalized).is_file():
                errors.append(f"Row {row_num}: image path does not exist: {image_path_raw}")

        for field, value in zip(header[2:], row[2:]):
            if field in allow_empty:
                continue
            if not value.strip():
                errors.append(f"Row {row_num}: {field} is empty")
            for marker in forbidden:
                if marker and marker in value:
                    errors.append(f"Row {row_num}: {field} contains forbidden placeholder {marker!r}")

        if confidence_field in header:
            confidence = row[header.index(confidence_field)].strip()
            try:
                number = float(confidence)
                if not 0 <= number <= 1:
                    errors.append(f"Row {row_num}: 整体置信度 must be between 0 and 1, got {confidence!r}")
            except ValueError:
                errors.append(f"Row {row_num}: 整体置信度 is not numeric: {confidence!r}")

    return {
        "csv": str(csv_path),
        "rows": len(data_rows),
        "columns": len(header),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", help="CSV file to validate")
    parser.add_argument("--image-root", help="Root for resolving relative image paths")
    parser.add_argument("--required-header", help="Comma-separated expected header; omit to validate structure without imposing a schema")
    parser.add_argument("--allow-empty", help="Comma-separated fields allowed to be empty")
    parser.add_argument("--forbidden", help="Comma-separated placeholder strings to reject")
    parser.add_argument("--no-check-paths", dest="check_paths", action="store_false", help="Skip image path existence checks")
    parser.set_defaults(check_paths=True)
    args = parser.parse_args()
    result = validate(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
