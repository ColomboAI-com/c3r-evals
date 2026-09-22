"""Audit the pinned Laya-associated synthetic train file without exporting row content."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from c3r_evals.source_admission import SourcePolicy, admit_source


def audit(parquet_file: Path, source: SourcePolicy) -> dict[str, object]:
    admit_source(source, use="training", claim="synthetic")
    digest = sha256(parquet_file.read_bytes()).hexdigest()
    if digest != source.file_sha256:
        raise ValueError("train file SHA-256 does not match the pinned source manifest")
    try:
        import pyarrow.parquet as pq
    except ImportError as error:
        raise RuntimeError("install the optional pyarrow dependency to audit Parquet") from error

    table = pq.read_table(parquet_file)
    required = {"id", "workflow", "split", "state", "questions", "gold", "n_questions"}
    if not required.issubset(table.column_names):
        raise ValueError("train file is missing required columns")
    ids: set[str] = set()
    state_hashes: set[str] = set()
    workflows: Counter[str] = Counter()
    question_types: Counter[str] = Counter()
    for row in table.select(sorted(required)).to_pylist():
        if row["split"] != "train":
            raise ValueError("sealed non-train row in training file")
        if not isinstance(row["id"], str) or row["id"] in ids:
            raise ValueError("missing or duplicate training id")
        ids.add(row["id"])
        state = json.loads(row["state"])
        questions = json.loads(row["questions"])
        gold = json.loads(row["gold"])
        if not isinstance(state, dict) or not isinstance(questions, dict) or not isinstance(gold, dict):
            raise ValueError("invalid typed-decision JSON object")
        if set(questions) != set(gold) or len(questions) != row["n_questions"]:
            raise ValueError("question and teacher-label keys differ")
        normalized = json.dumps(state, sort_keys=True, separators=(",", ":"))
        state_hash = sha256(normalized.encode("utf-8")).hexdigest()
        if state_hash in state_hashes:
            raise ValueError("duplicate synthetic state")
        state_hashes.add(state_hash)
        workflows[str(row["workflow"])] += 1
        for question in questions.values():
            question_types[str(question["type"])] += 1
    return {
        "source_id": source.source_id,
        "revision": source.revision,
        "file_sha256": digest,
        "evidence_kind": "synthetic",
        "partition": "train",
        "row_count": table.num_rows,
        "distinct_state_count": len(state_hashes),
        "workflow_counts": dict(sorted(workflows.items())),
        "question_type_counts": dict(sorted(question_types.items())),
        "outcome_label_basis": "upstream synthetic teacher labels; not independent C3R outcomes",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parquet_file", type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source = SourcePolicy(**json.loads(args.source.read_text(encoding="utf-8")))
    result = audit(args.parquet_file, source)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
