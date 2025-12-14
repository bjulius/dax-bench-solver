#!/usr/bin/env python3
"""
DAX Bench Solver - Full Benchmark Runner
Runs all 30 DAX Bench tasks against a specified model via OpenRouter
"""

import os
import json
import time
import re
import requests
from datetime import datetime
from pathlib import Path

# Configuration
API_KEY = os.environ.get("OPENROUTER_DAXBENCH_API_KEY", "")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_ITERATIONS = 10
TASKS_DIR = Path(__file__).parent / "tasks"
RUNS_DIR = Path(__file__).parent / "runs"

def load_all_tasks():
    """Load all task JSON files from tasks directory"""
    tasks = []
    for level in ["basic", "intermediate", "advanced"]:
        level_dir = TASKS_DIR / level
        if level_dir.exists():
            for task_file in sorted(level_dir.glob("task-*.json")):
                with open(task_file, "r") as f:
                    task = json.load(f)
                    task["_level"] = level
                    task["_file"] = str(task_file)
                    tasks.append(task)
    return tasks

def call_openrouter(model, messages):
    """Make API call to OpenRouter"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1000
    }

    start_time = time.time()
    response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
    elapsed = time.time() - start_time

    if response.status_code != 200:
        return None, {"error": response.text, "elapsed": elapsed}

    data = response.json()
    return data, {"elapsed": elapsed}

def extract_dax(response_text):
    """Extract DAX code from model response"""
    # Try to find code block first
    code_match = re.search(r'```(?:dax)?\s*(.*?)```', response_text, re.DOTALL | re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()

    # Otherwise look for measure pattern
    measure_match = re.search(r'(\[?\w+[\w\s]*\]?\s*=\s*.+)', response_text, re.DOTALL)
    if measure_match:
        return measure_match.group(1).strip()

    return response_text.strip()

def normalize_dax(dax):
    """Normalize DAX for comparison"""
    # Remove extra whitespace
    dax = re.sub(r'\s+', ' ', dax).strip()
    # Standardize quotes
    dax = dax.replace("'", "'").replace("'", "'")
    # Normalize decimal numbers: remove trailing zeros after decimal (0.90 -> 0.9)
    dax = re.sub(r'(\d+\.\d*?)0+(?=\D|$)', r'\1', dax)
    # Remove trailing decimal point (100. -> 100)
    dax = re.sub(r'(\d+)\.(?=\D|$)', r'\1', dax)
    return dax.lower()

def extract_expression(dax):
    """Extract just the expression part, stripping measure name if present.

    Handles patterns like:
    - 'Measure Name = SUM(...)'  -> 'SUM(...)'
    - '[Measure Name] = SUM(...)' -> 'SUM(...)'
    - 'SUM(...)' (no name) -> 'SUM(...)'
    - 'VAR x = ... RETURN ...' -> 'VAR x = ... RETURN ...'
    """
    dax = dax.strip()

    # Pattern: MeasureName = expression (but not VAR = which is different)
    # Look for measure name at start: word/bracket pattern followed by =
    # But NOT if it starts with VAR, IF, RETURN, CALCULATE, etc.
    dax_keywords = ['var', 'return', 'if', 'switch', 'calculate', 'sum', 'average',
                    'count', 'divide', 'max', 'min', 'filter', 'all', 'values',
                    'sumx', 'averagex', 'countx', 'maxx', 'minx', 'rankx', 'topn',
                    'earlier', 'earliest', 'blank', 'isblank', 'coalesce', 'true', 'false']

    # Extract first token (word only, strip parens/brackets)
    first_token_match = re.match(r'^[\[\"]?(\w+)', dax)
    first_word = first_token_match.group(1).lower() if first_token_match else ''

    # If starts with a DAX keyword, it's just an expression (no measure name)
    if first_word in dax_keywords:
        return dax

    # Try to find "MeasureName =" or "[Measure Name] =" at the start
    # Match: optional brackets, word chars/spaces, then = followed by space or keyword
    measure_pattern = r'^[\[\"]?[\w\s%]+[\]\"]?\s*=\s*'
    match = re.match(measure_pattern, dax, re.IGNORECASE)

    if match:
        # Make sure what follows the = is actually DAX (not another = like VAR x = 1)
        remainder = dax[match.end():].strip()
        # Extract first token from remainder
        first_after_match = re.match(r'^[\(\[]?(\w+)', remainder)
        first_after = first_after_match.group(1).lower() if first_after_match else ''
        if first_after in dax_keywords or remainder.startswith('('):
            return remainder

    return dax

def validate_dax(generated, expected, alternatives):
    """Check if generated DAX matches expected or alternatives"""
    gen_norm = normalize_dax(generated)
    exp_norm = normalize_dax(expected)

    # Check exact match first
    if exp_norm == gen_norm:
        return True, "exact_match"

    # Check alternatives exact match
    for alt in alternatives:
        if normalize_dax(alt) == gen_norm:
            return True, "alternative_match"

    # Extract expressions (strip measure names) and compare
    gen_expr = normalize_dax(extract_expression(generated))
    exp_expr = normalize_dax(extract_expression(expected))

    if gen_expr == exp_expr:
        return True, "expression_match"

    # Check alternatives with expression extraction
    for alt in alternatives:
        alt_expr = normalize_dax(extract_expression(alt))
        if gen_expr == alt_expr:
            return True, "alt_expression_match"

    # Legacy fallback: split on first = and compare RHS
    gen_parts = gen_norm.split('=', 1)
    exp_parts = exp_norm.split('=', 1)

    if len(gen_parts) == 2 and len(exp_parts) == 2:
        if gen_parts[1].strip() == exp_parts[1].strip():
            return True, "rhs_match"

    return False, "no_match"

def solve_task(task, model):
    """Attempt to solve a single task with iteration"""
    results = {
        "task_id": task["id"],
        "title": task["title"],
        "complexity": task["complexity"],
        "category": task["category"],
        "model": model,
        "iterations": [],
        "solved": False,
        "first_try": False,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cost": 0,
        "total_time": 0
    }

    messages = [
        {"role": "system", "content": task["prompt"]["system"]},
        {"role": "user", "content": f"{task['prompt']['user']}\n\nContext: {task['prompt']['dataModelContext']}"}
    ]

    for iteration in range(1, MAX_ITERATIONS + 1):
        iter_result = {"iteration": iteration}

        # Call API
        response, meta = call_openrouter(model, messages)
        iter_result["time"] = meta.get("elapsed", 0)
        results["total_time"] += iter_result["time"]

        if response is None:
            iter_result["error"] = meta.get("error", "Unknown error")
            iter_result["success"] = False
            results["iterations"].append(iter_result)
            continue

        # Extract response content
        try:
            content = response["choices"][0]["message"]["content"]
            usage = response.get("usage", {})
            iter_result["input_tokens"] = usage.get("prompt_tokens", 0)
            iter_result["output_tokens"] = usage.get("completion_tokens", 0)
            iter_result["cost"] = usage.get("cost", 0)

            results["total_input_tokens"] += iter_result["input_tokens"]
            results["total_output_tokens"] += iter_result["output_tokens"]
            results["total_cost"] += iter_result["cost"]
        except (KeyError, IndexError) as e:
            iter_result["error"] = f"Parse error: {e}"
            iter_result["success"] = False
            results["iterations"].append(iter_result)
            continue

        # Extract and validate DAX
        dax = extract_dax(content)
        iter_result["raw_response"] = content
        iter_result["extracted_dax"] = dax

        valid, match_type = validate_dax(
            dax,
            task["expectedOutput"]["dax"],
            task["expectedOutput"].get("alternativeCorrect", [])
        )

        iter_result["valid"] = valid
        iter_result["match_type"] = match_type

        if valid:
            iter_result["success"] = True
            results["solved"] = True
            results["final_dax"] = dax
            if iteration == 1:
                results["first_try"] = True
            results["iterations"].append(iter_result)
            break
        else:
            iter_result["success"] = False
            # Add feedback for next iteration
            feedback = f"Your DAX didn't match the expected pattern. Expected something like: {task['expectedOutput']['dax']}\nYou provided: {dax}\nPlease try again with the correct syntax."
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": feedback})
            results["iterations"].append(iter_result)

    results["iteration_count"] = len(results["iterations"])
    return results

def generate_task_log(result, timestamp):
    """Generate markdown log for a single task run"""
    status = "✅ SOLVED" if result["solved"] else "❌ FAILED"
    iters = result["iteration_count"]

    log = f"""# DAX Bench Run Log

