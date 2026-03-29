#!/usr/bin/env python3
"""
Batch evaluation runner. Runs N simulations with randomized CLI parameters,
evaluates each, and produces a summary report.

Usage:
    python evals/batch_eval.py              # 5 runs with random configs
    python evals/batch_eval.py --runs 10    # 10 runs
    python evals/batch_eval.py --runs 3 --skip-scoring  # fast mode, no LLM scoring
"""
import argparse
import json
import os
import random
import subprocess
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ── Random CLI configurations ────────────────────────────────────────────────

CONFIGS = [
    # Vanilla
    {"label": "vanilla", "args": ["--eras", "5", "--factions", "4"]},
    # High difficulty stress test
    {"label": "high-diff", "args": ["--eras", "6", "--factions", "4", "--difficulty", "14"]},
    # Many factions
    {"label": "crowded", "args": ["--eras", "5", "--factions", "6"]},
    # Minimal factions
    {"label": "duel", "args": ["--eras", "6", "--factions", "2"]},
    # Dynamic growth
    {"label": "growth-era", "args": ["--eras", "6", "--factions", "2", "--addFactions", "perEra"]},
    {"label": "growth-success", "args": ["--eras", "6", "--factions", "3", "--addFactions", "perSuccess"]},
    {"label": "growth-level", "args": ["--eras", "6", "--factions", "3", "--addFactions", "perLevel"]},
    # Darwinian
    {"label": "darwinian", "args": ["--eras", "6", "--factions", "5", "--removeFactions", "perFail"]},
    {"label": "brutal", "args": ["--eras", "6", "--factions", "5", "--difficulty", "13", "--removeFactions", "perFail", "noInfluence"]},
    # Full churn
    {"label": "churn", "args": ["--eras", "8", "--factions", "3", "--addFactions", "perEra", "--removeFactions", "perFail"]},
    # Long game
    {"label": "epic", "args": ["--eras", "10", "--factions", "4"]},
    # Easy start
    {"label": "easy", "args": ["--eras", "6", "--factions", "4", "--difficulty", "6"]},
    # Power consolidation
    {"label": "consolidation", "args": ["--eras", "8", "--factions", "3", "--addFactions", "perLevel", "--removeFactions", "perLevel"]},
]


