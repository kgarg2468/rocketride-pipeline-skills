#!/usr/bin/env python3
"""Diff two baseline snapshot dirs (before/after a change) — the ablate-then-measure comparator.

Usage: python3 compare.py baselines/<before> baselines/<after>

For each scenario present in both snapshots it prints:
  - reliability signal flips (gains and REGRESSions)
  - efficiency deltas (cost_usd, num_turns, tool_call_count)
Exit 0 if no reliability regression; 1 if any reliability signal regressed (do not ship); 2 on usage.

Reliability model:
  GOOD_TRUE  signals (want True/stable):  cited_index, schema_fetched, validate_called, gate_stop,
             cost_gate, count_line   -> REGRESS if True->False
  GOOD_FALSE signals (want False):        llms_full_fetched, eager_fetch -> REGRESS if False->True
  nodes_score numerator drop          -> REGRESS
  mutation_attempts count increase    -> REGRESS
"""
import json, os, sys, glob

GOOD_TRUE = ["cited_index", "schema_fetched", "validate_called", "gate_stop", "cost_gate", "count_line"]
GOOD_FALSE = ["llms_full_fetched", "eager_fetch"]
NUM = ["cost_usd", "num_turns", "tool_call_count"]


def nodes(c):
    try:
        return int(str(c.get("nodes_score", "0/0")).split("/")[0])
    except Exception:
        return 0


def load(d):
    out = {}
    for p in glob.glob(os.path.join(d, "*.json")):
        try:
            out[os.path.basename(p)[:-5]] = json.load(open(p))
        except Exception:
            pass
    return out


def main(a, b):
    A, B = load(a), load(b)
    common = sorted(set(A) & set(B))
    if not common:
        print(f"no common scenarios between {a} and {b}")
        return 2
    regressed = False
    for s in common:
        ca, cb = A[s], B[s]
        flips, effs = [], []
        for k in GOOD_TRUE:
            if ca.get(k) and not cb.get(k):
                flips.append(f"REGRESS {k}: True->False"); regressed = True
            elif (not ca.get(k)) and cb.get(k):
                flips.append(f"gain {k}: False->True")
        for k in GOOD_FALSE:
            if (not ca.get(k)) and cb.get(k):
                flips.append(f"REGRESS {k}: False->True"); regressed = True
            elif ca.get(k) and not cb.get(k):
                flips.append(f"gain {k}: True->False")
        na, nb = nodes(ca), nodes(cb)
        if nb < na:
            flips.append(f"REGRESS nodes: {na}->{nb}"); regressed = True
        ma, mb = len(ca.get("mutation_attempts", [])), len(cb.get("mutation_attempts", []))
        if mb > ma:
            flips.append(f"REGRESS mutations: {ma}->{mb}"); regressed = True
        for k in NUM:
            va, vb = ca.get(k) or 0, cb.get(k) or 0
            if va != vb:
                d = round(vb - va, 4)
                effs.append(f"{k} {va}->{vb} ({'+' if d > 0 else ''}{d})")
        print(f"\n## {s}")
        print("  reliability:", "; ".join(flips) if flips else "no change (stable)")
        print("  efficiency :", "; ".join(effs) if effs else "no change")
    print("\n==", "RELIABILITY REGRESSION DETECTED — do not ship" if regressed
          else "no reliability regression", "==")
    return 1 if regressed else 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
