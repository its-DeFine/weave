from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "scripts" / "weave_symphony_adapter.py"
SAMPLES = ROOT / "docs" / "samples" / "weave-symphony-adapter"

spec = importlib.util.spec_from_file_location("weave_symphony_adapter", ADAPTER_PATH)
assert spec is not None
weave_symphony_adapter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = weave_symphony_adapter
spec.loader.exec_module(weave_symphony_adapter)


def load_sample(name: str) -> dict:
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


class WeaveSymphonyAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.work_item = load_sample("work-item.valid.json")
        self.dispatch_item = load_sample("dispatch-item.valid.json")
        self.proof_envelope = load_sample("proof-envelope.valid.json")

    def test_sample_contracts_validate_and_invalid_samples_fail(self) -> None:
        weave_symphony_adapter.validate_work_item(self.work_item)
        weave_symphony_adapter.validate_dispatch_item(self.dispatch_item)
        weave_symphony_adapter.validate_proof_envelope(
            self.proof_envelope,
            dispatch_item=self.dispatch_item,
        )

        with self.assertRaises(weave_symphony_adapter.AdapterValidationError):
            weave_symphony_adapter.validate_work_item(
                load_sample("work-item.invalid-missing-proof-required.json")
            )

        with self.assertRaises(weave_symphony_adapter.AdapterValidationError):
            weave_symphony_adapter.validate_proof_envelope(
                load_sample("proof-envelope.invalid-overclaim.json"),
                dispatch_item=self.dispatch_item,
            )

    def test_normal_user_intent_becomes_complete_work_item_without_manual_stage(self) -> None:
        work_item = weave_symphony_adapter.work_item_from_intent(
            "Build the local adapter and prove local worker readback.",
            app_id="demo-adapter",
            work_item_id="wi-demo-adapter-engineering",
        )

        weave_symphony_adapter.validate_work_item(work_item)
        self.assertEqual(work_item["lifecycle_stage"], "engineering")
        self.assertEqual(work_item["intent_truth"]["scope_lattice"]["required_stages"], ["engineering"])
        self.assertFalse(work_item["intent_truth"]["scope_lattice"]["full_lifecycle_claim"])
        self.assertTrue(work_item["proof_required"])
        self.assertTrue(work_item["owner_boundary"]["requires_owner_approval"])
        self.assertTrue(work_item["non_claims"])

    def test_work_item_to_dispatch_item_preserves_weave_metadata(self) -> None:
        dispatch_item = weave_symphony_adapter.work_item_to_dispatch_item(self.work_item)

        self.assertEqual(dispatch_item["id"], self.dispatch_item["id"])
        self.assertEqual(dispatch_item["identifier"], self.dispatch_item["identifier"])
        self.assertEqual(dispatch_item["weave"]["app_id"], self.work_item["app_id"])
        self.assertEqual(dispatch_item["weave"]["work_item_id"], self.work_item["work_item_id"])
        self.assertEqual(dispatch_item["weave"]["lifecycle_stage"], self.work_item["lifecycle_stage"])
        self.assertEqual(dispatch_item["weave"]["proof_required"], self.work_item["proof_required"])
        self.assertEqual(dispatch_item["weave"]["non_claims"], self.work_item["non_claims"])

    def test_unsafe_or_gated_work_requires_gate_state_and_is_not_dispatchable_until_approved(self) -> None:
        gated = copy.deepcopy(self.work_item)
        gated["work_item_id"] = "wi-demo-calculator-deploy"
        gated["allowed_actions"] = ["deploy to production after approval"]
        gated["public_gate"] = {
            "required": True,
            "state": "pending_owner_approval",
            "reason": "production deploy is an external-effect action",
        }
        weave_symphony_adapter.validate_work_item(gated)
        self.assertFalse(weave_symphony_adapter.is_work_item_dispatchable(gated))

        missing_gate_state = copy.deepcopy(gated)
        missing_gate_state["public_gate"].pop("state")
        with self.assertRaises(weave_symphony_adapter.AdapterValidationError):
            weave_symphony_adapter.validate_work_item(missing_gate_state)

        with tempfile.TemporaryDirectory() as tmpdir:
            store = weave_symphony_adapter.LocalQueueStore(Path(tmpdir))
            store.enqueue_work_item(gated)
            with self.assertRaises(weave_symphony_adapter.AdapterStateError):
                store.dispatch_work_item(gated["work_item_id"])

    def test_prompt_includes_weave_lifecycle_proof_and_forbidden_action_requirements(self) -> None:
        prompt = weave_symphony_adapter.render_workflow_prompt(self.dispatch_item)

        self.assertIn("operating as a WEAVE lifecycle worker", prompt)
        self.assertIn("Lifecycle stage: `engineering`", prompt)
        self.assertIn("Intent Truth", prompt)
        self.assertIn("Owner Boundary", prompt)
        self.assertIn("Proof Required", prompt)
        self.assertIn("Required Proof Envelope Closeout", prompt)
        self.assertIn("Do not ask the owner to classify lifecycle stages manually", prompt)
        self.assertIn("do not mutate live tracker state", prompt)
        self.assertIn("do not deploy, publish, bill, or send public messages", prompt)
        self.assertIn("A completed worker result without a valid proof envelope is `revise`, not done", prompt)
        self.assertIn("done`, `blocked`, `needs_owner_action`, `revise`, `accepted_for_scope", prompt)

    def test_local_worker_process_happy_path_is_accepted_for_scope_and_preserves_non_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = weave_symphony_adapter.LocalQueueStore(Path(tmpdir))
            store.enqueue_work_item(self.work_item)
            dispatch_item = store.dispatch_next()

            envelope = weave_symphony_adapter.run_local_worker(
                store,
                work_item_id=self.work_item["work_item_id"],
            )
            weave_symphony_adapter.validate_proof_envelope(envelope, dispatch_item=dispatch_item)
            readback = weave_symphony_adapter.readback_from_store(
                store,
                work_item_id=self.work_item["work_item_id"],
            )

            self.assertEqual(readback["state"], "accepted_for_scope")
            self.assertEqual(readback["proof_state"], "valid")
            self.assertEqual(readback["non_claims"], self.work_item["non_claims"])
            self.assertEqual(envelope["reviewer"], "local-worker")
            self.assertTrue((Path(tmpdir) / "proofs" / f"{dispatch_item['id']}.proof.json").exists())
            self.assertTrue((Path(tmpdir) / "workspaces" / dispatch_item["id"] / "dispatch.json").exists())
            self.assertTrue((Path(tmpdir) / "workspaces" / dispatch_item["id"] / "WORKFLOW.md").exists())
            self.assertTrue((Path(tmpdir) / "workspaces" / dispatch_item["id"] / "worker-readback.json").exists())
            self.assertTrue((Path(tmpdir) / "workspaces" / dispatch_item["id"] / "proof.json").exists())

            events = store.state().events
            self.assertTrue(any(event["event_type"] == "worker_workspace_prepared" for event in events))
            self.assertTrue(any(event["event_type"] == "worker_run_completed" for event in events))

    def test_blocked_envelope_maps_to_blocked_with_exact_owner_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = weave_symphony_adapter.LocalQueueStore(Path(tmpdir))
            store.enqueue_work_item(self.work_item)
            store.dispatch_next()

            weave_symphony_adapter.run_fake_worker(
                store,
                outcome="blocked",
                work_item_id=self.work_item["work_item_id"],
            )
            readback = weave_symphony_adapter.readback_from_store(
                store,
                work_item_id=self.work_item["work_item_id"],
            )

            self.assertEqual(readback["state"], "blocked")
            self.assertEqual(readback["proof_state"], "valid")
            self.assertIn("Owner must approve", readback["next_action"])

    def test_incomplete_worker_closeout_is_rejected_as_revise(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = weave_symphony_adapter.LocalQueueStore(Path(tmpdir))
            store.enqueue_work_item(self.work_item)
            store.dispatch_next()

            weave_symphony_adapter.run_fake_worker(
                store,
                outcome="incomplete",
                work_item_id=self.work_item["work_item_id"],
            )
            readback = weave_symphony_adapter.readback_from_store(
                store,
                work_item_id=self.work_item["work_item_id"],
            )

            self.assertEqual(readback["state"], "revise")
            self.assertEqual(readback["proof_state"], "invalid")
            self.assertTrue(any("non_claims" in error for error in readback["validation_errors"]))
            self.assertTrue(any("artifacts" in error for error in readback["validation_errors"]))

    def test_overclaiming_worker_closeout_is_rejected_as_revise(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = weave_symphony_adapter.LocalQueueStore(Path(tmpdir))
            store.enqueue_work_item(self.work_item)
            store.dispatch_next()

            weave_symphony_adapter.run_fake_worker(
                store,
                outcome="overclaim",
                work_item_id=self.work_item["work_item_id"],
            )
            readback = weave_symphony_adapter.readback_from_store(
                store,
                work_item_id=self.work_item["work_item_id"],
            )

            self.assertEqual(readback["state"], "revise")
            self.assertEqual(readback["proof_state"], "invalid")
            self.assertTrue(any("claim exceeds proof surface" in error for error in readback["validation_errors"]))

    def test_replay_does_not_duplicate_active_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = weave_symphony_adapter.LocalQueueStore(Path(tmpdir))
            store.enqueue_work_item(self.work_item)

            first = store.dispatch_next()
            second = store.dispatch_next()
            events = store.state().events
            dispatch_created = [
                event for event in events if event["event_type"] == "dispatch_created"
            ]

            self.assertEqual(first["id"], second["id"])
            self.assertEqual(len(dispatch_created), 1)

            resumed = weave_symphony_adapter.LocalQueueStore(Path(tmpdir))
            third = resumed.dispatch_next()
            self.assertEqual(first["id"], third["id"])
            self.assertEqual(len(resumed.state().events), len(events))

    def test_completed_dispatch_without_valid_proof_maps_to_revise_not_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = weave_symphony_adapter.LocalQueueStore(Path(tmpdir))
            store.enqueue_work_item(self.work_item)
            dispatch_item = store.dispatch_next()
            store.mark_dispatch_state(dispatch_item["id"], "completed")

            readback = weave_symphony_adapter.readback_from_store(
                store,
                work_item_id=self.work_item["work_item_id"],
            )

            self.assertEqual(readback["state"], "revise")
            self.assertEqual(readback["proof_state"], "missing")
            self.assertIn("without a valid proof envelope", readback["next_action"])

    def test_invalid_lifecycle_and_missing_owner_boundary_fail_validation(self) -> None:
        bad_stage = copy.deepcopy(self.work_item)
        bad_stage["lifecycle_stage"] = "owner-made-up-stage"
        with self.assertRaises(weave_symphony_adapter.AdapterValidationError):
            weave_symphony_adapter.validate_work_item(bad_stage)

        missing_owner_boundary = copy.deepcopy(self.work_item)
        missing_owner_boundary.pop("owner_boundary")
        with self.assertRaises(weave_symphony_adapter.AdapterValidationError):
            weave_symphony_adapter.validate_work_item(missing_owner_boundary)

    def test_public_safety_validator_rejects_private_paths_and_credential_values(self) -> None:
        private_path_item = copy.deepcopy(self.work_item)
        private_path_item["worker_packet"]["target_surface"] = "/Users/" + "example/private"
        with self.assertRaises(weave_symphony_adapter.AdapterValidationError):
            weave_symphony_adapter.validate_work_item(private_path_item)

        credential_item = copy.deepcopy(self.work_item)
        credential_item["worker_packet"]["target_surface"] = "sk-" + ("a" * 24)
        with self.assertRaises(weave_symphony_adapter.AdapterValidationError):
            weave_symphony_adapter.validate_work_item(credential_item)


if __name__ == "__main__":
    unittest.main()
