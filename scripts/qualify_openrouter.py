#!/usr/bin/env python3
"""Run one bounded OpenRouter compatibility probe and write redacted evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import time
from urllib.request import Request, urlopen


def final_content(message: dict[str, object]) -> str:
    """Reasoning is not a user-visible completion and never counts as a pass."""
    value = message.get("content")
    return value if isinstance(value, str) else ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-tokens", type=int, default=128)
    args = parser.parse_args()
    if not 1 <= args.max_tokens <= 256:
        raise SystemExit("--max-tokens must be between 1 and 256")
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is required")
    body = json.dumps({"model": args.model, "messages": [{"role": "user", "content": "Reply only: C3R_OK"}],
                       "max_tokens": args.max_tokens, "temperature": 0}).encode()
    request = Request("https://openrouter.ai/api/v1/chat/completions", data=body,
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                               "X-Title": "C3R Provider Qualification"})
    started = time.perf_counter()
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
        status = response.status
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    choice = payload.get("choices", [{}])[0]
    message = choice.get("message", {})
    content = final_content(message)
    completed = bool(content.strip()) and choice.get("finish_reason") == "stop"
    evidence = {"schema_version": "1.0", "provider": "openrouter", "model_requested": args.model,
                "model_returned": payload.get("model"), "http_status": status, "latency_ms": elapsed_ms,
                "response_present": bool(content.strip()), "completed_response": completed,
                "response_sha256": sha256(content.encode()).hexdigest(),
                "usage": payload.get("usage", {}), "collected_at": datetime.now(timezone.utc).isoformat(),
                "finish_reason": choice.get("finish_reason"),
                "prompt_policy": "fixed-nonsensitive-v1", "max_tokens": args.max_tokens}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"probed {args.model}: status={status}, completed={completed}, latency_ms={elapsed_ms}")
    if not completed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
