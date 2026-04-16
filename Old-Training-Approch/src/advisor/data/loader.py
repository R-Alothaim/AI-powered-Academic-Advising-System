"""Fetch datasets from cloud storage or API endpoints."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def fetch_dataset(uri: str, cache_dir: str | None = None) -> list[dict[str, Any]]:
    """Fetch a JSONL dataset from a remote URI.

    If *cache_dir* is set, the file is cached locally to avoid repeated
    downloads.  Supports any HTTP(S) endpoint that returns JSONL.
    """
    if cache_dir:
        cache_path = Path(cache_dir) / _uri_to_filename(uri)
        if cache_path.exists():
            logger.info("Loading cached dataset from %s", cache_path)
            return _read_jsonl(cache_path)

    logger.info("Fetching dataset from %s", uri)
    resp = httpx.get(uri, timeout=120, follow_redirects=True)
    resp.raise_for_status()

    records = [json.loads(line) for line in resp.text.strip().splitlines() if line.strip()]
    logger.info("Fetched %d records", len(records))

    if cache_dir:
        cache_path = Path(cache_dir) / _uri_to_filename(uri)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        _write_jsonl(records, cache_path)
        logger.info("Cached to %s", cache_path)

    return records


def load_local(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSONL file from a local path."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    return _read_jsonl(path)


def save_local(records: list[dict[str, Any]], path: str | Path) -> int:
    """Write records to a local JSONL file. Returns count written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_jsonl(records, path)
    return len(records)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno} — bad JSON: {exc}") from exc
    return records


def _write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _uri_to_filename(uri: str) -> str:
    """Derive a safe cache filename from a URI."""
    import hashlib
    return hashlib.sha256(uri.encode()).hexdigest()[:16] + ".jsonl"
