"""Validate storyboard.json against its JSON Schema and film constraints."""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
STORYBOARD_PATH = ROOT / "storyboard.json"
SCHEMA_PATH = ROOT / "schema" / "storyboard.schema.json"


def main() -> int:
    try:
        storyboard = json.loads(STORYBOARD_PATH.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"Could not read {STORYBOARD_PATH}: {error}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as error:
        print(f"{STORYBOARD_PATH}: line {error.lineno}, column {error.colno}: {error.msg}", file=sys.stderr)
        return 1

    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"Could not read {SCHEMA_PATH}: {error}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as error:
        print(f"{SCHEMA_PATH}: line {error.lineno}, column {error.colno}: {error.msg}", file=sys.stderr)
        return 1

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(storyboard), key=lambda item: item.json_path)
    if errors:
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "storyboard"
            print(f"{location}: {error.message}", file=sys.stderr)
        return 1

    shots = storyboard["shots"]
    ids = [shot["id"] for shot in shots]
    if len(ids) != len(set(ids)):
        print("Shot IDs must be unique.", file=sys.stderr)
        return 1

    total_seconds = sum(shot["duration_seconds"] for shot in shots)
    if not 60 <= total_seconds <= 90:
        print(f"Total duration must be 60–90 seconds; storyboard is {total_seconds:g} seconds.", file=sys.stderr)
        return 1

    print(f"Storyboard valid: {len(shots)} shots, {total_seconds:g} seconds, language: {storyboard['language']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
