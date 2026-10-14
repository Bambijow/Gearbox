#!/usr/bin/env python3
"""Deterministic risk/uncertainty routing and discriminating-probe selection.

Uses author-supplied hypotheses/predictions, not invented probabilities or safety downgrades.
"""
from __future__ import annotations
import argparse
import json

RISK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
UNCERTAINTY = {"known", "partial", "high", "blocked"}


def compile_plan(data):
    if not isinstance(data, dict):
        raise ValueError("input must be an object")
    risk, uncertainty = data.get("risk"), data.get("uncertainty")
    if risk not in RISK or uncertainty not in UNCERTAINTY:
        raise ValueError("risk and uncertainty must be explicit valid enums")
    questions = data.get("blocking_product_questions", [])
    if not isinstance(questions, list) or not all(isinstance(x, str) and x.strip() for x in questions):
        raise ValueError("invalid blocking_product_questions")
    hypotheses = data.get("hypotheses", [])
    if not isinstance(hypotheses, list) or not all(isinstance(x, str) and x.strip() for x in hypotheses) or len(set(hypotheses)) != len(hypotheses):
        raise ValueError("hypotheses must be unique ids")
    probes = data.get("probes", [])
    if not isinstance(probes, list):
        raise ValueError("probes must be a list")
    selected = []
    for probe in probes:
        if not isinstance(probe, dict) or not isinstance(probe.get("id"), str) or not probe["id"].strip():
            raise ValueError("probe id required")
        cost = probe.get("cost")
        if type(cost) is not int or cost < 1 or cost > 100:
            raise ValueError("probe cost must be an integer 1..100")
        predictions = probe.get("predictions")
        if not isinstance(predictions, dict) or set(predictions) != set(hypotheses):
            raise ValueError("every probe must provide a predicted observable result for each hypothesis")
        if not all(isinstance(x, str) and x.strip() for x in predictions.values()):
            raise ValueError("predicted results must be non-empty")
        partitions = len(set(predictions.values()))
        selected.append({"id": probe["id"], "cost": cost, "outcome_partitions": partitions,
                         "distinguishing_power": partitions - 1,
                         "note": "Prediction signatures are hypotheses, not observed results"})
    if len({p["id"] for p in selected}) != len(selected):
        raise ValueError("duplicate probe id")
    # Greedy budget: no experiment when nothing can be distinguished or uncertainty resolved.
    budget = data.get("probe_budget", 0)
    if type(budget) is not int or budget < 0:
        raise ValueError("probe_budget must be non-negative")
    ranking = sorted((p for p in selected if p["distinguishing_power"] > 0),
                     key=lambda p: (-p["distinguishing_power"] / p["cost"], p["cost"], p["id"]))
    chosen = []
    left = budget
    if uncertainty in {"partial", "high"} and not questions:
        for probe in ranking:
            if probe["cost"] <= left:
                chosen.append(probe["id"])
                left -= probe["cost"]
                # One most discriminating experiment at a time; update hypotheses before more.
                break
    route = ("HUMAN_BLOCKED" if questions or uncertainty == "blocked" else
             "INVESTIGATE" if uncertainty in {"partial", "high"} and chosen else
             "EVIDENCE_BLOCKED" if uncertainty in {"partial", "high"} else "PLAN")
    return {"route": route, "risk": risk, "uncertainty": uncertainty,
            "selected_probe_ids": chosen, "probe_candidates": ranking,
            "human_questions": questions, "required_quality_floor": "critical" if risk == "critical" else "high" if risk == "high" else "standard",
            "remaining_budget": left,
            "note": "Risk gates never decrease because uncertainty is resolved. No probes executed; authorization is separate."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True)
    args = p.parse_args()
    try:
        with open(args.input, encoding="utf-8") as f:
            result = compile_plan(json.load(f))
    except (OSError, ValueError) as error:
        p.error(str(error))
    print(json.dumps(result, indent=2))
    return 0 if result["route"] in {"PLAN", "INVESTIGATE"} else 6


if __name__ == "__main__":
    raise SystemExit(main())
