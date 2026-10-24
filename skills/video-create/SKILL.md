---
name: video-create
description: "Create marketing and premium web hero videos from approved source images through fal.ai with budget-aware model routing; generates source art first when missing."
argument-hint: "[brief] [--image reference] [--hero] [--apply]"
disable-model-invocation: true
---

# Image-first video

Read `references/video-production.md`. Use the registered `video-producer` and `scripts/route_task.py --task-kind video-create`.

A real, inspected, rights-cleared reference image is mandatory. If missing, dispatch `asset-image` as a predecessor through its registered Codex Sol route, verify and persist the image output, then resume. Never call fal with a nonexistent reference or silently use text-to-video.

Classify shot requirements, then invoke `scripts/video_model_router.py`. Select the cheapest capable model, not the cheapest overall or the highest-cost by default. Enforce the user budget, verify live prices and API schema, and require explicit spend approval before any paid request. Missing FAL_KEY blocks execution.

Without `--apply`, deliver a storyboard, reference plan, model/cost estimate, and acceptance criteria. With `--apply`, call the guarded fal adapter after approval; verify the actual generated video before PASS. Hero deliverables include compressed web file, poster image, muted inline playback plan, responsive crop, accessible reduced-motion fallback and measured performance.
