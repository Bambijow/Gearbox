#!/usr/bin/env python3
"""Explicit Gemini/Claude routing; no legacy provider fallback."""
import argparse
import json

MODELS = {
    "economy": "gemini-4-hydrogen-low",
    "standard": "gemini-4-neon-medium",
    "deep": "gemini-4-neon-high",
    "frontier": "gemini-4-carbon-high",
}
CRITICAL = {"security", "auth", "concurrency", "persistence", "migration"}
CREATIVE = {"art-direction", "creative-direction"}
ARCHITECTURE = {"architecture", "domain-modeling", "architecture-decision", "architecture-review"}
THREE_D = {"model-3d", "review-3d", "motion-3d"}


def route(kind, risk="medium", complexity="medium", gemini=True, claude=True, capabilities=(), models=None):
    models = {**MODELS, **(models or {})}
    if kind in CREATIVE:
        provider, model, reviewer = "claude", "claude-opus-5-5", "gemini"
    elif kind in ARCHITECTURE:
        # Ordinary, reversible design stays on Neon. Critical/high-complexity
        # design uses Carbon with an independent Opus adversarial review.
        provider = "gemini"
        model = models["frontier"] if risk == "critical" or complexity == "high" else models["standard"]
        reviewer = "claude"
    elif kind in THREE_D:
        provider, model, reviewer = "gemini", models["frontier"], "gemini"
    elif kind in {"docs", "changelog", "metadata", "formatting", "simple-test"} and risk == "low":
        provider, model, reviewer = "gemini", models["economy"], None
    elif risk == "critical" or complexity == "high" or kind in CRITICAL:
        provider, model, reviewer = "gemini", models["deep"], "claude"
    else:
        provider, model, reviewer = "gemini", models["standard"], "claude"
    requires3d = kind in THREE_D
    blocked3d = requires3d and not ({"blender", "godot"} & set(capabilities))
    unavailable = not (gemini if provider == "gemini" else claude)
    unavailable_review = (reviewer == "gemini" and not gemini) or (reviewer == "claude" and not claude)
    blocked = unavailable or unavailable_review or blocked3d
    return {
        "task_kind": kind, "provider": provider, "model": model,
        "review_provider": reviewer, "review_model": model if reviewer == "gemini" and requires3d
            else (models["deep"] if reviewer == "gemini" else
                  "claude-opus-5-5" if reviewer == "claude" and
                  (kind in ARCHITECTURE and (risk == "critical" or complexity == "high"))
                  else "claude-sonnet-5-5" if reviewer else None),
        "independent_review": bool(reviewer), "status": "BLOCKED" if blocked else "READY",
        "blocker": "provider/reviewer missing" if unavailable or unavailable_review else
            "Gemini Blender/Godot capability required" if blocked3d else None,
        "policy": "No legacy provider and no silent provider fallback",
    }


def self_test():
    assert route("feature")["model"] == MODELS["standard"]
    assert route("docs", risk="low")["model"] == MODELS["economy"]
    assert route("architecture")["provider"] == "gemini"
    assert route("architecture")["model"] == MODELS["standard"]
    critical = route("architecture", risk="critical")
    assert critical["provider"] == "gemini" and critical["model"] == MODELS["frontier"]
    assert critical["review_provider"] == "claude" and critical["review_model"] == "claude-opus-5-5"
    assert critical["independent_review"] is True
    assert route("domain-modeling", complexity="high")["model"] == MODELS["frontier"]
    assert route("architecture", complexity="high", claude=False)["status"] == "BLOCKED"
    assert route("art-direction")["provider"] == "claude"
    assert route("architecture", models={"frontier": "my-carbon-id"}, risk="critical")["model"] == "my-carbon-id"
    assert route("feature", claude=False)["status"] == "BLOCKED"
    assert route("model-3d")["status"] == "BLOCKED"
    assert route("model-3d", capabilities=["blender"])["model"] == MODELS["frontier"]
    assert route("model-3d", capabilities=["godot"])["review_provider"] == "gemini"
    print("PASS: Gemini/Claude router self-test")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-kind", default="feature")
    ap.add_argument("--risk", choices=["low", "medium", "high", "critical"], default="medium")
    ap.add_argument("--complexity", choices=["low", "medium", "high"], default="medium")
    ap.add_argument("--no-gemini", action="store_true")
    ap.add_argument("--no-claude", action="store_true")
    ap.add_argument("--gemini-capability", action="append", default=[])
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    result = route(a.task_kind, a.risk, a.complexity, not a.no_gemini,
                   not a.no_claude, capabilities=a.gemini_capability)
    print(json.dumps(result, indent=2))
    if result["status"] != "READY":
        raise SystemExit(7)


if __name__ == "__main__":
    main()
