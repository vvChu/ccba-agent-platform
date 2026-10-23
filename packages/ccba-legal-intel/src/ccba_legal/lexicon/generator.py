"""Static Python Code Generator for CCILF Taxonomy (COND-17).

Compiles canonical_construction_taxonomy.yaml into a zero-IO, offline-capable
Python module (_generated_taxonomy.py) for distribution wheels and edge runtimes.
Generates compact, high-performance static data respecting the 800-LOC module budget.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

DEFAULT_YAML_SOURCE = (
    Path(__file__).parent.parent / "resources" / "canonical_construction_taxonomy.yaml"
)
DEFAULT_OUTPUT_MODULE = Path(__file__).parent / "_generated_taxonomy.py"


def compile_taxonomy_to_py(
    yaml_path: Path = DEFAULT_YAML_SOURCE,
    output_path: Path = DEFAULT_OUTPUT_MODULE,
) -> Path:
    """Compiles YAML taxonomy into static Python code module.

    Args:
        yaml_path: Path to canonical taxonomy YAML source of truth.
        output_path: Target path for the generated Python module.

    Returns:
        Path to the generated module.
    """
    raw_bytes = yaml_path.read_bytes()
    sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
    data: dict[str, Any] = yaml.safe_load(raw_bytes) or {}

    version = data.get("schema_version", data.get("taxonomy_version", "2026.10.1"))
    json_payload = json.dumps(data, ensure_ascii=False)

    lines = [
        '"""AUTO-GENERATED FILE — DO NOT EDIT DIRECTLY.',
        "",
        f"Generated from: {yaml_path.name}",
        f"Source SHA-256: {sha256_hash}",
        f"Version: {version}",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "import json",
        "",
        f'TAXONOMY_VERSION: str = "{version}"',
        f'TAXONOMY_SHA256: str = "{sha256_hash}"',
        "",
        f"_RAW_JSON: str = {json.dumps(json_payload)}",
        "",
        "CANONICAL_TAXONOMY: dict = json.loads(_RAW_JSON)",
        'TERMS: dict = CANONICAL_TAXONOMY.get("terms", {})',
        "",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    compile_taxonomy_to_py()
