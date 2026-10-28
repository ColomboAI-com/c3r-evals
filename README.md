# c3r-evals

Evidence tooling for **C3R: Robust Calibrated Compute Control**. This repository
turns governed traces into reproducible splits, calibration reports, and
provider-qualification evidence without storing prompts, responses, or secrets.

## Guarantees

- every record carries source, license, consent, collection-time, and content hashes;
- deterministic group-aware train/validation/calibration/test splits;
- exact and normalized-content contamination checks fail closed;
- Brier, NLL, ECE, MCE, accuracy, coverage, and selective-risk reports;
- provider probes are bounded and emit redacted, hash-addressed evidence.

This is evaluation infrastructure, not a claim that C3R is empirically qualified.
Published artifacts must include their manifest and pass `python -m unittest`.

## Laya source admission

The [Laya-associated typed-decisions dataset](https://huggingface.co/datasets/LocalLLaMA/typed-decisions)
is pinned in `sources/laya-typed-decisions-train.json` at revision
`c76749ec58bd8c3d2ea706b31c333a9059c38f90`. Its public card describes
synthetic scenarios and teacher labels. It may seed an attributed **synthetic**
training or benchmark slice; it is not observed C3R task-outcome data. The
upstream test split is sealed from training and C3R calibration. DeepSeek-generated
proposals likewise remain model-generated until independently adjudicated.

Run the fail-closed preflight before ingesting or releasing a source:

```bash
python scripts/check_source.py sources/laya-typed-decisions-train.json --use training --claim synthetic
```

The check rejects synthetic-to-empirical promotion, synthetic release calibration,
test-split contamination, and mutable or incomplete source declarations. It does
not independently verify the stated rights, consent, file hashes, or outcomes;
those require a separate provenance review. A passing source check alone can
never authorize a production claim.

The pinned public **train** Parquet file was audited with
`scripts/audit_laya_train.py` and optional `pyarrow` support
(`pip install '.[parquet]'`). Its SHA-256 matches
the registry, all 1,200 rows declare `train`, and 1,200 distinct synthetic states
were found across four workflows. The aggregate-only
[`sources/laya-typed-decisions-train.audit.json`](sources/laya-typed-decisions-train.audit.json)
records the counts and question types; no raw rows were committed. Reproduce with:

```bash
python scripts/audit_laya_train.py /path/to/all/train-00000-of-00001.parquet \
  --source sources/laya-typed-decisions-train.json \
  --output sources/laya-typed-decisions-train.audit.json
```

## Paired evaluation contract

`scripts/report_paired.py` consumes redacted JSONL observations with one
`baseline` and one `c3r` arm per task. Both arms must have the same state hash;
each must carry a unique trace hash, an independent outcome-label reference,
an explicit outcome kind, measured latency/cost, and an authority-bypass flag.
Missing arms, mismatched
states, duplicate traces, and invalid measurements fail closed. The report is
descriptive, not a production qualification or a substitute for inspecting the
underlying outcome labels. It requires a non-synthetic source policy, so the
Laya train manifest cannot be used to produce an empirical paired report.

The first [controlled report](sources/c3r-controlled-pairs-v1.report.json) covers
five C3R-authored local fixtures. Its positive label is **policy-rubric match**,
not task success; timing is a single-run smoke observation. No trained model,
provider, customer traffic, or live Colibri route is included. The pinned
redacted [raw observations](https://github.com/ColomboAI-com/c3r/blob/feat/standalone-runtime/evidence/controlled-pairs-v1/observations.jsonl)
and rubric generator are in the C3R draft branch.

## Quick start

```bash
python -m unittest discover -s tests
python scripts/qualify_openrouter.py --model MODEL_ID --output evidence.json
```

The provider probe requires `OPENROUTER_API_KEY`. It sends one fixed, non-sensitive
prompt with a hard cap of 256 generated tokens and never writes response content.
Reasoning-only output is not counted as a completed response. The redacted evidence
files cover one DeepSeek, one Qwen, and one frontier-model OpenRouter call, plus a
private self-hosted DeepSeek serving-budget observation. They are protocol smoke tests,
not end-to-end C3R qualification or evidence of comparative task success.
