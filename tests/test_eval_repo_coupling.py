"""Regression tests for isolated evals, repo identity and history-only analysis."""
from __future__ import annotations
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"scripts"/(name+".py"))
    value=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

def git(repo,*args):
    return subprocess.check_output(["git","-C",str(repo),*args],text=True).strip()

class HardeningTests(unittest.TestCase):
    def test_eval_does_not_inherit_untrusted_codex_or_claude_files(self):
        tool=module("behavior_eval")
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); old=root/"profile"
            (old/".codex"/"skills").mkdir(parents=True)
            (old/".codex"/"config.toml").write_text("untrusted = true")
            (old/".codex"/"skills"/"secret.md").write_text("malicious instruction")
            (old/".codex"/"auth.json").write_text('{"token":"fixture"}')
            for provider in ("claude","codex"):
                env=tool.isolated_environment(provider,root/provider,{"HOME":str(old)})
                self.assertNotEqual(env["HOME"],str(old))
                self.assertNotIn(str(old),env["XDG_CONFIG_HOME"])
                if provider=="codex":
                    self.assertTrue((Path(env["CODEX_HOME"])/"auth.json").exists())
                    self.assertFalse((Path(env["CODEX_HOME"])/"skills").exists())
                else:
                    self.assertFalse((Path(env["CLAUDE_CONFIG_DIR"])/"CLAUDE.md").exists())

    def test_wrong_repository_rejected(self):
        tool=module("worktree_manager")
        with tempfile.TemporaryDirectory() as td:
            roots=[Path(td)/name for name in ("a","b")]
            for root in roots:
                root.mkdir();git(root,"init")
            with self.assertRaisesRegex(ValueError,"REPOSITORY_MISMATCH"):
                tool.verify_repo(roots[0],roots[1])
            self.assertEqual(tool.verify_repo(roots[0],roots[0]),str(roots[0].resolve()))

    def test_cochange_counts_are_deterministic(self):
        tool=module("cochange_diagnostic")
        pairs=tool.analyze([["a.py","b.py"],["a.py","b.py"],["a.py","b.py"],["a.py","c.py"]],minimum=3)
        self.assertEqual(pairs,[{"files":["a.py","b.py"],"cochanges":3,"conditional_overlap":1.0}])
        self.assertEqual(tool.analyze([["a.py","b.py"]],minimum=3),[])

if __name__=="__main__":unittest.main()
