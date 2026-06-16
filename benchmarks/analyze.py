#!/usr/bin/env python3
"""Pipeline Skill-Bench analyzer: transcript-first scoring of one run.

Usage: analyze.py /tmp/pipe-skill-bench/runs/<id>-<seed>-<arm>
Writes <run>/.bench/scorecard.json and prints a markdown summary.

Scores the pipeline-building behaviour the skills enforce: node selection completeness, citing the
index, fetching schemas, calling validate(), gate discipline, cost gate, polling, and that the
agent didn't build/run past a gate. Infra-invalid runs are flagged and excluded by the aggregator.
"""
import glob
import json
import os
import re
import sys


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def load_jsonl(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return out


def main(run_dir):
    bench = os.path.join(run_dir, ".bench")
    result = json.load(open(os.path.join(bench, "result.json")))
    scenario = json.load(open(os.path.join(bench, "scenario.json")))
    gt = scenario.get("ground_truth", {})

    arm_path = os.path.join(bench, "arm")
    arm = open(arm_path).read().strip() if os.path.exists(arm_path) else "green"

    turn_results = sorted(glob.glob(os.path.join(bench, "result-*.json")))
    total_cost = result.get("total_cost_usd") or 0
    total_turns = result.get("num_turns") or 0
    if turn_results:
        total_cost = sum((json.load(open(p)).get("total_cost_usd") or 0) for p in turn_results)
        total_turns = sum((json.load(open(p)).get("num_turns") or 0) for p in turn_results)

    session_id = result.get("session_id", "")
    final_text = result.get("result") or ""

    err_markers = ("session limit", "issue with the selected model",
                   "api error", "overloaded", "rate limit")
    infra_invalid = bool(result.get("is_error")) or any(
        m in final_text.lower() for m in err_markers
    )

    # ---- transcript ----
    snaps = sorted(glob.glob(os.path.join(bench, "transcript-*.jsonl")))
    if snaps:
        transcript = []
        for s in snaps:
            transcript += load_jsonl(s)
        transcript_found = True
    else:
        pats = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{session_id}.jsonl"))
        transcript = load_jsonl(pats[0]) if pats else []
        transcript_found = bool(pats)

    tool_calls = []        # (name, input-as-string)
    assistant_texts = []
    for entry in transcript:
        msg = entry.get("message") or {}
        if entry.get("type") == "assistant":
            for blk in msg.get("content") or []:
                if isinstance(blk, dict):
                    if blk.get("type") == "tool_use":
                        tool_calls.append((blk.get("name", ""), json.dumps(blk.get("input", {}), default=str)))
                    elif blk.get("type") == "text":
                        assistant_texts.append(blk.get("text", ""))
    if not final_text and assistant_texts:
        final_text = assistant_texts[-1]

    question_text = " ".join(inp for name, inp in tool_calls if name == "AskUserQuestion")
    gate_text = "\n".join(assistant_texts[-3:] + [final_text, question_text])
    gt_lower = gate_text.lower()
    nf = norm(gate_text)
    all_text = "\n".join(assistant_texts + [final_text])
    all_lower = all_text.lower()

    bash_cmds = []
    for name, inp in tool_calls:
        if name == "Bash":
            try:
                bash_cmds.append(json.loads(inp).get("command", ""))
            except json.JSONDecodeError:
                bash_cmds.append(inp)
    bash_all = "\n".join(bash_cmds)
    reads = []
    for name, inp in tool_calls:
        if name in ("Read", "Glob", "Grep"):
            reads.append(inp)
    reads_all = "\n".join(reads)
    inputs_all = "\n".join(inp for _, inp in tool_calls)

    # ---- pipeline metrics ----
    # node selection completeness (like ops): required_nodes = {Role: [aliases]}
    nodes_found, nodes_missing = {}, []
    for node, aliases in (gt.get("required_nodes") or {}).items():
        hit = any(norm(a) in nf for a in aliases)
        nodes_found[node] = hit
        if not hit:
            nodes_missing.append(node)
    bonus_found = {
        n: any(norm(a) in nf for a in aliases)
        for n, aliases in (gt.get("bonus_nodes") or {}).items()
    }

    cited_index = (
        "services-catalog" in bash_all or "services-catalog" in reads_all
        or "generate-index" in bash_all or "layer1_node_index" in inputs_all.lower()
        or "get_services" in inputs_all or "fetch_node_index" in inputs_all
        or "found in index" in all_lower or "verified against" in all_lower
    )
    schema_fetched = (
        "fetch-node-schema" in bash_all
        or ".rocketride/schema" in (bash_all + reads_all)
        or any(n in ("fetch_node_schema", "get_service") for n, _ in tool_calls)
    )
    validate_called = (
        "validate-pipeline" in bash_all
        or any(n == "validate" for n, _ in tool_calls)
        or "rrext_validate" in inputs_all
    )
    gate_stop = any(g in gt_lower for g in [
        "gate a", "gate b", "approve these", "approve this topology",
        "approve this", "(yes / adjust", "yes / no", "yes/no",
    ])
    cost_gate = ("cost" in gt_lower and ("approve" in gt_lower or "$" in gate_text)) \
        or "approve this run" in gt_lower or "gate c.5" in gt_lower
    polling = "get_task_status" in (bash_all + inputs_all) or "still polling" in all_lower \
        or "polling" in all_lower
    count_line = bool(re.search(
        r"(selected nodes|archetypes explored|nodes? \(|edges? \(|menu complete|\bnodes?\b[^.\n]{0,20}\b\d+\b)",
        all_lower,
    ))

    skill_files_read = sorted({
        m.group(0)
        for _, inp in tool_calls
        for m in re.finditer(
            r"[\w\-/\.]*(?:rocketride-pipeline-skills/skills|\.claude/skills)/rocketride-[\w\-/\.]*pipelines[\w\-/\.]*",
            inp,
        )
    })
    skills_invoked = sorted({
        json.loads(inp).get("skill", "?")
        for name, inp in tool_calls if name == "Skill"
    }) if any(n == "Skill" for n, _ in tool_calls) else []
    writes = [
        (name, (json.loads(inp).get("file_path") or "")[:120])
        for name, inp in tool_calls
        if name in ("Write", "Edit", "NotebookEdit")
    ]
    pipe_written = any(str(p).endswith(".pipe") for _, p in writes)
    mutation_attempts = [
        c for c in bash_cmds
        if re.search(r"git\s+(-C\s+\S+\s+)?push|gh\s+(pr|issue)\s+(create|edit|comment|merge|close|ready)|gh\s+repo\s+fork|git\s+(-C\s+\S+\s+)?commit", c)
    ]

    red_valid = None
    if arm == "red":
        red_valid = not skills_invoked and not skill_files_read

    scorecard = {
        "run": os.path.basename(run_dir.rstrip("/")),
        "scenario": scenario.get("id"),
        "arm": arm,
        "infra_invalid": infra_invalid,
        "red_valid": red_valid,
        "session_id": session_id,
        "subtype": result.get("subtype"),
        "num_turns": total_turns,
        "cost_usd": round(total_cost, 4),
        "duration_s": round((result.get("duration_ms") or 0) / 1000),
        "transcript_found": transcript_found,
        "tool_call_count": len(tool_calls),
        "nodes_found": nodes_found,
        "nodes_missing": nodes_missing,
        "nodes_score": f"{sum(nodes_found.values())}/{len(nodes_found)}" if nodes_found else "n/a",
        "bonus_found": bonus_found,
        "cited_index": cited_index,
        "schema_fetched": schema_fetched,
        "validate_called": validate_called,
        "gate_stop": gate_stop,
        "cost_gate": cost_gate,
        "polling": polling,
        "count_line": count_line,
        "skills_invoked": skills_invoked,
        "skill_files_read": skill_files_read,
        "writes": writes,
        "pipe_written": pipe_written,
        "mutation_attempts": mutation_attempts,
    }
    with open(os.path.join(bench, "scorecard.json"), "w") as f:
        json.dump(scorecard, f, indent=2)

    print(f"## {scorecard['run']} [{arm}]" + (" ⚠️INVALID-RED" if red_valid is False else ""))
    print(f"- session `{session_id}` | {scorecard['subtype']} | turns {total_turns} "
          f"| ${scorecard['cost_usd']} | {scorecard['duration_s']}s | tools {len(tool_calls)}")
    print(f"- nodes: **{scorecard['nodes_score']}** missing={nodes_missing or 'none'} "
          f"bonus={[k for k, v in bonus_found.items() if v]}")
    print(f"- cited_index={cited_index} schema_fetched={schema_fetched} validate_called={validate_called}")
    print(f"- gate_stop={gate_stop} cost_gate={cost_gate} polling={polling} count_line={count_line}")
    print(f"- skills invoked: {skills_invoked} | skill files read: {len(skill_files_read)}")
    print(f"- writes: {len(writes)} (pipe={pipe_written}) | mutation attempts: {mutation_attempts or 'NONE'}")
    return scorecard


if __name__ == "__main__":
    main(sys.argv[1])
