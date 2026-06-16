#!/usr/bin/env python3
"""PreToolUse hook: append every tool call to .bench/tool_calls.jsonl. Never blocks (exit 0)."""
import json
import os
import sys
import time

try:
    data = json.load(sys.stdin)
    rec = {
        "ts": time.time(),
        "tool": data.get("tool_name"),
        "input": data.get("tool_input"),
    }
    base = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    path = os.path.join(base, ".bench", "tool_calls.jsonl")
    line = json.dumps(rec, default=str)
    with open(path, "a") as f:
        f.write(line[:4000] + "\n")
except Exception:
    pass
sys.exit(0)
