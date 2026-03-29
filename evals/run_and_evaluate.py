#!/usr/bin/env python3
"""
Demesne Auto-Content Validation & Self-Diagnosis System.

Runs the simulation, analyzes the output, detects bugs, scores narrative quality,
and produces a settlement summary + faction analysis.

Usage:
    python evals/run_and_evaluate.py [--skip-run] [--run-dir PATH]
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from glob import glob

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def find_newest_run(output_dir: str) -> str:
    """Find the most recently created run folder."""
    folders = sorted(glob(os.path.join(output_dir, "*/")), key=os.path.getmtime)
    if not folders:
        raise FileNotFoundError(f"No run folders found in {output_dir}")
    return folders[-1].rstrip("/")


def load_run_data(run_dir: str) -> dict:
    """Load all analyzable files from a run folder."""
    data = {"run_dir": run_dir, "run_name": os.path.basename(run_dir)}

    chronicle_path = os.path.join(run_dir, "game_chronicle.json")
    if os.path.exists(chronicle_path):
        with open(chronicle_path) as f:
            data["chronicle"] = json.load(f)

    narrative_path = os.path.join(run_dir, "narrative_summary.txt")
    if os.path.exists(narrative_path):
        with open(narrative_path) as f:
            data["narrative"] = f.read()

    events_path = os.path.join(run_dir, "events.jsonl")
    if os.path.exists(events_path):
        with open(events_path) as f:
            data["events"] = [json.loads(line) for line in f if line.strip()]

    return data


# ── Bug Detection ────────────────────────────────────────────────────────────

def detect_bugs(data: dict) -> list[dict]:
    """Run all deterministic bug checks on the run data."""
    bugs = []
    run_name = data["run_name"]
    narrative = data.get("narrative", "")
    chronicle = data.get("chronicle", {})

    # 1. JSON/XML leaks in narrative
    xml_patterns = [
        (r"<make_structure>\s*\{", "make_structure JSON leak"),
        (r"<strategy_choice>\s*\{", "strategy_choice JSON leak"),
        (r"<investment_choice>\s*\{", "investment_choice JSON leak"),
        (r"<rename_choice>\s*\{", "rename_choice JSON leak"),
        (r"<faction_intro>\s*\{", "faction_intro JSON leak"),
        (r"<place_name>\s*\{", "place_name JSON leak"),
        (r"<settlement_name>\s*\{", "settlement_name JSON leak"),
        (r"<challenge_response>\s*\{", "challenge_response JSON leak"),
    ]
    for pattern, desc in xml_patterns:
        for match in re.finditer(pattern, narrative):
            line_num = narrative[:match.start()].count("\n") + 1
            bugs.append({
                "run": run_name, "bug_type": "json_leak",
                "location": f"narrative_summary.txt:{line_num}",
                "detail": desc, "severity": "high",
            })

    # Also check for raw JSON blocks (opening brace after newline with "name":)
    for match in re.finditer(r'\n\s*\{\s*\n\s*"name":', narrative):
        line_num = narrative[:match.start()].count("\n") + 1
        bugs.append({
            "run": run_name, "bug_type": "json_leak",
            "location": f"narrative_summary.txt:{line_num}",
            "detail": "Raw JSON object in narrative", "severity": "high",
        })

    # 2. Metagame leaks
    metagame_patterns = [
        (r"\b(red|blue|green|orange|pink) tokens?\b", "token color reference"),
        (r"\bvictory points?\b", "victory points reference"),
        (r"\bL[123]\b", "culture level label"),
        (r"\bSECTION [12]\b", "section label leak"),
        (r"\bOPTION [AB]\b", "option label leak"),
    ]
    for pattern, desc in metagame_patterns:
        for match in re.finditer(pattern, narrative, re.IGNORECASE):
            # Skip if inside JSON (final state dump at end)
            if "FINAL STATE" in narrative[:match.start()][-200:]:
                continue
            line_num = narrative[:match.start()].count("\n") + 1
            bugs.append({
                "run": run_name, "bug_type": "metagame_leak",
                "location": f"narrative_summary.txt:{line_num}",
                "detail": f"{desc}: '{match.group()}'", "severity": "medium",
            })

    # 3. Name duplicates
    all_names = []
    for f in chronicle.get("factions", []):
        all_names.append(f["name"])
    for p in chronicle.get("places", []):
        all_names.append(p["name"])
    for era in chronicle.get("eras", []):
        for e in era.get("events", []):
            if e.get("event_type") == "historical_figure":
                all_names.append(e.get("name", ""))

    name_counts = Counter(n for n in all_names if n)
    for name, count in name_counts.items():
        if count > 1:
            bugs.append({
                "run": run_name, "bug_type": "name_duplicate",
                "location": "game_chronicle.json",
                "detail": f"'{name}' appears {count} times", "severity": "medium",
            })

    # 4. Truncated text (content blocks ending mid-word)
    blocks = narrative.split("\n" + "-" * 40 + "\n")
    for i, block in enumerate(blocks):
        stripped = block.rstrip()
        if stripped and len(stripped) > 50:
            last_char = stripped[-1]
            if last_char.isalpha() and last_char.islower():
                line_num = narrative[:narrative.find(stripped[-30:])].count("\n") + 1
                bugs.append({
                    "run": run_name, "bug_type": "truncated_text",
                    "location": f"narrative_summary.txt:~{line_num}",
                    "detail": f"Block {i} ends mid-word: '...{stripped[-40:]}'",
                    "severity": "medium",
                })

    # 5. Empty/useless factions
    for f in chronicle.get("factions", []):
        if f.get("victory_points", 0) == 0 and f.get("influence", 0) <= 0 and sum(f.get("tokens", {}).values()) == 0:
            bugs.append({
                "run": run_name, "bug_type": "empty_faction",
                "location": "game_chronicle.json",
                "detail": f"'{f['name']}' has 0 VP, <=0 influence, 0 tokens",
                "severity": "low",
            })

    # 6. Wiki seeds consumed but empty
    seeds = chronicle.get("inspiration_seeds", {}).get("seeds", [])
    for s in seeds:
        if s.get("used") and not s.get("concept", "").strip():
            bugs.append({
                "run": run_name, "bug_type": "empty_seed",
                "location": "game_chronicle.json",
                "detail": f"Seed {s['id']} marked used but concept is empty",
                "severity": "low",
            })

    return bugs


# ── Faction Analysis ─────────────────────────────────────────────────────────

def analyze_factions(chronicle: dict) -> list[dict]:
    """Deterministic faction analysis: VP, influence, relationships."""
    cultures = chronicle.get("cultures", {})
    factions = chronicle.get("factions", [])
    results = []

    for f in sorted(factions, key=lambda f: f.get("victory_points", 0), reverse=True):
        goals = f.get("goals", {})
        p = goals.get("primary", {})
        cat_data = cultures.get(p.get("category", ""), {})
        primary_achieved = (
            cat_data.get("level", 0) >= p.get("level", 99) and
            p.get("option", "") in cat_data.get("options_chosen", [])
        )

        # Find allies and rivals from goal overlaps
        allies = []
        rivals = []
        my_cats = set()
        if p.get("category"):
            my_cats.add(p["category"])
        for s in goals.get("secondary", []):
            if s.get("category"):
                my_cats.add(s["category"])
        t = goals.get("tertiary", {})
        if t.get("category"):
            my_cats.add(t["category"])

        for other in factions:
            if other["name"] == f["name"]:
                continue
            other_goals = other.get("goals", {})
            other_cats = set()
            op = other_goals.get("primary", {})
            if op.get("category"):
                other_cats.add(op["category"])
            for s in other_goals.get("secondary", []):
                if s.get("category"):
                    other_cats.add(s["category"])
            ot = other_goals.get("tertiary", {})
            if ot.get("category"):
                other_cats.add(ot["category"])

            shared = my_cats & other_cats
            if shared:
                # Check for option conflicts in shared categories
                conflicting = False
                for cat in shared:
                    my_opt = p.get("option") if p.get("category") == cat else None
                    other_opt = op.get("option") if op.get("category") == cat else None
                    if my_opt and other_opt and my_opt != other_opt:
                        conflicting = True
                        rivals.append(f"{other['name']} (conflict: {cat})")
                        break
                if not conflicting:
                    allies.append(f"{other['name']} (shared: {', '.join(shared)})")

        results.append({
            "name": f["name"],
            "ideology": f.get("ideology", "?"),
            "species": f.get("species", "?"),
            "vp": f.get("victory_points", 0),
            "influence": f.get("influence", 0),
            "vp_distance_from_win": 80 - f.get("victory_points", 0),
            "primary_goal": f"{p.get('option', '?')} ({p.get('category', '?')} L{p.get('level', '?')})",
            "primary_achieved": primary_achieved,
            "allies": allies[:3],
            "rivals": rivals[:3],
        })

    return results


# ── Narrative Scoring (LLM) ──────────────────────────────────────────────────

def score_narrative(chronicle: dict, narrative: str) -> dict:
    """Use LLM to score narrative quality and generate summary."""
    import anthropic
    import config

    if not config.ANTHROPIC_API_KEY:
        return {"error": "No API key", "scores": {}, "summary": "", "recommendations": []}

    # Build compact context for the LLM
    settlement = chronicle.get("settlement", {})
    cultures = chronicle.get("cultures", {})
    factions = chronicle.get("factions", [])
    seeds = chronicle.get("inspiration_seeds", {})

    culture_list = []
    for cat, info in cultures.items():
        if info.get("level", 0) > 0:
            culture_list.append(f"{cat} L{info['level']}: {', '.join(info.get('options_chosen', []))}")

    faction_list = []
    for f in sorted(factions, key=lambda f: f.get("victory_points", 0), reverse=True):
        faction_list.append(f"{f['name']} ({f.get('ideology', '?')} {f.get('species', '?')}): {f.get('victory_points', 0)} VP, inf={f.get('influence', 0)}")

    challenges = []
    for era in chronicle.get("eras", []):
        for c in era.get("challenge_results", []):
            challenges.append(f"Era {c.get('era', '?')}: {'WIN' if c.get('success') else 'FAIL'}")

    seed_list = []
    for s in seeds.get("seeds", []):
        status = f"used in {s.get('used_in', '?')}" if s.get("used") else "unused"
        seed_list.append(f"{s.get('concept', '?')[:60]}... [{status}]")

    # Extract traveler sections (last ~500 chars before each era boundary)
    traveler_sections = []
    era_breaks = [m.start() for m in re.finditer(r"^={60}", narrative, re.MULTILINE)]
    for i, pos in enumerate(era_breaks):
        # Look backward from era break for traveler content
        pre = narrative[max(0, pos - 800):pos].strip()
        if pre:
            traveler_sections.append(pre[-400:])

    prompt = f"""\
