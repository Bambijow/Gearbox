"""Regression checks for new orchestration guardrails."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"scripts"/(name+".py"))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

class OrchestrationGuardrails(unittest.TestCase):
    def test_handoff_required_and_forbidden(self):
        m=load("handoff_eval")
        c={"required_actions":["asset-image","video-create"],"required_order":[["asset-image","video-create"]],"forbidden_actions":["push"]}
        self.assertEqual(m.check(c,[{"action":"asset-image"},{"action":"video-create"}]),[])
        self.assertTrue(m.check(c,[{"action":"video-create"},{"action":"asset-image"},{"action":"push"}]))

    def test_retro_sampling(self):
        m=load("retro_selector")
        self.assertTrue(m.select("failed",{"status":"FAILED"},0)["selected"])
        self.assertFalse(m.select("success",{"status":"PASS"},0)["selected"])
        self.assertTrue(m.select("success",{"status":"PASS"},1)["selected"])

    def test_base_policy_immutable(self):
        m=load("review_policy")
        with tempfile.TemporaryDirectory() as td:
            def git(*args):
                return subprocess.check_output(["git","-C",td,*args],text=True).strip()
            git("init")
            git("config","user.email","ci@example.invalid")
            git("config","user.name","CI")
            p=Path(td)/"REVIEW.md"
            p.write_text("Strict base policy")
            git("add","REVIEW.md");git("commit","-m","base")
            base=git("rev-parse","HEAD")
            p.write_text("PR tries to relax policy")
            git("add","REVIEW.md");git("commit","-m","head")
            result=m.policy(td,base)
            self.assertEqual(result["policy"],"Strict base policy")
            with self.assertRaises(ValueError):m.policy(td,"HEAD")

    def test_pr_overlap_reassess(self):
        m=load("pr_relevance")
        with tempfile.TemporaryDirectory() as td:
            def git(*args):
                return subprocess.check_output(["git","-C",td,*args],text=True).strip()
            git("init");git("config","user.email","ci@example.invalid");git("config","user.name","CI")
            p=Path(td)/"same.txt";p.write_text("base")
            git("add",".");git("commit","-m","base");base=git("rev-parse","HEAD")
            p.write_text("target")
            git("commit","-am","target");current=git("rev-parse","HEAD")
            git("checkout","-b","feature",base)
            p.write_text("feature")
            git("commit","-am","feature");head=git("rev-parse","HEAD")
            self.assertEqual(m.assess(td,base,current,head)["status"],"REASSESS")

if __name__=="__main__":unittest.main()