## Run Information
| Field | Value |
|-------|-------|
| **Task** | {result['task_id']} - {result['title']} |
| **Model** | {result['model']} |
| **Timestamp** | {timestamp} |
| **Result** | {status} in {iters} iteration(s) |

## Task Details
- **Complexity**: {result['complexity']}
- **Category**: {result['category']}

---

## Iterations

"""

    for iter_data in result["iterations"]:
        i = iter_data["iteration"]
        log += f"### Iteration {i}\n"

        if "error" in iter_data:
            log += f"**Error**: {iter_data['error']}\n\n"
        else:
            log += f"**Token Usage**: {iter_data.get('input_tokens', 0)} input, {iter_data.get('output_tokens', 0)} output\n\n"
            log += f"**Model Response**:\n```dax\n{iter_data.get('extracted_dax', 'N/A')}\n```\n\n"
            log += f"**Validation**: {'✅ PASSED' if iter_data.get('success') else '❌ FAILED'}"
            if iter_data.get('match_type'):
                log += f" ({iter_data['match_type']})"
            log += "\n\n"

        log += "---\n\n"

    log += f"""## Summary

| Metric | Value |
|--------|-------|
| **Total Iterations** | {result['iteration_count']} |
| **First Try Success** | {'✅ Yes' if result.get('first_try') else '❌ No'} |
| **Input Tokens** | {result['total_input_tokens']} |
| **Output Tokens** | {result['total_output_tokens']} |
| **Total Cost** | ${result['total_cost']:.6f} |
| **Total Time** | {result['total_time']:.2f}s |

