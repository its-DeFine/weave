from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_context_index.py"

spec = importlib.util.spec_from_file_location("validate_context_index", SCRIPT_PATH)
assert spec is not None
validate_context_index = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validate_context_index
spec.loader.exec_module(validate_context_index)


class ValidateContextIndexTests(unittest.TestCase):
    def test_public_sample_validates(self) -> None:
        index = validate_context_index.load_index(REPO_ROOT / "docs/context-sources/livepeer-context-index.sample.json")

        validate_context_index.validate_index(index)

    def test_requires_all_three_application_paths(self) -> None:
        index = validate_context_index.load_index(REPO_ROOT / "docs/context-sources/livepeer-context-index.sample.json")
        for source in index["sources"]:
            source["application_paths"] = ["existing_api"]

        with self.assertRaises(validate_context_index.ValidationError):
            validate_context_index.validate_index(index)

    def test_rejects_schema_enum_and_pattern_violations(self) -> None:
        index = validate_context_index.load_index(REPO_ROOT / "docs/context-sources/livepeer-context-index.sample.json")
        index["sources"][0]["id"] = "Bad_ID"
        index["sources"][0]["stage_use"] = ["research", "invalid-stage"]
        index["sources"][0]["freshness"] = "eventually"

        with self.assertRaises(validate_context_index.ValidationError):
            validate_context_index.validate_index(index)

    def test_rejects_invalid_application_path_enum(self) -> None:
        index = validate_context_index.load_index(REPO_ROOT / "docs/context-sources/livepeer-context-index.sample.json")
        index["sources"][0]["application_paths"] = ["existing_api", "private_runtime"]

        with self.assertRaises(validate_context_index.ValidationError):
            validate_context_index.validate_index(index)


if __name__ == "__main__":
    unittest.main()
