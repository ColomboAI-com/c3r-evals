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

## Quick start

```bash
python -m unittest discover -s tests
python scripts/qualify_openrouter.py --model MODEL_ID --output evidence.json
```

The provider probe requires `OPENROUTER_API_KEY`. It sends one fixed, non-sensitive
prompt with at most 16 generated tokens and never writes response content.