"""

    if result.get("final_dax"):
        log += f"""## Final DAX
```dax
{result['final_dax']}
```
"""

    return log

def generate_summary_report(all_results, model, timestamp):
    """Generate summary report for full benchmark run"""
    total_tasks = len(all_results)
    solved = sum(1 for r in all_results if r["solved"])
    first_try = sum(1 for r in all_results if r.get("first_try"))
    total_iters = sum(r["iteration_count"] for r in all_results)
    total_input = sum(r["total_input_tokens"] for r in all_results)
    total_output = sum(r["total_output_tokens"] for r in all_results)
    total_cost = sum(r["total_cost"] for r in all_results)
    total_time = sum(r["total_time"] for r in all_results)

    report = f"""# DAX Bench Full Benchmark Report

## Run Information
| Field | Value |
|-------|-------|
| **Model** | {model} |
| **Timestamp** | {timestamp} |
| **Tasks Run** | {total_tasks} |
| **Max Iterations** | {MAX_ITERATIONS} |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | {solved}/{total_tasks} ({100*solved/total_tasks:.1f}%) |
| **First-Try Success** | {first_try}/{total_tasks} ({100*first_try/total_tasks:.1f}%) |
| **Total Iterations** | {total_iters} |
| **Avg Iterations/Task** | {total_iters/total_tasks:.2f} |
| **Total Input Tokens** | {total_input:,} |
| **Total Output Tokens** | {total_output:,} |
| **Total Tokens** | {total_input + total_output:,} |
| **Total Cost** | ${total_cost:.4f} |
| **Cost per Task** | ${total_cost/total_tasks:.6f} |
| **Total Time** | {total_time:.1f}s ({total_time/60:.1f}m) |
| **Avg Time/Task** | {total_time/total_tasks:.2f}s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
"""

    for level in ["basic", "intermediate", "advanced"]:
        level_results = [r for r in all_results if r["complexity"] == level]
        if level_results:
            l_solved = sum(1 for r in level_results if r["solved"])
            l_first = sum(1 for r in level_results if r.get("first_try"))
            l_iters = sum(r["iteration_count"] for r in level_results) / len(level_results)
            report += f"| {level.capitalize()} | {l_solved}/{len(level_results)} | {l_first}/{len(level_results)} | {l_iters:.2f} |\n"

    report += """