Evaluate this fantasy settlement simulation output.

SETTLEMENT: {settlement.get('name', '?')} ({settlement.get('location', '?')} / {settlement.get('terrain', '?')})
Stage: {settlement.get('stage', '?')} | Eras: {settlement.get('total_eras', '?')}

ESTABLISHED CULTURES:
{chr(10).join(culture_list) if culture_list else 'None'}

FACTIONS:
{chr(10).join(faction_list)}

CHALLENGES: {', '.join(challenges)}

WIKI SOURCE: {seeds.get('source_article', 'None')}
SEEDS:
{chr(10).join(seed_list) if seed_list else 'None'}

TRAVELER DESCRIPTIONS (what a visitor sees):
{chr(10).join(traveler_sections[-2:]) if traveler_sections else 'None available'}

NARRATIVE EXCERPT (last 2000 chars):
{narrative[-2000:]}

Score each dimension 1-10 and explain briefly:
1. DRAMA: Do challenges feel consequential? Do factions rise and fall?
2. CULTURE_ALIGNMENT: Does the narrative reflect established cultures?
3. FACTION_DYNAMICS: Are alliances, rivalries, and scapegoating visible?
4. WORLD_COHERENCE: Does the settlement feel like a real, consistent place?
5. SEED_INTEGRATION: Did wiki seeds produce unique, non-generic elements?

