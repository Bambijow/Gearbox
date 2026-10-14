#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

RISKS={"low","medium","high","critical"}
VISIBILITY={"loud-local","mixed","silent"}
TASK_GATES={"passed","not-applicable","failed"}
COVERAGE={"complete","gaps","blocked","not-provided","not-applicable"}
QUALITY={"pass","repair","blocked","not-provided","not-applicable"}

@dataclass
class FinalReviewRoute:
    mode:str
    fresh_reviewers:int
    comprehensive_reviewer:bool
    cross_provider_peer:bool
    verifier_required:bool
    rationale:list[str]
    review_focus:list[str]

def route(args:argparse.Namespace)->FinalReviewRoute:
    missing=args.coverage_status=="not-provided" or args.quality_aggregate=="not-provided"
    if missing and not getattr(args,"legacy_incomplete_evidence",False):
        raise ValueError("coverage and quality evidence must be supplied; absence is not non-applicability")
    for key in ("coverage_status","quality_aggregate"):
        if getattr(args,key)=="not-applicable" and not (getattr(args,"evidence_not_applicable_reason",None) or "").strip():
            raise ValueError("not-applicable evidence requires --evidence-not-applicable-reason")
    if args.task_review_gates=="failed":
        raise ValueError("required task review gate is failed; final review cannot substitute for it")
    if args.quality_aggregate in {"repair","blocked"}:
        raise ValueError(f"compiled quality aggregate is {args.quality_aggregate}; final review cannot substitute for failed/missing gates")
    if args.coverage_status=="blocked":
        raise ValueError("coverage matrix contains blocked proof; repair/adjudicate before final review")

    uncovered=list(dict.fromkeys(args.uncovered_failure_mode or []))
    full=[]
    if args.risk=="critical":full.append("critical risk")
    flags=[
        (args.auth_permissions,"auth/permissions boundary"),
        (args.billing_money,"money/billing boundary"),
        (args.secrets_crypto,"secrets/cryptography boundary"),
        (args.destructive_migration,"destructive migration"),
        (args.persistence_data,"persistence/data-integrity invariant"),
        (args.public_contract,"public/external contract"),
        (args.production_config,"production configuration/rollout control"),
        (args.concurrency,"concurrency/coordination invariant"),
        (args.architecture_change,"material architecture/shared-interface redesign"),
    ]
    for enabled,label in flags:
        if enabled:full.append(label)
    if args.exec_lines is not None and args.exec_lines>=args.full_exec_line_min:
        full.append(f"executable non-test change {args.exec_lines} >= full floor {args.full_exec_line_min}")

    if full:
        return FinalReviewRoute(
            mode="full",fresh_reviewers=2 if args.hybrid else 1,comprehensive_reviewer=True,
            cross_provider_peer=bool(args.hybrid),verifier_required=True,rationale=full,
            review_focus=uncovered or ["comprehensive integration consequence review"],
        )

    focused=[]
    if missing:focused.append("legacy missing evidence requires focused review; it is not completion proof")
    if args.risk=="high":focused.append("high risk without a full-review boundary")
    if args.failure_visibility=="silent":focused.append("plausible failure is silent")
    elif args.failure_visibility=="mixed":focused.append("failure visibility is mixed")
    if args.shared_seam:focused.append("integrated diff changes a shared seam")
    if args.integration_repair:focused.append("integration repair changed the final risk surface")
    if args.coverage_status=="gaps":focused.append("coverage matrix has proof gaps")
    if uncovered:focused.append("uncovered failure modes remain")

    if focused:
        return FinalReviewRoute(
            mode="focused",fresh_reviewers=1,comprehensive_reviewer=False,cross_provider_peer=False,
            verifier_required=True,rationale=focused,
            review_focus=uncovered or ["attack the silent/shared integration gap only"],
        )

    if args.failure_visibility!="loud-local":
        raise ValueError("lite requires loud-local failure visibility")
    return FinalReviewRoute(
        mode="lite",fresh_reviewers=0,comprehensive_reviewer=False,cross_provider_peer=False,
        verifier_required=True,
        rationale=[
            "required task review gates are complete",f"{args.risk} risk","failure is loud and local",
            "compiled quality gates are passing or not separately required",
            "coverage matrix has no unresolved proof gap" if args.coverage_status=="complete" else "no coverage gap was supplied",
            "no high-consequence boundary forces a deeper final review",
        ],
        review_focus=[],
    )

