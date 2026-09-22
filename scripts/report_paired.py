"""Evaluate redacted same-state baseline/C3R JSONL observations."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from c3r_evals.paired import PairedObservation, paired_report
from c3r_evals.source_admission import SourcePolicy, admit_source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--claim", required=True, choices=("controlled", "empirical"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source = SourcePolicy(**json.loads(args.source.read_text(encoding="utf-8")))
    try:
        admission = admit_source(source, use="benchmark", claim=args.claim)
        observations = [
            PairedObservation(**json.loads(line))
            for line in args.observations.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        report = paired_report(observations)
    except (TypeError, ValueError) as error:
        parser.error(str(error))
    result = {
        "source_admission": asdict(admission),
        "observation_count": len(observations),
        "report": report,
        "qualification": "descriptive paired report only; independent provenance review required",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
