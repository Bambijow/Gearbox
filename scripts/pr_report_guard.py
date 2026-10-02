#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

START = "<!-- gearbox-critical-code:start -->"
END = "<!-- gearbox-critical-code:end -->"
NONE = "<!-- gearbox-critical-code:none -->"
ENTRY_RE = re.compile(
    r"###\s+`(?P<path>[^`:\n]+(?:/[^`:\n]+)*):(?P<start>\d+)-(?P<end>\d+)`\s*\n"
    r"```(?P<lang>[^\n]*)\n(?P<code>.*?)\n```\s*\n"
    r"\*\*Why this matters:\*\*\s*(?P<why>.+?)\s*\n"
    r"\*\*Review focus:\*\*\s*(?P<focus>.+?)(?=\n###\s+`|\n<!-- gearbox-critical-code:end -->|\Z)",
    re.DOTALL,
)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip("\n").splitlines()).strip()


def validate(report: Path, repo_root: Path, require_code: bool, max_snippets: int, max_lines: int, max_total_lines: int) -> int:
    text = report.read_text(encoding="utf-8")
    if "<!-- gearbox-report:v1 -->" not in text:
        fail("missing Gearbox report marker")

    if START not in text or END not in text:
        if require_code:
            fail("critical-code block is required for a PR with substantive code/config changes")
        if NONE not in text:
            fail("report must include either a critical-code block or the explicit no-critical-code marker")
        print("PASS: no critical product code declared")
        return 0

    if text.index(START) > text.index(END):
        fail("critical-code markers are reversed")
    block = text.split(START, 1)[1].split(END, 1)[0]
    entries = list(ENTRY_RE.finditer(block))
    if not entries:
        fail("critical-code block contains no valid source-backed excerpts")
    if len(entries) > max_snippets:
        fail(f"too many critical snippets: {len(entries)} > {max_snippets}")

    total_lines = 0
    seen: set[tuple[str, int, int]] = set()
    root = repo_root.resolve()
    for m in entries:
        rel = m.group("path")
        start = int(m.group("start"))
        end = int(m.group("end"))
        if start < 1 or end < start:
            fail(f"invalid line range for {rel}: {start}-{end}")
        line_count = end - start + 1
        if line_count > max_lines:
            fail(f"critical snippet too long for {rel}: {line_count} lines > {max_lines}")
        total_lines += line_count
        if total_lines > max_total_lines:
            fail(f"critical snippets exceed total line budget: {total_lines} > {max_total_lines}")
        key = (rel, start, end)
        if key in seen:
            fail(f"duplicate critical snippet: {rel}:{start}-{end}")
        seen.add(key)

        path = (root / rel).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            fail(f"critical snippet path escapes repository: {rel}")
        if not path.exists() or not path.is_file():
            fail(f"critical snippet source does not exist: {rel}")
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        if end > len(lines):
            fail(f"critical snippet range exceeds {rel}: file has {len(lines)} lines")
        actual = "\n".join(lines[start - 1:end])
        quoted = m.group("code")
        if normalize(actual) != normalize(quoted):
            fail(f"excerpt does not exactly match {rel}:{start}-{end}")
        if len(m.group("why").strip()) < 12:
            fail(f"missing meaningful 'Why this matters' for {rel}:{start}-{end}")
        if len(m.group("focus").strip()) < 8:
            fail(f"missing meaningful 'Review focus' for {rel}:{start}-{end}")

    print(f"PASS: {len(entries)} source-backed critical code excerpt(s), {total_lines} total lines")
    return 0


def self_test() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        (root / "src" / "app.ts").write_text("const a = 1;\nconst b = 2;\nexport const c = a + b;\n", encoding="utf-8")
        good = root / "good.md"
        good.write_text(
            "<!-- gearbox-report:v1 -->\n"
            "## Critical logic to inspect\n"
            f"{START}\n"
            "### `src/app.ts:2-3`\n"
            "```ts\nconst b = 2;\nexport const c = a + b;\n```\n"
            "**Why this matters:** This computes the exported behavior used by callers.\n"
            "**Review focus:** Confirm the exported value remains correct.\n"
            f"{END}\n",
            encoding="utf-8",
        )
        validate(good, root, True, 5, 30, 120)
        bad = root / "bad.md"
        bad.write_text("<!-- gearbox-report:v1 -->\n## Critical logic to inspect\n- src/app.ts changed\n", encoding="utf-8")
        try:
            validate(bad, root, True, 5, 30, 120)
        except SystemExit as exc:
            if exc.code != 1:
                raise
        else:
            fail("self-test expected prose-only report to fail")
    print("PASS: pr-report-guard self-test")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Gearbox PR technical reports contain source-backed critical code excerpts.")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--require-code", action="store_true")
    ap.add_argument("--max-snippets", type=int, default=5)
    ap.add_argument("--max-lines", type=int, default=30)
    ap.add_argument("--max-total-lines", type=int, default=120)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.report:
        ap.error("--report is required unless --self-test is used")
    return validate(args.report, args.repo_root, args.require_code, args.max_snippets, args.max_lines, args.max_total_lines)


if __name__ == "__main__":
    raise SystemExit(main())
