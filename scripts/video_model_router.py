#!/usr/bin/env python3
"""Deterministic, capability-first fal.ai video model selector. No network calls."""
import argparse
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "orchestration-registry.json"
def select(*, complexity="simple", duration=5, resolution="720p", first_last=False, multi_shot=False, max_usd=1.5, has_image=False):
    if not has_image:
        return {"blocked": True, "blocker": "IMAGE_REFERENCE_REQUIRED", "predecessor_task_kind": "asset-image"}
    catalog = json.loads(CATALOG.read_text())["video_models"]
    candidates = []
    for m in catalog["models"]:
        if duration not in m["durations"] or resolution not in m["resolutions"]:
            continue
        features = set(m["features"])
        if first_last and "first_last_frame" not in features: continue
        if multi_shot and "multi_shot" not in features: continue
        if complexity == "cinematic" and "cinematic" not in features: continue
        if complexity == "standard" and m["tier"] == "simple": continue
        rate = m.get("usd_per_second_by_resolution", {}).get(resolution, m.get("usd_per_second"))
        if rate is None: continue
        price = round(rate * duration, 4)
        candidates.append((price, m))
    if not candidates:
        return {"blocked": True, "blocker": "NO_CAPABLE_VIDEO_MODEL", "required_features": {"complexity": complexity, "first_last": first_last, "multi_shot": multi_shot}}
    price, chosen = min(candidates, key=lambda item: (item[0], item[1]["id"]))
    if price > max_usd:
        return {"blocked": True, "blocker": "VIDEO_BUDGET_EXCEEDED", "cheapest_capable_model": chosen["id"], "estimated_usd": price, "budget_usd": max_usd}
    return {"blocked": False, "model": chosen["id"], "estimated_usd": price, "budget_usd": max_usd, "requires_live_pricing_confirmation": True, "requires_spend_approval": True, "rationale": "lowest catalog estimate among candidates satisfying required capabilities", "pricing_verified_at": catalog["pricing_verified_at"], "input_image_field": chosen["input_image_field"]}
def self_test():
    assert select()["blocker"] == "IMAGE_REFERENCE_REQUIRED"
    assert select(has_image=True)["model"].endswith("v2.5-turbo/pro/image-to-video")
    assert select(has_image=True, complexity="standard")["model"] == "wan/v2.6/image-to-video"
    assert select(has_image=True, multi_shot=True)["model"] == "wan/v2.6/image-to-video"
    assert select(has_image=True, complexity="cinematic", duration=8, first_last=True, max_usd=4)["model"].endswith("first-last-frame-to-video")
    assert select(has_image=True, complexity="cinematic", duration=8, first_last=True, max_usd=1)["blocker"] == "VIDEO_BUDGET_EXCEEDED"
    print("PASS: video model router")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--complexity", choices=["simple","standard","cinematic"], default="simple")
    p.add_argument("--duration",type=int,default=5)
    p.add_argument("--resolution",choices=["720p","1080p"],default="720p")
    p.add_argument("--first-last",action="store_true")
    p.add_argument("--multi-shot",action="store_true")
    p.add_argument("--max-usd",type=float,default=1.5)
    p.add_argument("--has-image",action="store_true")
    a=p.parse_args()
    if a.self_test: self_test();return 0
    r=select(complexity=a.complexity,duration=a.duration,resolution=a.resolution,first_last=a.first_last,multi_shot=a.multi_shot,max_usd=a.max_usd,has_image=a.has_image)
    print(json.dumps(r,indent=2))
    return 7 if r["blocked"] else 0
if __name__=="__main__":
    raise SystemExit(main())
