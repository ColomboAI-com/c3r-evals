"""Print a machine-readable preflight admission decision for a source manifest."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from c3r_evals.source_admission import SourcePolicy, admit_source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--use", required=True, choices=("training", "calibration", "benchmark", "publication"))
    parser.add_argument("--claim", required=True, choices=("synthetic", "controlled", "empirical", "production"))
    args = parser.parse_args()
    source = SourcePolicy(**json.loads(args.manifest.read_text(encoding="utf-8")))
    try:
        decision = admit_source(source, use=args.use, claim=args.claim)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(asdict(decision), sort_keys=True))


if __name__ == "__main__":
    main()
