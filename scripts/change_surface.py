#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import PurePosixPath

CODE_EXTS={".py",".js",".jsx",".ts",".tsx",".vue",".svelte",".go",".rs",".rb",".php",".java",".kt",".swift",".cs",".cpp",".c",".h"}
UI_EXTS={".jsx",".tsx",".vue",".svelte",".css",".scss",".sass",".less",".html"}
IMAGE_EXTS={".png",".jpg",".jpeg",".webp",".gif",".svg",".avif"}
THREED_EXTS={".blend",".gltf",".glb",".fbx",".obj",".dae",".usd",".usdz"}
AUDIO_EXTS={".wav",".mp3",".ogg",".flac",".m4a",".aac"}
LEVEL_EXTS={".tscn",".scn",".tmx",".map"}

def _parts(path:str)->set[str]:
    return {p.casefold() for p in PurePosixPath(path.replace("\\","/")).parts}

def classify_path(path:str)->set[str]:
    p=path.replace("\\","/")
    low=p.casefold()
    parts=_parts(p)
    ext=PurePosixPath(low).suffix
    out:set[str]=set()

    if any(x in parts for x in {"test","tests","spec","specs","__tests__"}) or any(x in low for x in (".test.",".spec.")):
        out.add("tests")
    if any(x in parts for x in {"docs","documentation"}) or ext in {".md",".mdx",".rst"}:
        out.add("docs")

    if ext in UI_EXTS or any(x in parts for x in {"ui","views","pages","screens","components","frontend","web"}):
        out.add("user_ui")
    if any(x in low for x in ("button","dialog","modal","menu","popover","drawer","tabs","form","combobox","select","tooltip","toast","accordion","command-palette")):
        out.update({"user_ui","interactive_ui"})
    if ext in UI_EXTS and any(x in parts for x in {"components","ui"}):
        out.add("interactive_ui")

    if any(x in low for x in ("design-system","design_system","tokens","theme","theming","primitives")) or (
        "components" in parts and any(x in parts for x in {"ui","shared","common"})
    ):
        out.update({"user_ui","shared_design_system"})

    if any(x in parts for x in {"locales","locale","i18n","translations","messages"}) or any(x in low for x in ("copy.","content.","strings.")):
        out.add("ux_copy")

    if ext in IMAGE_EXTS:
        out.add("visual_asset")
    if ext in THREED_EXTS:
        out.add("asset_3d")
    if ext in AUDIO_EXTS or any(x in parts for x in {"audio","sound","sounds","sfx","music"}):
        out.add("audio")
    if ext in LEVEL_EXTS and any(x in parts for x in {"levels","level","maps","map","scenes","worlds"}):
        out.add("level")
    if any(x in parts for x in {"levels","level","encounters","maps","worlds"}):
        out.add("level")

    if any(x in low for x in ("webgl","three.","threejs","shader","glsl","canvas","pixi","ogl","babylon")) or ext in {".glsl",".vert",".frag",".wgsl"}:
        out.update({"creative_runtime","performance_sensitive","user_ui"})
    if any(x in low for x in ("performance","perf.","profil","benchmark")):
        out.add("performance_sensitive")

    if any(x in parts for x in {"migrations","migration","db","database"}) or ext==".sql" or any(x in low for x in ("schema.prisma","drizzle","sequelize","typeorm")):
        out.add("persistence")
    if any(x in low for x in ("auth","permission","role","rbac","oauth","secret","crypto","credential","session")):
        out.add("security_boundary")
    if any(x in low for x in ("openapi","swagger","graphql","public-api","public_api")) or "api" in parts:
        out.add("public_api")
    if any(x in parts for x in {"terraform","k8s","kubernetes","deploy","deployment","helm","infra","infrastructure"}) or any(x in low for x in ("dockerfile",".github/workflows")):
        out.add("production_config")
    if any(x in low for x in ("observability","telemetry","metrics","tracing","logging","opentelemetry")):
        out.add("observability")

    if ext in CODE_EXTS and not out.intersection({"tests","docs"}):
        out.add("runtime_behavior")
    return out

def classify(paths:list[str],hints:list[str])->dict:
    surfaces:set[str]=set()
    by_path={}
    for path in paths:
        found=classify_path(path)
        by_path[path]=sorted(found)
        surfaces.update(found)
    for hint in hints:
        h=hint.strip().casefold().replace("-","_")
        if h:
            surfaces.add(h)
    asset_families=surfaces.intersection({"visual_asset","asset_3d","audio"})
    if len(asset_families)>=2:
        surfaces.add("multi_asset")
    if "creative_runtime" in surfaces:
        surfaces.update({"user_ui","interactive_ui","performance_sensitive"})
    return {"schema_version":1,"paths":by_path,"surfaces":sorted(surfaces)}

def self_test()->None:
    r=classify(["src/components/ui/Button.tsx","src/theme/tokens.css"],[])
    assert {"user_ui","interactive_ui","shared_design_system"}.issubset(set(r["surfaces"]))
    r=classify(["web/hero.frag","web/scene.ts"],[])
    assert {"creative_runtime","performance_sensitive","user_ui"}.issubset(set(r["surfaces"]))
    r=classify(["game/levels/arena.tscn","assets/sfx/hit.ogg"],[])
    assert "level" in r["surfaces"] and "audio" in r["surfaces"]
    r=classify(["db/migrations/001.sql","src/auth/session.ts"],[])
    assert {"persistence","security_boundary"}.issubset(set(r["surfaces"]))
    print("PASS: change-surface self-test")

def main()->int:
    ap=argparse.ArgumentParser(description="Classify changed/owned paths into Gearbox consequence surfaces.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--path",action="append",default=[])
    ap.add_argument("--hint",action="append",default=[])
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    print(json.dumps(classify(args.path,args.hint),indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
