#!/usr/bin/env python3
"""Read-only code-reference diagnostics for durable solution notes."""
import argparse
import ast
import re
import tempfile
from pathlib import Path
from solutions_audit import parse_fm

REF = re.compile(r"^[\w./-]+::[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*$")

def symbols(source):
    tree = ast.parse(source)
    result = set()
    def visit(body, prefix=""):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + node.name
                result.add(name)
                visit(node.body, name + ".")
    visit(tree.body)
    return result

def check(root, repo, allow_missing=False):
    errors = []
    if not root.exists():
        return errors if allow_missing else [f"missing solutions directory: {root}"]
    for note in sorted(root.rglob("*.md")):
        if note.name.lower() in {"index.md", "readme.md"}:
            continue
        fm = parse_fm(note.read_text(encoding="utf-8"))
        raw = fm.get("code_refs")
        if raw is None:
            continue
        if not raw.startswith("[") or not raw.endswith("]"):
            errors.append(f"{note}: code_refs must be an inline list")
            continue
        values = [x.strip().strip('"\'') for x in raw[1:-1].split(",") if x.strip()]
        if not values:
            errors.append(f"{note}: code_refs cannot be empty")
        for value in values:
            if not REF.fullmatch(value):
                errors.append(f"{note}: invalid code reference {value}")
                continue
            path, symbol = value.split("::", 1)
            file = (repo / path).resolve()
            if not file.is_relative_to(repo.resolve()) or not file.is_file():
                errors.append(f"{note}: missing or escaping code reference {path}")
                continue
            if file.suffix == ".py":
                try:
                    names = symbols(file.read_text(encoding="utf-8"))
                except (SyntaxError, UnicodeError) as exc:
                    errors.append(f"{note}: cannot inspect {path}: {exc}")
                    continue
                if symbol not in names:
                    errors.append(f"{note}: missing symbol {path}::{symbol}")
            else:
                errors.append(f"{note}: unsupported symbol language {path} (Python only)")
    return errors

def self_test():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        (root / "src" / "app.py").write_text("class Handler:\n    def run(self):\n        pass\n")
        notes = root / "docs" / "solutions"
        notes.mkdir(parents=True)
        p = notes / "note.md"
        p.write_text("---\ncode_refs: [src/app.py::Handler.run]\n---\n")
        assert check(notes, root) == []
        p.write_text("---\ncode_refs: [src/app.py::Handler.missing]\n---\n")
        assert any("missing symbol" in e for e in check(notes, root))
        p.write_text("---\ncode_refs: [../secret.py::Leak]\n---\n")
        assert check(notes, root)
    print("PASS: solution-refs self-test")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dir", type=Path, default=Path("docs/solutions"))
    p.add_argument("--repo-root", type=Path, default=Path("."))
    p.add_argument("--allow-missing", action="store_true")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        self_test()
        return
    errors = check(a.dir, a.repo_root, a.allow_missing)
    for error in errors:
        print(("ERROR" if a.strict else "WARN") + ": " + error)
    if errors and a.strict:
        raise SystemExit(1)
    print(f"PASS: solution reference check ({len(errors)} candidate(s))")

if __name__ == "__main__":
    main()
