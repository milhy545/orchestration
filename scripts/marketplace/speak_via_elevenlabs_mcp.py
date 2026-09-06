#!/usr/bin/env python3
# FORAI:speak_via_elevenlabs_mcp.py;DEF[load_env_file,build_parser,main];IMP[os,re,json,asyncio,pathlib,argparse,__future__];EXP[load_env_file,build_parser,main];LANG[python]
"""Generate speech via the ElevenLabs MCP python package."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from pathlib import Path


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        cleaned = value.strip()
        if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
            cleaned = cleaned[1:-1]
        os.environ.setdefault(key.strip(), cleaned)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--voice-id", required=True)
    parser.add_argument("--model-id", default="eleven_multilingual_v2")
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--output-format", default="mp3_44100_128")
    parser.add_argument("--agent-family", default="codex")
    return parser


async def main() -> int:
    args = build_parser().parse_args()
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not os.getenv("ELEVENLABS_API_KEY"):
        load_env_file(Path("/vault/runtime/elevenlabs-mcp.env"))
        load_env_file(Path("/vault/runtime/mega-orchestrator.env"))

    os.environ.setdefault("ELEVENLABS_MCP_OUTPUT_MODE", "files")
    os.environ.setdefault("ELEVENLABS_MCP_BASE_PATH", str(output_path.parent))

    if not os.getenv("ELEVENLABS_API_KEY"):
        print(json.dumps({"error": "ELEVENLABS_API_KEY is not configured"}))
        return 1

    try:
        from elevenlabs_mcp.server import mcp
    except Exception as exc:  # pragma: no cover - dependency may be absent locally
        print(json.dumps({"error": f"Unable to import elevenlabs_mcp: {exc}"}))
        return 1

    result = await mcp.call_tool(
        "text_to_speech",
        {
            "text": args.text,
            "voice_id": args.voice_id,
            "model_id": args.model_id,
            "output_directory": str(output_path.parent),
            "output_format": args.output_format,
        },
    )

    payload = {
        "agent_family": args.agent_family,
        "output_path": str(output_path),
        "mime_type": "audio/mpeg",
        "playback_hint": f"Play the generated file at {output_path}",
    }
    if result is not None and hasattr(result, "content"):
        payload["content"] = []
        for item in result.content:
            if hasattr(item, "text"):
                payload["content"].append(item.text)
                match = re.search(r"File saved as:\s*(.+?)\.", item.text)
                if match:
                    payload["output_path"] = match.group(1).strip()

    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
