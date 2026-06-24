#!/usr/bin/env python3
"""Lint NODE_DECISION_GUIDE.md (blocking CI check).

Two invariants the guide must never violate:
  1. ANTI-FABRICATION — every node-shaped id named in the guide exists in LAYER1_NODE_INDEX.json
     (a renamed/removed node must not silently linger as a recommendation).
  2. NO DOLLAR-LITERALS — the guide encodes cost as a *pattern*, never a number (prices go stale).

Exit 0 = clean, 1 = violation. Run: python3 tools/lint_decision_guide.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GUIDE = os.path.join(HERE, "..", "skills", "rocketride-designing-pipelines", "NODE_DECISION_GUIDE.md")
INDEX = os.path.join(HERE, "..", "skills", "rocketride-designing-pipelines", "LAYER1_NODE_INDEX.json")

# classType words + non-node backtick tokens that legitimately appear (not nodes)
CLASSTYPES = {"store", "database", "llm", "embedding", "agent", "memory", "rerank", "source",
              "data", "text", "preprocessor", "image", "audio", "video", "tool", "search",
              "guard", "infrastructure", "target", "crewai", "deepagent"}
ALLOW = CLASSTYPES | {"pgvector", "miniLM", "miniAll", "response_*"}
# a token shaped like a node id in a real family (must then BE a real node)
NODE_SHAPED = re.compile(r"^(llm|embedding|agent|db|memory|rerank|tool|store|preprocessor)_[a-z0-9_]+$")


def main():
    valid = {e["name"] for e in json.load(open(INDEX)) if isinstance(e, dict) and e.get("name")}
    guide = open(GUIDE).read()
    tokens = [t.strip() for t in re.findall(r"`([^`]+)`", guide)]

    fabricated = []
    for t in tokens:
        if t in valid or t in ALLOW or "." in t or "/" in t or "$" in t or " " in t:
            continue
        if NODE_SHAPED.match(t) and t not in valid:
            fabricated.append(t)

    dollars = re.findall(r"\$\s?[0-9]", guide)

    ok = True
    if fabricated:
        ok = False
        print("FAIL anti-fabrication — node ids not in LAYER1_NODE_INDEX.json:", sorted(set(fabricated)))
    if dollars:
        ok = False
        print("FAIL dollar-literals present (cost must be a pattern, not a number):", dollars[:5])
    if ok:
        n_nodes = len({t for t in tokens if t in valid})
        print(f"OK — {n_nodes} catalog nodes referenced, all exist; no dollar-literals.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
