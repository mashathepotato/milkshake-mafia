#!/usr/bin/env python3
"""Photographer CLI — python -m photographer <command> [options]"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path


def _make_request_id() -> str:
    return str(uuid.uuid4())[:8]


def _add_capture_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--url", required=True, help="URL to capture")
    parser.add_argument("--out", metavar="DIR", help="Write artifacts to this directory")
    parser.add_argument("--request-id", default=None, help="Request ID (auto-generated if omitted)")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--no-full-page", action="store_true")
    parser.add_argument("--wait-until", default="networkidle", choices=["load", "domcontentloaded", "networkidle"])
    parser.add_argument("--wait-ms", type=int, default=500)
    parser.add_argument(
        "--embedder",
        choices=["dinov2", "histogram"],
        default="dinov2",
        help="Which embedder to use; falls back to histogram if dinov2 unavailable",
    )


def cmd_capture(args: argparse.Namespace) -> None:
    from photographer.contracts import CaptureRequest, Viewport
    from photographer.capture import capture

    req = CaptureRequest(
        request_id=args.request_id or _make_request_id(),
        url=args.url,
        viewport=Viewport(width=args.width, height=args.height),
        full_page=not args.no_full_page,
        wait_until=args.wait_until,
        wait_ms=args.wait_ms,
    )

    out_dir = Path(args.out) if args.out else None
    screenshot = capture(req, out_dir=out_dir)
    data = screenshot.model_dump()

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        dest = out / f"{req.request_id}.screenshot.json"
        dest.write_text(json.dumps(data, indent=2))
        print(f"Wrote {dest}", file=sys.stderr)

    print(json.dumps(data, indent=2))


def cmd_embed(args: argparse.Namespace) -> None:
    from photographer.embed import load_embedder, embed_image
    from PIL import Image

    embedder, warnings = load_embedder(prefer=args.embedder)
    image = Image.open(args.image).convert("RGB")

    artifact = embed_image(
        image=image,
        embedder=embedder,
        request_id=args.request_id or _make_request_id(),
        url=f"file://{Path(args.image).resolve()}",
        source="png_path",
        extra_warnings=warnings,
    )
    print(json.dumps(artifact.model_dump(), indent=2))


def cmd_run(args: argparse.Namespace) -> None:
    from photographer.contracts import CaptureRequest, Viewport
    from photographer.embed import load_embedder
    from photographer.pipeline import process

    req = CaptureRequest(
        request_id=args.request_id or _make_request_id(),
        url=args.url,
        viewport=Viewport(width=args.width, height=args.height),
        full_page=not args.no_full_page,
        wait_until=args.wait_until,
        wait_ms=args.wait_ms,
    )

    embedder, warnings = load_embedder(prefer=args.embedder)
    for w in warnings:
        print(f"Warning: {w}", file=sys.stderr)

    out_dir = Path(args.out) if args.out else None
    screenshot, embedding = process(req, embedder=embedder, out_dir=out_dir)

    screenshot_data = screenshot.model_dump()
    embedding_data = embedding.model_dump()

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{req.request_id}.screenshot.json").write_text(json.dumps(screenshot_data, indent=2))
        # embedding.json already written by pipeline.process; just ensure screenshot json lands too
        print(f"Artifacts written to {out}/", file=sys.stderr)

    print(json.dumps({"screenshot": screenshot_data, "embedding": embedding_data}, indent=2))


def cmd_baseline_build(args: argparse.Namespace) -> None:
    from photographer.baseline import build
    from photographer.embed import load_embedder

    embedder, warnings = load_embedder(prefer=args.embedder)
    for w in warnings:
        print(f"Warning: {w}", file=sys.stderr)
    cellar_path = Path(args.cellar) if args.cellar else None
    out_dir = Path(args.out_dir) if args.out_dir else None
    build(
        baseline_id=args.baseline_id,
        embedder=embedder,
        cellar_path=cellar_path,
        out_dir=out_dir,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="photographer",
        description="Photographer: visual encoder tier (capture → embed)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # capture
    p_cap = sub.add_parser("capture", help="Capture a screenshot")
    _add_capture_args(p_cap)

    # embed
    p_emb = sub.add_parser("embed", help="Embed an image file")
    p_emb.add_argument("--image", required=True, help="Path to PNG file")
    p_emb.add_argument("--request-id", default=None)
    p_emb.add_argument(
        "--embedder",
        choices=["dinov2", "histogram"],
        default="dinov2",
        help="Which embedder to use; falls back to histogram if dinov2 unavailable",
    )

    # run (capture + embed)
    p_run = sub.add_parser("run", help="Capture + embed in one pass")
    _add_capture_args(p_run)

    # baseline
    p_bl = sub.add_parser("baseline", help="Baseline management")
    bl_sub = p_bl.add_subparsers(dest="baseline_command", required=True)
    p_bl_build = bl_sub.add_parser(
        "build",
        help="Capture + embed every URL in baselines/cellar_urls_v0.json into baselines/embeddings/",
    )
    p_bl_build.add_argument("--baseline-id", default=None, help="Override baseline_id (defaults to cellar JSON's baseline_id)")
    p_bl_build.add_argument("--cellar", default=None, help="Override cellar URLs JSON path (default: baselines/cellar_urls_v0.json)")
    p_bl_build.add_argument("--out-dir", default=None, help="Override embeddings output directory (default: baselines/embeddings/)")
    p_bl_build.add_argument(
        "--embedder",
        choices=["dinov2", "histogram"],
        default="histogram",
        help="Which embedder to use; falls back to histogram if dinov2 unavailable",
    )

    args = parser.parse_args()

    if args.command == "capture":
        cmd_capture(args)
    elif args.command == "embed":
        cmd_embed(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "baseline":
        cmd_baseline_build(args)


if __name__ == "__main__":
    main()
