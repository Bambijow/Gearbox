#!/usr/bin/env python3
"""Offline evidence check for independently killed critical guard mutants."""
import argparse
import json
from pathlib import Path

def check(data):
    if data.get("schema_version") != 1 or not isinstance(data.get("guards"), list) or not data["guards"]:
        raise ValueError("expected nonempty guards and schema_version=1")
    seen = set()
    for item in data["guards"]:
        if not isinstance(item, dict):
            raise ValueError("guard entry must be an object")
        name = item.get("guard")
        if not isinstance(name, str) or not name or name in seen:
            raise ValueError("guard names must be nonempty and unique")
        seen.add(name)
        for field in ("mutation_diff", "test_command", "failure_evidence"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"{name}: missing {field}")
        if item.get("mutation_applied") is not True or item.get("baseline_green") is not True:
            raise ValueError(f"{name}: mutation not confirmed or baseline not green")
        if item.get("mutation_killed") is not True or item.get("failure_is_intended") is not True:
            raise ValueError(f"{name}: guard not independently proven")
        if item.get("mutated_guards") != [name]:
            raise ValueError(f"{name}: mutation must target only that guard")
    expected = data.get("expected_guards")
    if not isinstance(expected, list) or not expected or len(set(expected)) != len(expected) or set(expected) != seen:
        raise ValueError("expected_guards must exactly match tested guards")
    return len(seen)

def self_test():
    entry = dict(guard="auth", mutated_guards=["auth"], mutation_diff="diff.patch",
                 baseline_green=True, mutation_applied=True, mutation_killed=True,
                 failure_is_intended=True, test_command="pytest test_auth.py",
                 failure_evidence="auth-red.txt")
    good = dict(schema_version=1, expected_guards=["auth"], guards=[entry])
    assert check(good) == 1
    for bad in (dict(good, expected_guards=["auth", "owner"]),
                dict(good, guards=[dict(entry, mutation_killed=False)]),
                dict(good, guards=[dict(entry, mutated_guards=["auth", "owner"])])):
        try: check(bad)
        except ValueError: pass
        else: raise AssertionError("invalid proof accepted")
    print("PASS: guard-mutation-proof self-test")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.report is None:
        parser.error("--report required")
    try:
        count = check(json.loads(args.report.read_text(encoding="utf-8")))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"PASS: independently killed {count} guard(s); inspect raw evidence before accepting")

if __name__ == "__main__":
    main()
