import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from c3r_evals.source_admission import SourcePolicy, admit_source
from scripts.audit_laya_train import audit


def laya_source(partition: str = "train") -> SourcePolicy:
    return SourcePolicy(
        source_id="LocalLLaMA/typed-decisions",
        revision="c76749ec58bd8c3d2ea706b31c333a9059c38f90",
        file_sha256="46a58d63edfd86e23229c78afe8b72307bb4ca9fb0e8df180cabb3c67ec9dcd5",
        license_id="Apache-2.0",
        evidence_kind="synthetic",
        partition=partition,
        rights_basis="public dataset license",
        consent_basis="publisher-provided synthetic records; no customer data",
        retention_rule="retain pinned public revision while attribution remains",
        publication_scope="attributed-derived",
    )


class SourceAdmissionTests(unittest.TestCase):
    def test_laya_synthetic_train_is_admitted_only_for_synthetic_training(self):
        decision = admit_source(laya_source(), use="training", claim="synthetic")
        self.assertEqual(decision.source_id, "LocalLLaMA/typed-decisions")
        self.assertEqual(decision.claim, "synthetic")

    def test_laya_cannot_be_called_empirical_or_calibration(self):
        with self.assertRaisesRegex(ValueError, "synthetic source"):
            admit_source(laya_source(), use="training", claim="empirical")
        with self.assertRaisesRegex(ValueError, "synthetic source"):
            admit_source(laya_source(), use="calibration", claim="synthetic")

    def test_upstream_test_is_sealed(self):
        for use in ("training", "calibration"):
            with self.subTest(use=use), self.assertRaisesRegex(ValueError, "sealed"):
                admit_source(laya_source("test"), use=use, claim="synthetic")

    def test_mutable_revision_or_missing_rights_is_rejected(self):
        from dataclasses import replace

        with self.assertRaisesRegex(ValueError, "immutable"):
            admit_source(replace(laya_source(), revision="main"), use="training", claim="synthetic")
        with self.assertRaisesRegex(ValueError, "rights_basis"):
            admit_source(replace(laya_source(), rights_basis=""), use="training", claim="synthetic")

    def test_controlled_runs_do_not_prove_field_performance(self):
        from dataclasses import replace

        controlled = replace(laya_source(), evidence_kind="controlled")
        admit_source(controlled, use="calibration", claim="controlled")
        with self.assertRaisesRegex(ValueError, "field evidence"):
            admit_source(controlled, use="publication", claim="production")

    def test_invalid_partition_and_no_publication_rights_fail_closed(self):
        from dataclasses import replace

        with self.assertRaisesRegex(ValueError, "partition"):
            admit_source(replace(laya_source(), partition="TEST"), use="training", claim="synthetic")
        with self.assertRaisesRegex(ValueError, "publication scope"):
            admit_source(
                replace(laya_source(), publication_scope="none"),
                use="publication",
                claim="synthetic",
            )

    def test_audit_rejects_unpinned_file_before_parquet_read(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "untrusted.parquet"
            path.write_bytes(b"not the pinned dataset")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                audit(path, laya_source())


if __name__ == "__main__":
    unittest.main()