def parser()->argparse.ArgumentParser:
    p=argparse.ArgumentParser(description="Route Gearbox final integrated review by consequence and uncovered proof gaps.")
    p.add_argument("--risk",choices=sorted(RISKS));p.add_argument("--failure-visibility",choices=sorted(VISIBILITY));p.add_argument("--task-review-gates",choices=sorted(TASK_GATES))
    p.add_argument("--coverage-status",choices=sorted(COVERAGE),default="not-provided")
    p.add_argument("--quality-aggregate",choices=sorted(QUALITY),default="not-provided")
    p.add_argument("--uncovered-failure-mode",action="append",default=[])
    p.add_argument("--legacy-incomplete-evidence",action="store_true",help="Compatibility only: missing evidence forces at least focused review, never completion.")
    p.add_argument("--evidence-not-applicable-reason")
    p.add_argument("--hybrid",action="store_true");p.add_argument("--shared-seam",action="store_true");p.add_argument("--integration-repair",action="store_true")
    p.add_argument("--auth-permissions",action="store_true");p.add_argument("--billing-money",action="store_true");p.add_argument("--secrets-crypto",action="store_true");p.add_argument("--destructive-migration",action="store_true");p.add_argument("--persistence-data",action="store_true");p.add_argument("--public-contract",action="store_true");p.add_argument("--production-config",action="store_true");p.add_argument("--concurrency",action="store_true");p.add_argument("--architecture-change",action="store_true")
    p.add_argument("--exec-lines",type=int);p.add_argument("--full-exec-line-min",type=int,default=200);p.add_argument("--json",action="store_true");p.add_argument("--self-test",action="store_true")
    return p

def self_test():
    p=parser()
    defaults=["--coverage-status","complete","--quality-aggregate","pass"]
    cases=[
        (["--risk","low","--failure-visibility","loud-local","--task-review-gates","passed","--coverage-status","complete","--quality-aggregate","pass"],"lite",0),
        (["--risk","medium","--failure-visibility","silent","--task-review-gates","passed"],"focused",1),
        (["--risk","low","--failure-visibility","loud-local","--task-review-gates","passed","--coverage-status","gaps","--uncovered-failure-mode","retry duplication"],"focused",1),
        (["--risk","medium","--failure-visibility","loud-local","--task-review-gates","passed","--public-contract"],"full",1),
        (["--risk","critical","--failure-visibility","silent","--task-review-gates","passed","--hybrid"],"full",2),
    ]
    for argv,mode,n in cases:
        result=route(p.parse_args(defaults+argv));assert result.mode==mode,(argv,asdict(result));assert result.fresh_reviewers==n
    focus=route(p.parse_args(defaults+["--risk","low","--failure-visibility","loud-local","--task-review-gates","passed","--coverage-status","gaps","--uncovered-failure-mode","x"]))
    assert focus.review_focus==["x"]
    for bad in [
        ["--risk","low","--failure-visibility","loud-local","--task-review-gates","failed"],
        ["--risk","low","--failure-visibility","loud-local","--task-review-gates","passed","--quality-aggregate","repair"],
        ["--risk","low","--failure-visibility","loud-local","--task-review-gates","passed","--coverage-status","blocked"],
    ]:
        try:route(p.parse_args(defaults+bad));raise AssertionError("invalid precondition should fail")
        except ValueError:pass
    print("PASS: final-review-router")

def main():
    p=parser();args=p.parse_args()
    if args.self_test:self_test();return 0
    missing=[name for name in ("risk","failure_visibility","task_review_gates") if getattr(args,name) is None]
    if missing:p.error("required arguments missing: "+", ".join("--"+x.replace("_","-") for x in missing))
    try:result=route(args)
    except ValueError as exc:
        print(json.dumps({"ok":False,"reason":str(exc)},indent=2));return 5
    payload={"ok":True,**asdict(result)}
    if args.json:print(json.dumps(payload,indent=2))
    else:print(f"{result.mode}: reviewers={result.fresh_reviewers} :: "+"; ".join(result.rationale))
    return 0

if __name__=="__main__":
    raise SystemExit(main())