---

## Per-Task Results

| Task | Complexity | Category | Solved | Iters | Cost |
|------|------------|----------|--------|-------|------|
"""

    for r in all_results:
        status = "✅" if r["solved"] else "❌"
        report += f"| {r['task_id']} | {r['complexity']} | {r['category']} | {status} | {r['iteration_count']} | ${r['total_cost']:.4f} |\n"

    report += """
---

## Failed Tasks (if any)

"""

    failed = [r for r in all_results if not r["solved"]]
    if failed:
        for r in failed:
            report += f"- **{r['task_id']}**: {r['title']} ({r['complexity']})\n"
    else:
        report += "*All tasks solved successfully!*\n"

    return report

def main():
    if not API_KEY:
        print("ERROR: OPENROUTER_DAXBENCH_API_KEY not set")
        return

    # Get model from command line or use default
    import sys
    model = sys.argv[1] if len(sys.argv) > 1 else "google/gemini-2.5-flash"

    print(f"DAX Bench Solver - Full Benchmark")
    print(f"Model: {model}")
    print(f"Max Iterations: {MAX_ITERATIONS}")
    print("-" * 50)

    # Load tasks
    tasks = load_all_tasks()
    print(f"Loaded {len(tasks)} tasks")

    # Ensure runs directory exists
    RUNS_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    date_prefix = datetime.now().strftime("%Y-%m-%d_%H%M")
    model_safe = model.replace("/", "_").replace(":", "_")

    all_results = []

    for i, task in enumerate(tasks, 1):
        print(f"\n[{i}/{len(tasks)}] {task['id']}: {task['title']} ({task['complexity']})")

        result = solve_task(task, model)
        all_results.append(result)

        status = "[OK]" if result["solved"] else "[FAIL]"
        iters = result["iteration_count"]
        cost = result["total_cost"]
        print(f"  {status} {'Solved' if result['solved'] else 'Failed'} in {iters} iter(s), ${cost:.4f}")

        # Write individual log
        log_content = generate_task_log(result, timestamp)
        log_file = RUNS_DIR / f"{date_prefix}_{task['id']}_{model_safe}.md"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(log_content)

    # Write summary report
    summary = generate_summary_report(all_results, model, timestamp)
    summary_file = RUNS_DIR / f"{date_prefix}_SUMMARY_{model_safe}.md"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary)

    print("\n" + "=" * 50)
    print("BENCHMARK COMPLETE")
    print("=" * 50)

    solved = sum(1 for r in all_results if r["solved"])
    first_try = sum(1 for r in all_results if r.get("first_try"))
    total_cost = sum(r["total_cost"] for r in all_results)
    total_time = sum(r["total_time"] for r in all_results)

    print(f"Solved: {solved}/{len(tasks)} ({100*solved/len(tasks):.1f}%)")
    print(f"First-Try: {first_try}/{len(tasks)} ({100*first_try/len(tasks):.1f}%)")
    print(f"Total Cost: ${total_cost:.4f}")
    print(f"Total Time: {total_time:.1f}s")
    print(f"\nSummary: {summary_file}")

if __name__ == "__main__":
    main()
