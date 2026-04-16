#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# train.sh — Run knowledge distillation on a cloud VM.
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

source "${PROJECT_ROOT}/.env"
export PROJECT_ROOT

echo "══════════════════════════════════════════════"
echo "  Knowledge Distillation Training"
echo "══════════════════════════════════════════════"
echo "  Teacher : ${TEACHER_MODEL_NAME}"
echo "  Student : ${STUDENT_MODEL_NAME}"
echo "  Device  : $(python3 -c 'import torch; print("cuda" if torch.cuda.is_available() else "cpu")')"
echo "══════════════════════════════════════════════"

# Ensure cleaned data exists
if [ ! -f "cache/data/train_clean.jsonl" ]; then
    echo "Cleaned data not found — running prepare_data.sh first..."
    bash "${SCRIPT_DIR}/prepare_data.sh"
fi

python3 - <<'PYEOF'
import logging, os, sys, yaml
sys.path.insert(0, os.path.join(os.environ.get("PROJECT_ROOT", "."), "src"))

from advisor.data.loader import load_local
from advisor.distillation.trainer import DistillationTrainer
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(levelname)-5s  %(message)s")
log = logging.getLogger("train")

config_path = os.path.join(os.environ["PROJECT_ROOT"], "configs", "distill.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

# Resolve env vars in config strings
def resolve(obj):
    if isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        return os.environ.get(obj[2:-1], obj)
    if isinstance(obj, dict):
        return {k: resolve(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve(v) for v in obj]
    return obj

config = resolve(config)

records = load_local("cache/data/train_clean.jsonl")
log.info("Loaded %d cleaned training records", len(records))

seed = config["data"]["seed"]
val_ratio = config["data"]["val_split"]
train_recs, val_recs = train_test_split(records, test_size=val_ratio, random_state=seed)
log.info("Split: %d train / %d val", len(train_recs), len(val_recs))

trainer = DistillationTrainer(config)
best_ckpt = trainer.train(train_recs, val_recs)
log.info("Best checkpoint: %s", best_ckpt)
PYEOF

echo "✓ Training complete."
