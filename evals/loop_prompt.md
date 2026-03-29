# Demesne Evaluation Loop

Run `python evals/run_and_evaluate.py` and review the output.

## After each run:

1. Read `eval_report.json` from the newest output folder
2. Report in this format:
   ```
   RUN: [settlement name]
   SCORES: drama=[N] culture=[N] factions=[N] coherence=[N] seeds=[N] AVG=[N]
   BUGS: [count] ([types])
   SUMMARY: [2 paragraphs from report]
   TOP ISSUE: [most impactful recommendation]
   ```
3. Check `evals/buglist.json` for recurring patterns
4. If a bug type appears 3+ times, flag it as SYSTEMIC and describe the pattern
5. If average score is below 6, suggest specific prompt improvements referencing the relevant agent file and method

## Rules:

- Do NOT modify game code during the loop
- Only observe, analyze, and report
- If the simulation crashes, report the error and continue to the next run
- Each loop iteration should take ~10-15 minutes (simulation + LLM eval)

## Running variations:

To test different configurations, modify the eval command:
```bash
# High churn test
python evals/run_and_evaluate.py --eras 8 --factions 3 --difficulty 14

# Large faction test
python evals/run_and_evaluate.py --eras 6 --factions 6

# Analyze existing run without re-running
python evals/run_and_evaluate.py --skip-run --run-dir output/FOLDER_NAME
```
