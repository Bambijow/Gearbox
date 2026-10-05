#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

RISKS={"low","medium","high","critical"}
VISIBILITY={"loud-local","mixed","silent"}
TASK_GATES={"passed","not-applicable","failed"}

@dataclass
class FinalReviewRoute:
    mode: str
    fresh_reviewers: int
    comprehensive_reviewer: bool
    cross_provider_peer: bool
    verifier_required: bool
    rationale: list[str]

def route(args: argparse.Namespace) -> FinalReviewRoute:
    if args.task_review_gates=="failed":
        raise ValueError("required task review gate is failed; final review cannot substitute for it")

    full=[]
    if args.risk=="critical": full.append("critical risk")
    flags=[
        ("auth_permissions",args.auth_permissions,"auth/permissions boundary"),
        ("billing_money",args.billing_money,"money/billing boundary"),
        ("secrets_crypto",args.secrets_crypto,"secrets/cryptography boundary"),
        ("destructive_migration",args.destructive_migration,"destructive migration"),
        ("persistence_data",args.persistence_data,"persistence/data-integrity invariant"),
        ("public_contract",args.public_contract,"public/external contract"),
        ("production_config",args.production_config,"production configuration/rollout control"),
        ("concurrency",args.concurrency,"concurrency/coordination invariant"),
        ("architecture_change",args.architecture_change,"material architecture/shared-interface redesign"),
    ]
    for _key,enabled,label in flags:
        if enabled: full.append(label)
    if args.exec_lines is not None and args.exec_lines >= args.full_exec_line_min:
        full.append(f"executable non-test change {args.exec_lines} >= full floor {args.full_exec_line_min}")

    if full:
        return FinalReviewRoute(
            mode="full",
            fresh_reviewers=2 if args.hybrid else 1,
            comprehensive_reviewer=True,
            cross_provider_peer=bool(args.hybrid),
            verifier_required=True,
            rationale=full,
        )

    focused=[]
    if args.risk=="high": focused.append("high risk without a full-review boundary")
    if args.failure_visibility=="silent": focused.append("plausible failure is silent")
    elif args.failure_visibility=="mixed": focused.append("failure visibility is mixed")
    if args.shared_seam: focused.append("integrated diff changes a shared seam")
    if args.integration_repair: focused.append("integration repair changed the final risk surface")

    if focused:
        return FinalReviewRoute(
            mode="focused",
            fresh_reviewers=1,
            comprehensive_reviewer=False,
            cross_provider_peer=False,
            verifier_required=True,
            rationale=focused,
        )

    if args.failure_visibility!="loud-local":
        raise ValueError("lite requires loud-local failure visibility")
    return FinalReviewRoute(
        mode="lite",
        fresh_reviewers=0,
        comprehensive_reviewer=False,
        cross_provider_peer=False,
        verifier_required=True,
        rationale=[
            "required task review gates are complete",
            f"{args.risk} risk",
            "failure is loud and local",
            "no high-consequence boundary forces a deeper final review",
        ],
    )

def parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(description="Route Gearbox final integrated review by failure consequence.")
    p.add_argument("--risk",choices=sorted(RISKS))
    p.add_argument("--failure-visibility",choices=sorted(VISIBILITY))
    p.add_argument("--task-review-gates",choices=sorted(TASK_GATES))
    p.add_argument("--hybrid",action="store_true")
    p.add_argument("--shared-seam",action="store_true")
    p.add_argument("--integration-repair",action="store_true")
    p.add_argument("--auth-permissions",action="store_true")
    p.add_argument("--billing-money",action="store_true")
    p.add_argument("--secrets-crypto",action="store_true")
    p.add_argument("--destructive-migration",action="store_true")
    p.add_argument("--persistence-data",action="store_true")
    p.add_argument("--public-contract",action="store_true")
    p.add_argument("--production-config",action="store_true")
    p.add_argument("--concurrency",action="store_true")
    p.add_argument("--architecture-change",action="store_true")
    p.add_argument("--exec-lines",type=int)
    p.add_argument("--full-exec-line-min",type=int,default=200)
    p.add_argument("--json",action="store_true")
    p.add_argument("--self-test",action="store_true")
    return p

def self_test() -> None:
    p=parser()
    cases=[
        (["--risk","low","--failure-visibility","loud-local","--task-review-gates","passed"],"lite",0),
        (["--risk","medium","--failure-visibility","silent","--task-review-gates","passed"],"focused",1),
        (["--risk","high","--failure-visibility","loud-local","--task-review-gates","passed"],"focused",1),
        (["--risk","medium","--failure-visibility","loud-local","--task-review-gates","passed","--public-contract"],"full",1),
        (["--risk","medium","--failure-visibility","loud-local","--task-review-gates","passed","--exec-lines","250","--hybrid"],"full",2),
        (["--risk","critical","--failure-visibility","silent","--task-review-gates","passed","--hybrid"],"full",2),
    ]
    for argv,mode,n in cases:
        result=route(p.parse_args(argv))
        assert result.mode==mode,(argv,asdict(result))
        assert result.fresh_reviewers==n,(argv,asdict(result))
    try:
        route(p.parse_args(["--risk","low","--failure-visibility","loud-local","--task-review-gates","failed"]))
    except ValueError:
        pass
    else:
        raise AssertionError("failed task review gate must reject final routing")
    print("PASS: final-review-router")

def main() -> int:
    p=parser()
    args=p.parse_args()
    if args.self_test:
        self_test(); return 0
    missing=[name for name in ("risk","failure_visibility","task_review_gates") if getattr(args,name) is None]
    if missing:
        p.error("required arguments missing: " + ", ".join("--"+x.replace("_","-") for x in missing))
    try:
        result=route(args)
    except ValueError as exc:
        print(json.dumps({"ok":False,"reason":str(exc)},indent=2))
        return 5
    payload={"ok":True,**asdict(result)}
    if args.json:
        print(json.dumps(payload,indent=2))
    else:
        print(f"{result.mode}: reviewers={result.fresh_reviewers} :: " + "; ".join(result.rationale))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
