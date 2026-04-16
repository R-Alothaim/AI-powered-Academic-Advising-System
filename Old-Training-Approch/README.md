# Academic Advisor

AI-powered academic advising system. A smaller student model is trained via **knowledge distillation** from a larger teacher model, using curated study-plan Q&A datasets hosted in cloud storage.

## Architecture

```
academic-advisor/
├── configs/
│   ├── distill.yaml            # KD hyperparameters, model refs, data pipeline config
│   └── eval.yaml               # Evaluation thresholds and category definitions
├── src/advisor/
│   ├── data/
│   │   ├── loader.py           # Fetch datasets from cloud URIs (with local caching)
│   │   ├── schema.py           # Pydantic validation for chat-format records
│   │   └── cleaner.py          # Fix legacy data issues that caused hallucinations
│   ├── distillation/
│   │   ├── losses.py           # KD loss: alpha * CE + (1-alpha) * T^2 * KL-div
│   │   └── trainer.py          # Training loop with teacher inference + student update
│   ├── evaluation/
│   │   ├── metrics.py          # Exact match, refusal accuracy, token F1
│   │   └── runner.py           # Generate predictions and compute metrics
│   └── serving/
│       └── app.py              # FastAPI inference endpoint
├── scripts/
│   ├── prepare_data.sh         # Fetch → validate → clean → cache
│   ├── train.sh                # Run knowledge distillation
│   ├── evaluate.sh             # Eval suite with threshold checks
│   └── serve.sh                # Launch inference API
├── docker/
│   ├── Dockerfile.train        # GPU image for training on cloud VM
│   └── Dockerfile.serve        # Slim image for serving
└── tests/                      # Unit tests for cleaner, losses, metrics, loader
```

## Setup

```bash
pip install -e ".[dev]"
cp .env.example .env
# Fill in .env: dataset URIs, model names, WandB key
```

## Pipeline

```bash
# 1. Fetch cloud datasets, validate, clean, and cache locally
bash scripts/prepare_data.sh

# 2. Knowledge distillation (teacher → student)
bash scripts/train.sh

# 3. Evaluate the student model
bash scripts/evaluate.sh

# 4. Serve
bash scripts/serve.sh
```

## Data Cleaning

The legacy datasets contained issues that caused the model to hallucinate. The cleaning pipeline (`src/advisor/data/cleaner.py`) fixes these automatically before training:

| Issue | Root cause | Count | Fix |
|---|---|---|---|
| Broken grammar in user prompts | Automated paraphrasing generated malformed questions (`"what is how long..."`) | 300 | Regex-based rewrites to valid English |
| Bare-dash prerequisites | Missing data encoded as `"is -."` instead of readable text | 6 | Normalized to `"has no prerequisite"` |
| Wrong credit hours | ENG001/ENG002 incorrectly listed as 8 credit hours | 120 | Corrected to 3 (verified against source) |
| Inconsistent punctuation | Same canonical answer with/without colon | 2 | Normalized to single form |
| Exact duplicates | Paraphrasing pipeline produced identical Q/A pairs | ~150 | Deduplicated (first kept) |

## Evaluation

The eval dataset covers two classes:

- **Control** (91 pairs) — factual lookups the model must answer correctly
- **Adversarial** (159 pairs) — inputs the model must refuse (invented courses, fact mismatches, jailbreaks, cross-domain, vague prompts)

Pass/fail thresholds are configured in `configs/eval.yaml`.

## Tests

```bash
pytest
```
