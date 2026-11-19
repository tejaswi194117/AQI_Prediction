"""Append lightweight provenance records for source extraction runs."""

import json
from datetime import datetime, timezone
from pathlib import Path


MANIFEST_FILE = Path("data/raw/extraction_manifest.jsonl")


def record_extraction(source, status, output_file=None, row_count=None, error=None):
    """Append one JSON record without storing credentials or response payloads."""
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "status": status,
        "output_file": str(output_file) if output_file else None,
        "row_count": row_count,
        "error": str(error) if error else None,
    }
    with MANIFEST_FILE.open("a", encoding="utf-8") as manifest:
        manifest.write(json.dumps(record, sort_keys=True) + "\n")
