#!/usr/bin/env python3
"""Fetch one node's config schema (Layer 2).

CONSTRAINT (agent contract / future MCP tool description): configure a node using ONLY the fields
this schema defines — never invent field names (e.g. it is `modelTotalTokens`, not `max_tokens`).
Fetch ONE node at a time; never bulk-load the schema catalog (FF#17).

Order of preference:
  1. Live engine via the RocketRide SDK:  client.get_service(<name>)
  2. The cached catalog file:             .rocketride/schema/<name>.json

Usage:
  python3 fetch-node-schema.py <node_name>
  python3 fetch-node-schema.py llm_openai

Prints the service/schema definition as JSON. The agent reads `required` fields, the
`Pipe.schema` (incl. dependencies.profile.oneOf for LLM/embedding/store profiles), and any
conditional constraints before configuring the node. Never configure a node without this.
"""
import sys, os, json, asyncio


def from_files(name):
    """Walk up from cwd looking for .rocketride/schema/<name>.json."""
    here = os.getcwd()
    for _ in range(8):
        cand = os.path.join(here, ".rocketride", "schema", f"{name}.json")
        if os.path.isfile(cand):
            return json.load(open(cand))
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    return None


async def from_engine(name):
    try:
        from rocketride import RocketRideClient  # type: ignore
    except Exception:
        sys.stderr.write("[fetch-node-schema] RocketRide SDK not importable; falling back to files\n")
        sys.stderr.write("ERROR_JSON: " + json.dumps({
            "code": "ENGINE_UNAVAILABLE", "retriable": False,
            "fallback": "reading the bundled .rocketride/schema/<name>.json (do NOT retry the engine)"}) + "\n")
        return None
    try:
        async with RocketRideClient() as client:  # reads uri/auth from .env
            return await client.get_service(name)
    except Exception as e:
        sys.stderr.write(f"[fetch-node-schema] engine unavailable ({e}); falling back to files\n")
        sys.stderr.write("ERROR_JSON: " + json.dumps({
            "code": "ENGINE_UNAVAILABLE", "retriable": False,
            "fallback": "reading the bundled .rocketride/schema/<name>.json (do NOT retry the engine)"}) + "\n")
        return None


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__)
        sys.exit(2)
    name = sys.argv[1]
    result = asyncio.run(from_engine(name))
    source = "engine (get_service)"
    if result is None:
        result = from_files(name)
        source = ".rocketride/schema file"
    if result is None:
        sys.stderr.write(
            f"[fetch-node-schema] no schema for '{name}' from engine or files.\n"
            f"  - is the node name spelled exactly as in the index?\n"
            f"  - run from a workspace with a .rocketride/ dir, or connect an engine (.env).\n"
        )
        sys.stderr.write("ERROR_JSON: " + json.dumps({
            "code": "SCHEMA_NOT_FOUND", "retriable": False,
            "fallback": "verify the node name against the L1 index — it may not exist; do not invent fields"}) + "\n")
        sys.exit(1)
    sys.stderr.write(f"[fetch-node-schema] source: {source}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
