# Video production: image-first, capability-first and cost-aware

For marketing footage, premium website hero loops, cinematic product backgrounds. Use `video-create` rather than native UI/3D `motion-design`. Do not incur video inference charges merely because a web site is described as premium.

DAG: requested video → inspect licensed source still(s) → missing? `asset-image` through Codex Sol → approve source image → classify movement/subject/story → select cheapest capable fal model → verify current tariff and schema → explicit spend authorization → render → inspect playback → optimize and ship.

Image reference is a hard dependency. If absent and image generation fails, block `IMAGE_REFERENCE_REQUIRED`. Track asset provenance, user acceptance, actual image URI, generation settings, input revision, chosen model and fal request ID. Do not let video agent invent image references.

Model selection uses `scripts/video_model_router.py` and the declarative `video_models` catalog in `orchestration-registry.json`. Rules:
- Simple: single shot, gentle parallax/atmosphere. Economical models preferred.
- Standard: nontrivial movement, multiple shots, higher visual fidelity. Exclude basic tier.
- Cinematic: controlled first/end frames or premium cinematic direction. Require an endpoint that supports every needed feature.
- Filter by supported duration, resolution, frame control, multi-shot, audio, input modality and actual provider schema before comparing price.
- Among qualifying candidates, pick lowest projected bill for requested settings. Do not downgrade needed quality to fit budget: block and present choices.
- Cost numbers are snapshots, **not guaranteed live quotes**. Recheck provider pricing and the model's endpoint parameters before dispatch. Enforce approved USD ceiling; no automatic retries for ambiguous billable failures.

Provider: https://fal.ai/explore/image-to-video-apis . Secure API key only via `FAL_KEY` environment variable, never prompts or checked-in files. Dry-run by default. Do not mark paid rendering successful from a request ID alone.

For website hero, aim for restrained movement, a static poster, safe text area, mobile crop, muted autoplay/playsinline, reduced-motion static fallback, compressed delivery and real playback/performance checks. Marketing requires brand alignment, shot-level continuity and usage rights.