def main():
    parser = argparse.ArgumentParser(description="Batch Demesne evaluation")
    parser.add_argument("--runs", type=int, default=5, help="Number of runs")
    parser.add_argument("--skip-scoring", action="store_true", help="Skip LLM narrative scoring (faster)")
    args = parser.parse_args()

    # Pick N random configs (with replacement if N > len(CONFIGS))
    selected = random.choices(CONFIGS, k=args.runs)

    results = []
    print(f"{'='*60}")
    print(f"BATCH EVALUATION: {args.runs} runs")
    print(f"{'='*60}\n")

    for i, config in enumerate(selected):
        print(f"\n{'─'*60}")
        print(f"RUN {i+1}/{args.runs}: {config['label']}")
        print(f"  Args: {' '.join(config['args'])}")
        print(f"{'─'*60}")

        # Step 1: Run simulation directly
        sim_cmd = [
            sys.executable,
            os.path.join(PROJECT_ROOT, "main.py"),
        ] + config["args"]
        print(f"  Running simulation...")
        try:
            sim_result = subprocess.run(sim_cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=900)
        except subprocess.TimeoutExpired:
            print(f"  SIMULATION TIMED OUT after 900s")
            results.append({"run": i+1, "config": config["label"], "status": "TIMEOUT"})
            continue
        if sim_result.returncode != 0:
            print(f"  SIMULATION FAILED: {sim_result.stderr[-200:]}")
            results.append({"run": i+1, "config": config["label"], "status": "CRASHED", "error": sim_result.stderr[-200:]})
            continue
        print(f"  Simulation complete. Evaluating...")

        # Step 2: Run eval on the newest output (skip-run mode, no extra args to conflict)
        eval_cmd = [
            sys.executable,
            os.path.join(PROJECT_ROOT, "evals", "run_and_evaluate.py"),
            "--skip-run",
        ]

        try:
            eval_result = subprocess.run(eval_cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=1200)
        except subprocess.TimeoutExpired:
            print(f"  TIMED OUT after 1200s")
            results.append({"run": i+1, "config": config["label"], "status": "TIMEOUT"})
            continue

        if eval_result.returncode != 0:
            print(f"  EVAL FAILED: {eval_result.stderr[-200:]}")
            results.append({"run": i+1, "config": config["label"], "status": "EVAL_FAILED", "error": eval_result.stderr[-200:]})
            continue

        # Parse eval output for key metrics
        output = eval_result.stdout
        print(output[-1500:])  # Print last portion

        # Try to find the newest eval_report.json
        try:
            from evals.run_and_evaluate import find_newest_run
            newest = find_newest_run(os.path.join(PROJECT_ROOT, "output"))
            report_path = os.path.join(newest, "eval_report.json")
            if os.path.exists(report_path):
                with open(report_path) as f:
                    report = json.load(f)
                results.append({
                    "run": i+1,
                    "config": config["label"],
                    "status": "OK",
                    "settlement": report.get("run", "?"),
                    "bugs": report.get("bugs_found", 0),
                    "avg_score": report.get("average_score", 0),
                    "scores": report.get("scores", {}),
                    "summary": report.get("summary", "")[:200],
                })
            else:
                results.append({"run": i+1, "config": config["label"], "status": "NO_REPORT"})
        except Exception as e:
            results.append({"run": i+1, "config": config["label"], "status": "PARSE_ERROR", "error": str(e)})

    # ── Batch Summary ────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"BATCH SUMMARY: {args.runs} runs")
    print(f"{'='*60}\n")

    ok_runs = [r for r in results if r.get("status") == "OK"]
    failed_runs = [r for r in results if r.get("status") != "OK"]

    if ok_runs:
        avg_bugs = sum(r["bugs"] for r in ok_runs) / len(ok_runs)
        avg_score = sum(r["avg_score"] for r in ok_runs) / len(ok_runs) if any(r.get("avg_score") for r in ok_runs) else 0

        print(f"Successful: {len(ok_runs)}/{args.runs}")
        print(f"Average bugs: {avg_bugs:.1f}")
        if avg_score:
            print(f"Average score: {avg_score:.1f}/10")
        print()

        for r in ok_runs:
            scores = r.get("scores", {})
            score_str = " ".join(f"{k[:3]}={v}" for k, v in scores.items()) if scores else "no scores"
            print(f"  [{r['config']:15s}] {r['settlement']:30s} bugs={r['bugs']:3d} {score_str}")

    if failed_runs:
        print(f"\nFailed: {len(failed_runs)}/{args.runs}")
        for r in failed_runs:
            print(f"  [{r['config']:15s}] {r['status']}: {r.get('error', '')[:60]}")

    # Check buglist for systemic issues
    buglist_path = os.path.join(PROJECT_ROOT, "evals", "buglist.json")
    if os.path.exists(buglist_path):
        with open(buglist_path) as f:
            all_bugs = json.load(f)
        if all_bugs:
            from collections import Counter
            systemic = Counter(b["bug_type"] for b in all_bugs)
            print(f"\nSYSTEMIC BUGS (across all runs ever):")
            for bug_type, count in systemic.most_common(5):
                print(f"  {bug_type}: {count} occurrences")

    # Save batch report
    avg_bugs_final = avg_bugs if ok_runs else 0
    avg_score_final = avg_score if ok_runs else 0
    batch_report = {
        "timestamp": datetime.now().isoformat(),
        "runs_attempted": args.runs,
        "runs_succeeded": len(ok_runs),
        "average_bugs": avg_bugs_final,
        "average_score": avg_score_final,
        "results": results,
    }
    batch_path = os.path.join(PROJECT_ROOT, "evals", f"batch_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
    with open(batch_path, "w") as f:
        json.dump(batch_report, f, indent=2)
    print(f"\nBatch report: {batch_path}")


if __name__ == "__main__":
    main()
