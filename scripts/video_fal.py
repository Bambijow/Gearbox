#!/usr/bin/env python3
"""fal.ai paid image-to-video execution. Offline dry run by default."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from video_model_router import select

def source_image(value: str) -> str:
    if not value: raise ValueError("IMAGE_REFERENCE_REQUIRED")
    u = urlparse(value)
    if u.scheme == "https" and u.netloc and not u.username and not u.password:
        return value
    if u.scheme: raise ValueError("Only HTTPS reference URLs or existing image files allowed")
    p = Path(value).expanduser().resolve()
    if not p.is_file() or p.suffix.lower() not in {".png",".jpg",".jpeg",".bmp",".webp"}:
        raise ValueError("IMAGE_REFERENCE_REQUIRED: supported local image file not found")
    return str(p)

def main() -> int:
    ap=argparse.ArgumentParser(description="Guarded fal.ai image-to-video generator")
    ap.add_argument("--image",required=True)
    ap.add_argument("--end-image")
    ap.add_argument("--prompt",required=True)
    ap.add_argument("--complexity",choices=("simple","standard","cinematic"),default="simple")
    ap.add_argument("--duration",type=int,default=5)
    ap.add_argument("--resolution",choices=("720p","1080p"),default="720p")
    ap.add_argument("--multi-shot",action="store_true")
    ap.add_argument("--max-usd",type=float,default=1.5)
    ap.add_argument("--apply",action="store_true")
    ap.add_argument("--approve-spend",action="store_true")
    ap.add_argument("--live-price-confirmed",action="store_true")
    args=ap.parse_args()
    try:
        start=source_image(args.image)
        end=source_image(args.end_image) if args.end_image else None
    except ValueError as exc:
        print(json.dumps({"blocked":True,"reason":str(exc)}));return 7
    choice=select(complexity=args.complexity,duration=args.duration,resolution=args.resolution,first_last=bool(end),multi_shot=args.multi_shot,max_usd=args.max_usd,has_image=True)
    if choice["blocked"]:
        print(json.dumps(choice));return 7
    print(json.dumps({"selected_model":choice["model"],"estimated_usd":choice["estimated_usd"],"budget_usd":args.max_usd,"image_reference_present":True,"dry_run":not args.apply}))
    if not args.apply:return 0
    if not args.approve_spend or not args.live_price_confirmed:
        print("BLOCKED: spend approval and live price confirmation required");return 7
    if not os.environ.get("FAL_KEY"):
        print("BLOCKED: missing FAL_KEY");return 7
    try:
        import fal_client
    except ImportError:
        print("BLOCKED: install fal-client explicitly in the execution environment");return 7
    if not start.startswith("https://"):start=fal_client.upload_file(start)
    if end and not end.startswith("https://"):end=fal_client.upload_file(end)
    payload={"prompt":args.prompt,"resolution":args.resolution,"duration":str(args.duration)}
    model=choice["model"]
    if model.endswith("first-last-frame-to-video"):
        payload.update({"first_frame_url":start,"last_frame_url":end})
    else:
        payload["image_url"]=start
        if model=="wan/v2.6/image-to-video":payload["multi_shots"]=args.multi_shot
    # No automatic retries: a timeout may represent an already billable job.
    try:
        result=fal_client.subscribe(model,arguments=payload,with_logs=False)
    except Exception:
        print("fal.ai request failed or status unknown; inspect provider dashboard before retrying")
        return 7
    video=result.get("video",{}) if isinstance(result,dict) else {}
    print(json.dumps({"model":model,"video_url":video.get("url"),"request_id":result.get("request_id") if isinstance(result,dict) else None,"requires_playback_review":True}))
    return 0 if video.get("url") else 7
if __name__=="__main__":raise SystemExit(main())
