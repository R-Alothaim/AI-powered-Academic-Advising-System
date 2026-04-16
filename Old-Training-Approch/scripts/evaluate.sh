#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# evaluate.sh — Run evaluation suite against the distilled model.
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

source "${PROJECT_ROOT}/.env"
export PROJECT_ROOT

echo "══════════════════════════════════════════════"
echo "  Evaluation Suite"
echo "══════════════════════════════════════════════"

# Ensure cleaned eval data exists
if [ ! -f "cache/data/eval_clean.jsonl" ]; then
    echo "Cleaned eval data not found — running prepare_data.sh first..."
    bash "${SCRIPT_DIR}/prepare_data.sh"
fi

python3 - <<'PYEOF'
import json, logging, os, sys, yaml
sys.path.insert(0, os.path.join(os.environ.get("PROJECT_ROOT", "."), "src"))

from advisor.data.loader import load_local
from advisor.evaluation.runner import run_evaluation

logging.basicConfig(level=logging.INFO, format="%(levelname)-5s  %(message)s")

config_path = os.path.join(os.environ["PROJECT_ROOT"], "configs", "eval.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

# Resolve env vars
def resolve(obj):
    if isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        return os.environ.get(obj[2:-1], obj)
    if isinstance(obj, dict):
        return {k: resolve(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve(v) for v in obj]
    return obj

config = resolve(config)

eval_records = load_local("cache/data/eval_clean.jsonl")
results = run_evaluation(config, eval_records)

print("\n" + "=" * 55)
print("  RESULTS")
print("=" * 55)
print(json.dumps(results, indent=2))
PYEOF

echo "✓ Evaluation complete."
