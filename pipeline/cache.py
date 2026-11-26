"""Small content-hash cache shared by keyframe and moving-shot stages."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "outputs" / "cache_manifest.json"


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def input_digest(parameters: dict) -> str:
    packed = json.dumps(parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return digest_bytes(packed)


def read_manifest() -> dict:
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "entries": {}}


def cache_hit(manifest: dict, key: str, signature: str, output_path: Path) -> bool:
    entry = manifest.get("entries", {}).get(key, {})
    return (
        output_path.is_file()
        and entry.get("input_sha256") == signature
        and entry.get("output_sha256") == digest_file(output_path)
    )


def record_output(manifest: dict, key: str, signature: str, output_path: Path) -> None:
    manifest.setdefault("version", 1)
    manifest.setdefault("entries", {})[key] = {
        "input_sha256": signature,
        "output_sha256": digest_file(output_path),
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