Then write exactly 2 paragraphs summarizing this settlement for someone who hasn't read the files. Tell them what's interesting, where the drama is, and where the tensions are NOW.

Output as JSON:
{{
  "scores": {{"drama": N, "culture_alignment": N, "faction_dynamics": N, "world_coherence": N, "seed_integration": N}},
  "score_notes": "brief explanation of scores",
  "summary": "Two paragraphs...",
  "recommendations": ["improvement suggestion 1", "..."]
}}
"""

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=config.MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        # Strip markdown fences
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3].strip()
        return json.loads(raw)
    except Exception as e:
        return {"error": str(e), "scores": {}, "summary": "", "recommendations": []}


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Demesne evaluation pipeline")
    parser.add_argument("--skip-run", action="store_true", help="Skip simulation, analyze existing output")
    parser.add_argument("--run-dir", help="Analyze a specific run folder")
    args, extra_args = parser.parse_known_args()

    output_dir = os.path.join(PROJECT_ROOT, "output")

    # Step 1: Run simulation (pass all extra args directly to main.py)
    if not args.skip_run and not args.run_dir:
        print("=== RUNNING SIMULATION ===")
        # Default args if none provided
        if not any(a.startswith("--eras") for a in extra_args):
            extra_args = ["--eras", "6", "--factions", "4"] + extra_args
        cmd = [sys.executable, os.path.join(PROJECT_ROOT, "main.py")] + extra_args
        print(f"  Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        if result.returncode != 0:
            print(f"  Simulation failed with code {result.returncode}")
            sys.exit(1)
        print("  Simulation complete.\n")

    # Step 2: Find and load run
    if args.run_dir:
        run_dir = args.run_dir
    else:
        run_dir = find_newest_run(output_dir)
    print(f"=== ANALYZING: {os.path.basename(run_dir)} ===\n")
    data = load_run_data(run_dir)

    if "chronicle" not in data:
        print("  ERROR: No game_chronicle.json found")
        sys.exit(1)

    # Step 3: Bug detection
    print("=== BUG DETECTION ===")
    bugs = detect_bugs(data)
    by_type = Counter(b["bug_type"] for b in bugs)
    print(f"  Found {len(bugs)} bugs: {dict(by_type)}")
    for b in bugs[:5]:
        print(f"    [{b['severity'].upper()}] {b['bug_type']}: {b['detail'][:80]}")
    if len(bugs) > 5:
        print(f"    ... and {len(bugs) - 5} more")

    # Append to buglist.json
    buglist_path = os.path.join(os.path.dirname(__file__), "buglist.json")
    existing_bugs = []
    if os.path.exists(buglist_path):
        with open(buglist_path) as f:
            existing_bugs = json.load(f)
    existing_bugs.extend(bugs)
    with open(buglist_path, "w") as f:
        json.dump(existing_bugs, f, indent=2)

    # Step 4: Faction analysis
    print("\n=== FACTION ANALYSIS ===")
    faction_analysis = analyze_factions(data["chronicle"])
    for fa in faction_analysis:
        status = "✓ PRIMARY" if fa["primary_achieved"] else f"→ {fa['primary_goal']}"
        print(f"  {fa['vp']:3d}VP inf={fa['influence']:3d} {fa['name']} ({fa['ideology']} {fa['species']})")
        print(f"       {status}")
        if fa["allies"]:
            print(f"       Allies: {', '.join(fa['allies'][:2])}")
        if fa["rivals"]:
            print(f"       Rivals: {', '.join(fa['rivals'][:2])}")

    # Step 5: Narrative scoring (LLM)
    print("\n=== NARRATIVE SCORING ===")
    scoring = score_narrative(data["chronicle"], data.get("narrative", ""))
    scores = scoring.get("scores", {})
    if scores:
        for dim, score in scores.items():
            bar = "█" * score + "░" * (10 - score)
            print(f"  {dim:20s} {bar} {score}/10")
        avg = sum(scores.values()) / len(scores) if scores else 0
        print(f"  {'AVERAGE':20s} {'=' * 20} {avg:.1f}/10")
    else:
        print(f"  Scoring failed: {scoring.get('error', 'unknown')}")

    summary = scoring.get("summary", "")
    if summary:
        print(f"\n=== SETTLEMENT SUMMARY ===\n{summary}")

    recommendations = scoring.get("recommendations", [])
    if recommendations:
        print(f"\n=== RECOMMENDATIONS ===")
        for r in recommendations:
            print(f"  - {r}")

    # Step 6: Write eval report
    report = {
        "run": data["run_name"],
        "timestamp": datetime.now().isoformat(),
        "bugs_found": len(bugs),
        "bugs_by_type": dict(by_type),
        "scores": scores,
        "score_notes": scoring.get("score_notes", ""),
        "average_score": sum(scores.values()) / len(scores) if scores else 0,
        "summary": summary,
        "faction_analysis": faction_analysis,
        "recommendations": recommendations,
    }
    report_path = os.path.join(run_dir, "eval_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n=== Report saved: {report_path} ===")

    # Step 7: Check for systemic bugs
    if len(existing_bugs) > 10:
        systemic = Counter(b["bug_type"] for b in existing_bugs)
        for bug_type, count in systemic.most_common(3):
            if count >= 3:
                print(f"\n  ⚠ SYSTEMIC BUG: '{bug_type}' appeared {count} times across runs")


if __name__ == "__main__":
    main()
