#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# prepare_data.sh — Fetch cloud datasets, validate, clean, and split.
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

source "${PROJECT_ROOT}/.env"

echo "══════════════════════════════════════════════"
echo "  Data Preparation Pipeline"
echo "══════════════════════════════════════════════"

python3 - <<'PYEOF'
import logging, os, sys
sys.path.insert(0, os.path.join(os.environ.get("PROJECT_ROOT", "."), "src"))

from advisor.data.loader import fetch_dataset, save_local
from advisor.data.schema import validate_records
from advisor.data.cleaner import clean_dataset

logging.basicConfig(level=logging.INFO, format="%(levelname)-5s  %(message)s")
log = logging.getLogger("prepare")

train_uri = os.environ["DATASET_TRAIN_URI"]
eval_uri  = os.environ["DATASET_EVAL_URI"]
cache     = os.environ.get("DATA_CACHE_DIR", "./cache/data")

for label, uri, out in [
    ("train", train_uri, "cache/data/train_clean.jsonl"),
    ("eval",  eval_uri,  "cache/data/eval_clean.jsonl"),
]:
    log.info("── %s ──", label.upper())

    records = fetch_dataset(uri, cache_dir=cache)
    log.info("Fetched %d records", len(records))

    valid, errors = validate_records(records)
    if errors:
        log.warning("%d validation errors:", len(errors))
        for e in errors[:5]:
            log.warning("  %s", e)

    cleaned = clean_dataset(valid)
    n = save_local(cleaned, out)
    log.info("Wrote %d cleaned records → %s\n", n, out)

log.info("Done.")
PYEOF

echo "✓ Data preparation complete."
