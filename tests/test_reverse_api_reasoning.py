"""Deterministic regression tests for passive API reverse and reasoning controls."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import api_reconstruct
import contract_challenge
import decision_trace
import investigation_plan
import final_review_router


def demo_har():
    def entry(method, url, code, request_body=None, response_body=None):
        req = {"method": method, "url": url, "headers": [{"name": "Authorization", "value": "Bearer TOPSECRET"}],
               "postData": {"mimeType": "application/json", "text": json.dumps(request_body)} if request_body is not None else {}}
        res = {"status": code, "headers": [{"name": "Set-Cookie", "value": "session=SECRET"}],
               "content": {"mimeType": "application/json", "text": json.dumps(response_body)} if response_body is not None else {}}
        return {"request": req, "response": res}
    return {"log": {"version": "1.2", "entries": [
        entry("POST", "https://internal.example/orders?access_token=SECRET", 201,
              {"quantity": 3, "password": "TOPSECRET"}, {"id": "hello-private", "status": "pending"}),
        entry("GET", "https://internal.example/orders/123?session=TOPSECRET", 200,
              response_body={"id": 123, "status": "pending"}),
        entry("GET", "https://internal.example/orders/456", 404,
              response_body={"message": "TOPSECRET"})]}}


class ApiReverseTests(unittest.TestCase):
    def test_offline_har_observations_are_not_api_truth(self):
        data = api_reconstruct.inspect_har(demo_har(), "f" * 64)
        self.assertEqual(data["status"], "OBSERVED_ONLY")
        self.assertEqual([(x["method"], x["path_template"]) for x in data["operations"]],
                         [("POST", "/orders"), ("GET", "/orders/{numeric}")])
        self.assertEqual(data["operations"][1]["statuses"], [200, 404])
        body = json.dumps(data)
        for secret in ("TOPSECRET", "internal.example", "hello-private", "access_token=", "session="):
            self.assertNotIn(secret, body)
        self.assertNotIn("required", json.dumps(data["openapi_candidate"]))
        self.assertTrue(all(p["requires_authorization"] for p in data["candidate_probes"]))

    def test_invalid_entries_cannot_invent_observed_status(self):
        data = demo_har()
        data["log"]["entries"].append({"request": {"method": "GET", "url": "file:///passwd"}, "response": {"status": 200}})
        parsed = api_reconstruct.inspect_har(data, "x")
        self.assertEqual(len(parsed["skipped"]), 1)
        self.assertEqual(parsed["skipped"][0]["reason"], "unparseable URL")
        for version in ("1.1", 1, None):
            data["log"]["version"] = version
            with self.assertRaises(ValueError):
                api_reconstruct.inspect_har(data, "x")

    def test_url_template_does_not_disclose_secret_bearing_segments(self):
        for url in ("https://h.example/api/token/SUPERSECRET", "https://h.example/api/u/a@b.test",
                    "https://h.example/api/u/" + "a" * 70):
            self.assertIn("{opaque}", api_reconstruct.safe_path(url)[0])
        with self.assertRaises(ValueError):
            api_reconstruct.safe_path("ftp://example.test/root")

    def test_non_json_and_deep_structures_remain_explicitly_limited(self):
        value = {"a": {"b": {"c": {"d": {"e": {"f": {"g": "value"}}}}}}}
        output = api_reconstruct.shape(value)
        self.assertIn("max nesting depth", json.dumps(output))
        self.assertEqual(api_reconstruct.extract_json_shape({"text": "secret"}, "text/plain")["status"], "non-json-or-unknown")


class DecisionTraceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        path = self.root / "evidence.txt"
        path.write_text("exercised reference", encoding="utf-8")
        self.data = {"schema_version": 1, "run_id": "r1", "source_fingerprint": "source-A",
                     "evidence": [{"id": "E1", "path": "evidence.txt", "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                   "source_fingerprint": "source-A"}],
                     "decisions": [
                         {"id": "D1", "statement": "server returned 201", "kind": "observation", "decision_reason": "status observed",
                          "falsifier": "response with different status", "evidence_ids": ["E1"], "depends_on": [], "affected_tasks": ["API-1"]},
                         {"id": "D2", "statement": "port response shape", "kind": "approved-target", "approval_pointer": "spec.md#decision-1",
                          "decision_reason": "user accepted", "falsifier": "contradicting target acceptance", "evidence_ids": ["E1"],
                          "depends_on": ["D1"], "affected_tasks": ["PORT-2"]}]}

    def test_verified_ledger_and_changed_evidence_invalidates_descendants(self):
        ok = decision_trace.inspect_ledger(self.data, self.root)
        self.assertEqual(ok["status"], "VERIFIED_LEDGER")
        invalid = decision_trace.inspect_ledger(self.data, self.root, ["E1"])
        self.assertEqual(invalid["status"], "REVALIDATION_REQUIRED")
        self.assertEqual([d["decision_id"] for d in invalid["invalidated_decisions"]], ["D1", "D2"])

    def test_missing_file_and_wrong_source_fail_closed(self):
        (self.root / "evidence.txt").unlink()
        self.assertEqual(decision_trace.inspect_ledger(self.data, self.root)["status"], "BLOCKED")
        self.data["source_fingerprint"] = "other"
        self.assertEqual(decision_trace.inspect_ledger(self.data, self.root)["status"], "BLOCKED")

    def test_dependency_cycle_and_unauthorized_approval_are_rejected(self):
        self.data["decisions"][0]["depends_on"] = ["D2"]
        self.assertEqual(decision_trace.inspect_ledger(self.data, self.root)["status"], "BLOCKED")
        self.data["decisions"][0]["depends_on"] = []
        self.data["decisions"][1].pop("approval_pointer")
        self.assertEqual(decision_trace.inspect_ledger(self.data, self.root)["status"], "BLOCKED")


class InvestigationTests(unittest.TestCase):
    def setUp(self):
        self.data = {"risk": "high", "uncertainty": "high", "hypotheses": ["A", "B", "C"],
                     "probes": [{"id": "weak", "cost": 2, "predictions": {"A": "same", "B": "same", "C": "same"}},
                                {"id": "decisive", "cost": 3, "predictions": {"A": "201", "B": "400", "C": "409"}}],
                     "probe_budget": 3}

    def test_risk_and_uncertainty_are_separate(self):
        p = investigation_plan.compile_plan(self.data)
        self.assertEqual(p["route"], "INVESTIGATE")
        self.assertEqual(p["selected_probe_ids"], ["decisive"])
        self.assertEqual(p["required_quality_floor"], "high")
        self.data["uncertainty"] = "known"
        p2 = investigation_plan.compile_plan(self.data)
        self.assertEqual(p2["route"], "PLAN")
        self.assertEqual(p2["required_quality_floor"], "high")
        self.assertEqual(p2["selected_probe_ids"], [])

    def test_spec_question_blocks_even_if_probe_is_available(self):
        self.data["blocking_product_questions"] = ["Is legacy behavior intentional?"]
        self.assertEqual(investigation_plan.compile_plan(self.data)["route"], "HUMAN_BLOCKED")
        self.data.pop("blocking_product_questions")
        self.data["probe_budget"] = 1
        self.assertEqual(investigation_plan.compile_plan(self.data)["route"], "EVIDENCE_BLOCKED")

    def test_incomplete_predictions_rejected(self):
        self.data["probes"][1]["predictions"].pop("C")
        with self.assertRaises(ValueError):
            investigation_plan.compile_plan(self.data)


class ChallengeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "proof.txt").write_text("real candidate fixture output")
        self.contract = {"source": {"fingerprint": "reference-1"}, "target": {"revision": "target-commit"},
                         "claims": [{"id": "C1", "material": True}]}
        self.report = {"schema_version": 1, "reference_fingerprint": "reference-1", "target_revision": "target-commit",
                       "challenges": [{"claim_id": "C1", "adversarial_input": "repeat POST and read stored state",
                                       "verdict": "NO_COUNTEREXAMPLE_OBSERVED",
                                       "evidence": {"path": "proof.txt", "sha256": hashlib.sha256((self.root / "proof.txt").read_bytes()).hexdigest()}}]}

    def test_fresh_evidence_is_reviewed_not_equivalence(self):
        r = contract_challenge.check(self.contract, self.report, self.root)
        self.assertEqual(r["status"], "REVIEWED_NOT_PROVEN")
        self.assertFalse(r["runtime_equivalence_proven"])

    def test_counterexample_or_missing_probe_cannot_pass(self):
        self.report["challenges"][0]["verdict"] = "COUNTEREXAMPLE"
        self.assertEqual(contract_challenge.check(self.contract, self.report, self.root)["status"], "REPAIR")
        self.report["challenges"] = []
        self.assertEqual(contract_challenge.check(self.contract, self.report, self.root)["status"], "GAPS")

    def test_stale_target_or_missing_proof_blocks(self):
        self.report["target_revision"] = "old-target"
        self.assertEqual(contract_challenge.check(self.contract, self.report, self.root)["status"], "BLOCKED")
        self.report["target_revision"] = "target-commit"
        (self.root / "proof.txt").unlink()
        self.assertEqual(contract_challenge.check(self.contract, self.report, self.root)["status"], "BLOCKED")

    def test_final_review_requires_challenge_for_transfer(self):
        base = ["--risk", "low", "--failure-visibility", "loud-local", "--task-review-gates", "passed",
                "--coverage-status", "complete", "--quality-aggregate", "pass", "--behavior-transfer"]
        with self.assertRaises(ValueError):
            final_review_router.route(final_review_router.parser().parse_args(base))
        r = final_review_router.route(final_review_router.parser().parse_args(base + ["--contract-challenge-status", "reviewed"]))
        self.assertEqual(r.mode, "focused")
        for status in ("counterexample", "gaps"):
            with self.subTest(status=status), self.assertRaises(ValueError):
                final_review_router.route(final_review_router.parser().parse_args(base + ["--contract-challenge-status", status]))


if __name__ == "__main__":
    unittest.main()
