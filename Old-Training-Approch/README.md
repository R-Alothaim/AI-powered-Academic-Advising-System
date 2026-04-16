# Academic Advisor

**Version:** `beta-1.0.9`
> **Notice:** Due to intellectual property (IP) rights, the release source code is not publicly shared in this repository.
> - This document is intended as a high-level technical overview of the system's design and methodology.
---

## Overview

A compact **student model** is trained via **knowledge distillation (KD)** from a larger **teacher model**, producing an efficient inference-time model that preserves the teacher's advisory behavior on curated study-plan Q&A.

---

## Knowledge Distillation

Knowledge distillation transfers the teacher's learned function to the student by matching output distributions rather than hard labels alone.

### Temperature-Scaled Softmax

Given logits `z`, both networks emit softened distributions:

```
p_i(T) = exp(z_i / T) / Σ_j exp(z_j / T)
```

For `T > 1`, the distribution flattens, amplifying the relative mass of non-argmax classes. This exposes the teacher's inter-class similarity structure — the *dark knowledge* absent from one-hot targets.

### Objective

The student minimizes a convex combination of supervised and distillation terms:

```
L = α · H(y, p_S(1)) + (1 − α) · T² · KL( p_T(T) ∥ p_S(T) )
```

Where:
- `H(y, p_S(1))` — cross-entropy between ground-truth labels and the student's unsoftened distribution.
- `KL( p_T(T) ∥ p_S(T) )` — KL-divergence between temperature-softened teacher and student distributions.
- `α ∈ [0, 1]` — weighting between hard-label and soft-target supervision.
- `T²` — gradient rescaling factor that compensates for the `1/T²` attenuation introduced by temperature scaling, keeping soft-target gradients on the same magnitude scale as hard-target gradients.

### Gradient Behavior

Differentiating the KL term with respect to student logits `z_S` yields:

```
∂L_KD / ∂z_S,i  =  (1/T) · ( p_S,i(T) − p_T,i(T) )
```

The student is pushed toward the teacher's full probability vector, not merely its argmax. Near-miss classes receive graded, informative gradients rather than a binary wrong/right signal.

### Why It Fits This Task

The answer space contains many semantically adjacent items (overlapping course codes, prerequisite chains, near-duplicate phrasings). Hard-label training treats all incorrect classes as equidistant from the target; KD preserves the teacher's learned metric over that space, yielding better generalization and more reliable refusal behavior on adversarial inputs at a fraction of the teacher's parameter count.

---

## Repository Structure

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

---

## Data Cleaning

Under knowledge distillation the student does not merely imitate the teacher's correct behavior — it imitates whatever distribution the teacher has been conditioned on. Any structural defect in the source corpus is therefore not a nuisance but an *attack surface*: noise that survives preprocessing is transferred through the soft-target channel with higher fidelity than through hard-label supervision alone. The preprocessing stage (`src/advisor/data/cleaner.py`) is accordingly treated as a first-class training artifact — deterministic, idempotent, content-addressed, and re-runnable from raw source — rather than an exploratory notebook step. It runs as a hard gate in `scripts/prepare_data.sh`; records that cannot be safely normalized are quarantined rather than silently dropped.

The pipeline targets six defect classes observed in the legacy corpus, each with a characterized root cause and a bounded remediation:

| Defect class | Root cause | Remediation |
|---|---|---|
| **Tokenizer-adverse Unicode** | Web-scraped source documents carried mixed Unicode artifacts — NFC/NFD inconsistencies, zero-width joiners, BOMs, non-breaking spaces, and bidi control characters — which fragment into distinct BPE token sequences for otherwise identical strings. | Unicode normalization to NFC, stripping of zero-width and bidi control code points, whitespace collapse to a single ASCII space, and enforcement of a fixed character whitelist per language. |
| **Label–context contradiction** | Upstream ETL joined course-catalog records against an out-of-sync prerequisite table, producing `(prompt, response)` pairs whose answer contradicts facts stated in the prompt (e.g. prompt lists CS201 as prerequisite, answer claims none). Distilling on contradictory targets teaches the student to ignore its own context. | Rule-based consistency checker cross-references entities mentioned in the prompt against the canonical course registry; contradicting records are quarantined for manual review rather than auto-repaired. |
| **PII and identifier leakage** | A subset of records was sourced from advising-session transcripts and retained student IDs, email addresses, and instructor names that were never intended for model exposure. Memorization risk is elevated under KD because rare tokens receive disproportionate soft-target mass. | Regex-and-NER cascade over the full corpus (emails, phone numbers, national-ID patterns, person-name spans from a lightweight NER pass), replaced with typed placeholders (`<STUDENT_ID>`, `<INSTRUCTOR>`); redaction audit log retained separately. |
| **Prompt-injection residue** | Paraphrase-augmented prompts occasionally included imperative strings copied from source web pages (`"ignore previous instructions and..."`) that the teacher had learned to refuse but that still pollute the student's input distribution as benign-looking tokens. | Pattern library of known injection surface forms is matched at ingestion; affected records are routed to a hardened subset used only for refusal-behavior distillation, not for factual supervision. |
| **Distributional skew across answer classes** | The paraphrase pipeline oversampled high-frequency courses (introductory requirements) by a factor of ~8× relative to upper-division electives, biasing the teacher's soft targets toward the head of the distribution and starving tail classes of gradient. | Per-answer-class frequency capping with stratified subsampling of the head and targeted re-paraphrasing of the tail; post-balance class entropy is asserted above a configured threshold in `prepare_data.sh`. |
| **Train/eval contamination** | Paraphrase augmentation was run before the eval split was held out, so near-duplicates of eval prompts (cosine similarity ≥ 0.92 under a sentence encoder) leaked into training and inflated reported metrics. | Embedding-based near-duplicate detection against the held-out eval set; any training record exceeding the similarity threshold is removed prior to distillation, and the check is re-run as a CI assertion. |

Each stage is unit-tested in `tests/` against fixtures drawn from the observed failure modes, emits before/after diffs keyed by a stable record hash, and is safe to re-run without side effects. The cleaning contract is explicit: **the student is distilled from a corpus whose defects have been characterized, bounded, and either removed or quarantined — never smoothed over.**

---

