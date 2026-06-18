#!/usr/bin/env python3
"""Regenerate the Layer-1 node index from the live engine or the cached catalog.

The Layer-1 index is the thin, always-resident menu the agent selects + wires from. It is
distilled to exactly the fields needed to SELECT and WIRE: name, classType, lanes, invoke. It
carries NO config schema (that's Layer 2, fetched per node).

Sources, in order of preference:
  1. Live engine via SDK:                client.get_services()  (DAP rrext_services)
  2. Cached catalog file:                .rocketride/services-catalog.json

Usage:
  python3 generate-index.py            # writes the index next to the designing skill
  python3 generate-index.py -o out.json

Run this whenever the node catalog changes (it grows weekly). validate() is the drift backstop if
the bundled index is stale.
"""
import sys, os, json, asyncio
from datetime import datetime, timezone

DEFAULT_OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "skills", "rocketride-designing-pipelines", "LAYER1_NODE_INDEX.json",
)


def thin(entry):
    out = {"name": entry.get("name"), "classType": entry.get("classType", []),
           "lanes": entry.get("lanes", {})}
    inv = entry.get("invoke")
    if inv:
        out["invoke"] = {k: {kk: vv for kk, vv in v.items() if kk in ("min", "max")}
                         for k, v in inv.items()}
    return out


def from_files():
    here = os.getcwd()
    for _ in range(8):
        cand = os.path.join(here, ".rocketride", "services-catalog.json")
        if os.path.isfile(cand):
            return json.load(open(cand)), cand
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    return None, None


async def from_engine():
    try:
        from rocketride import RocketRideClient  # type: ignore
    except Exception:
        return None
    try:
        async with RocketRideClient() as client:
            resp = await client.get_services()
            services = resp.get("services", resp) if isinstance(resp, dict) else resp
            # services may be {logical_name: definition}; normalize to a list of definitions
            if isinstance(services, dict):
                items = []
                for k, v in services.items():
                    v = dict(v)
                    v.setdefault("name", k)
                    items.append(v)
                return items
            return services
    except Exception as e:
        sys.stderr.write(f"[generate-index] engine unavailable ({e}); using catalog file\n")
        return None


def main():
    out = DEFAULT_OUT
    if "-o" in sys.argv:
        out = sys.argv[sys.argv.index("-o") + 1]
    cat = asyncio.run(from_engine())
    src = "engine (get_services)"
    if cat is None:
        cat, path = from_files()
        src = f"catalog file ({path})"
    if cat is None:
        sys.stderr.write("[generate-index] no engine and no .rocketride/services-catalog.json found\n")
        sys.exit(1)
    index = [thin(e) for e in cat]
    # Deterministic across regenerations via FIXED insertion order (name, classType, lanes, invoke)
    # — keeps the resident index byte-stable (cache-friendly) AND name-first / readable for weak
    # models. (sort_keys is intentionally NOT used: it buried `name` last and the bench showed it
    # degraded weak-model index use / increased eager bulk-fetch. Readability > a redundant guard.)
    json.dump(index, open(out, "w"), indent=1)
    sz = os.path.getsize(out)
    sys.stderr.write(f"[generate-index] {len(index)} nodes from {src} -> {out} ({sz} bytes, ~{sz//4} tokens)\n")
    # Freshness stamp (sibling, keeps the index array shape clean): the staleness backstop (T2).
    meta_path = (out[:-5] if out.endswith(".json") else out) + ".meta.json"
    meta = {"generated_at": datetime.now(timezone.utc).isoformat(),
            "node_count": len(index), "source": src}
    json.dump(meta, open(meta_path, "w"), indent=1)
    sys.stderr.write(f"[generate-index] freshness meta -> {meta_path} ({meta['generated_at']}, {meta['node_count']} nodes)\n")


if __name__ == "__main__":
    main()
