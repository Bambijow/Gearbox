"""Guard against false optimization wins."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import optimization_holdout as holdout
from codex_worker import build_command

class HoldoutTests(unittest.TestCase):
    def setUp(self):
        self.report={"holdout_disclosed_before_variant":False,"holdout_mutated":False,
            "workload_equivalent":True,"required_work_skipped":False,"correctness_pass":True,
            "budget":{"attempts":2},"usage":{"attempts":1},
            "baseline":{"training":[100,101,100],"holdout":[100,101,100]},
            "candidate":{"training":[70,71,70],"holdout":[70,71,70]}}
    def test_real_gain(self):
        self.assertEqual(holdout.adjudicate(self.report)["decision"],"KEEP")
    def test_training_only_gain_rejected(self):
        self.report["candidate"]["holdout"]=[101,100,101]
        self.assertEqual(holdout.adjudicate(self.report)["decision"],"REJECT")
    def test_skipped_work_rejected(self):
        self.report["required_work_skipped"]=True
        self.assertEqual(holdout.adjudicate(self.report)["decision"],"REJECT")
    def test_changed_holdout_rejected(self):
        self.report["holdout_mutated"]=True
        self.assertEqual(holdout.adjudicate(self.report)["decision"],"REJECT")
    def test_budget_breach_rejected(self):
        self.report["usage"]["attempts"]=3
        self.assertEqual(holdout.adjudicate(self.report)["decision"],"REJECT")
    def test_codex_isolated_command(self):
        cmd=build_command(codex_bin="codex",worktree=Path("/tmp/worktree"),
            schema=Path("/tmp/schema.json"),result=Path("/tmp/result.json"),
            sandbox="read-only",ignore_user_config=True)
        self.assertIn("--ignore-user-config",cmd)

if __name__=="__main__":
    unittest.main()
