#!/usr/bin/env python3
"""
DAX Bench Solver v3 - Dual-Tier Feedback Strategy
Tier 1: Basic feedback (first 5 iterations)
Tier 2: Enhanced feedback with hints (next 5 iterations)
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
TIER1_ITERATIONS = 5  # Basic feedback
TIER2_ITERATIONS = 5  # Enhanced feedback
MAX_ITERATIONS = TIER1_ITERATIONS + TIER2_ITERATIONS
TASKS_DIR = Path(__file__).parent / "tasks"
RUNS_DIR = Path(__file__).parent / "runs"

def load_all_tasks():
    """Load all task JSON files"""
    tasks = []
    for level in ["basic", "intermediate", "advanced"]:
        level_dir = TASKS_DIR / level
        if level_dir.exists():
            for task_file in sorted(level_dir.glob("task-*.json")):
                with open(task_file, "r", encoding="utf-8") as f:
                    task = json.load(f)
                    task["_level"] = level
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
    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
        elapsed = time.time() - start_time
        if response.status_code != 200:
            return None, {"error": response.text, "elapsed": elapsed}
        return response.json(), {"elapsed": elapsed}
    except Exception as e:
        return None, {"error": str(e), "elapsed": time.time() - start_time}

def extract_dax(response_text):
    """Extract DAX code from model response"""
    code_match = re.search(r'```(?:dax)?\s*(.*?)```', response_text, re.DOTALL | re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()
    measure_match = re.search(r'(\[?\w+[\w\s]*\]?\s*=\s*.+)', response_text, re.DOTALL)
    if measure_match:
        return measure_match.group(1).strip()
    return response_text.strip()

def parse_measure(dax):
    """Parse measure name and expression"""
    match = re.match(r'\[?([^\]=]+)\]?\s*=\s*(.+)', dax, re.DOTALL)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None

def normalize_dax(dax):
    """Normalize DAX for comparison"""
    dax = re.sub(r'\s+', ' ', dax).strip()
    dax = dax.replace("'", "'").replace("'", "'")
    return dax.lower()

def validate_dax(generated, expected, alternatives):
    """Check if generated DAX matches expected or alternatives"""
    gen_norm = normalize_dax(generated)

    if normalize_dax(expected) == gen_norm:
        return True, "exact_match"

    for alt in alternatives:
        if normalize_dax(alt) == gen_norm:
            return True, "alternative_match"

    # Expression-level matching
    gen_name, gen_expr = parse_measure(generated)
    exp_name, exp_expr = parse_measure(expected)

    if gen_expr and exp_expr:
        if normalize_dax(gen_expr) == normalize_dax(exp_expr):
            return True, "expression_match"

    for alt in alternatives:
        alt_name, alt_expr = parse_measure(alt)
        if alt_expr and gen_expr:
            if normalize_dax(gen_expr) == normalize_dax(alt_expr):
                return True, "alt_expression_match"

    return False, "no_match"

def generate_basic_feedback(task, generated_dax, iteration):
    """Tier 1: Simple, non-prescriptive feedback"""
    return f"Your DAX doesn't produce the expected result. Please review and try again. (Attempt {iteration}/{MAX_ITERATIONS})"

def generate_enhanced_feedback(task, generated_dax, iteration):
    """Tier 2: Detailed feedback with hints"""
    feedback_parts = []

    name, expr = parse_measure(generated_dax)
    expected_dax = task["expectedOutput"]["dax"]
    expected_name, expected_expr = parse_measure(expected_dax)

    # Check for missing key functions
    key_functions = ["SUM", "CALCULATE", "FILTER", "ALL", "DIVIDE", "SUMX", "AVERAGEX",
                    "TOTALYTD", "DATESYTD", "SAMEPERIODLASTYEAR", "DISTINCTCOUNT",
                    "RANKX", "TOPN", "VALUES", "TREATAS", "EARLIER", "ALLEXCEPT",
                    "KEEPFILTERS", "SUMMARIZE", "ADDCOLUMNS", "SELECTCOLUMNS",
                    "DATESINPERIOD", "DATEADD", "PERCENTILEX.INC"]

    if expr and expected_expr:
        expected_funcs = [f for f in key_functions if f.upper() in expected_expr.upper()]
        generated_funcs = [f for f in key_functions if f.upper() in (expr.upper() if expr else "")]

        missing_funcs = set(expected_funcs) - set(generated_funcs)
        if missing_funcs:
            feedback_parts.append(f"HINT: Consider using: {', '.join(missing_funcs)}")

    # Add task hints if available
    if "hints" in task and task["hints"]:
        feedback_parts.append("Additional hints:")
        for hint in task["hints"][:2]:
            feedback_parts.append(f"  - {hint}")

    # Show expected pattern structure (not the full answer)
    if expected_expr:
        # Extract just the main function pattern
        main_func_match = re.match(r'(\w+)\s*\(', expected_expr)
        if main_func_match:
            feedback_parts.append(f"The solution starts with {main_func_match.group(1)}()")

    feedback_parts.append(f"\nThis is attempt {iteration}/{MAX_ITERATIONS} (Enhanced feedback mode)")

    return "\n".join(feedback_parts) if feedback_parts else f"Please try a different approach. (Attempt {iteration}/{MAX_ITERATIONS})"

def solve_task(task, model):
    """Solve task with dual-tier feedback strategy"""
    results = {
        "task_id": task["id"],
        "title": task["title"],
        "complexity": task["complexity"],
        "category": task["category"],
        "model": model,
        "iterations": [],
        "solved": False,
        "first_try": False,
        "solved_in_tier": None,
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
        # Determine which tier we're in
        current_tier = 1 if iteration <= TIER1_ITERATIONS else 2

        iter_result = {
            "iteration": iteration,
            "tier": current_tier
        }

        response, meta = call_openrouter(model, messages)
        iter_result["time"] = meta.get("elapsed", 0)
        results["total_time"] += iter_result["time"]

        if response is None:
            iter_result["error"] = meta.get("error", "Unknown error")
            iter_result["success"] = False
            results["iterations"].append(iter_result)
            messages.append({"role": "assistant", "content": "[Error]"})
            messages.append({"role": "user", "content": f"API error. Please try again."})
            continue

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
            results["solved_in_tier"] = current_tier
            if iteration == 1:
                results["first_try"] = True
            results["iterations"].append(iter_result)
            break
        else:
            iter_result["success"] = False

            # Generate appropriate feedback based on tier
            if current_tier == 1:
                feedback = generate_basic_feedback(task, dax, iteration)
                iter_result["feedback_tier"] = "basic"
            else:
                feedback = generate_enhanced_feedback(task, dax, iteration)
                iter_result["feedback_tier"] = "enhanced"

            iter_result["feedback"] = feedback
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": feedback})
            results["iterations"].append(iter_result)

            # Add tier transition message
            if iteration == TIER1_ITERATIONS:
                transition_msg = "Switching to enhanced feedback mode with additional hints..."
                messages.append({"role": "user", "content": transition_msg})

    results["iteration_count"] = len(results["iterations"])
    return results

def generate_task_log(result, timestamp):
    """Generate markdown log"""
    status = "✅ SOLVED" if result["solved"] else "❌ FAILED"
    tier_info = f" (Tier {result['solved_in_tier']})" if result.get("solved_in_tier") else ""

    log = f"""# DAX Bench Run Log (v3 - Dual Tier)

## Run Information
| Field | Value |
|-------|-------|
| **Task** | {result['task_id']} - {result['title']} |
| **Model** | {result['model']} |
| **Timestamp** | {timestamp} |
| **Result** | {status} in {result['iteration_count']} iteration(s){tier_info} |

## Task Details
- **Complexity**: {result['complexity']}
- **Category**: {result['category']}

## Feedback Strategy
- **Tier 1** (iterations 1-{TIER1_ITERATIONS}): Basic feedback
- **Tier 2** (iterations {TIER1_ITERATIONS+1}-{MAX_ITERATIONS}): Enhanced feedback with hints

---

## Iterations

"""

    for iter_data in result["iterations"]:
        i = iter_data["iteration"]
        tier = iter_data.get("tier", 1)
        tier_label = "Basic" if tier == 1 else "Enhanced"

        log += f"### Iteration {i} [{tier_label} Feedback]\n\n"

        if "error" in iter_data:
            log += f"**Error**: {iter_data['error']}\n\n"
        else:
            log += f"**Tokens**: {iter_data.get('input_tokens', 0)} in, {iter_data.get('output_tokens', 0)} out\n\n"
            log += f"**Generated DAX**:\n```dax\n{iter_data.get('extracted_dax', 'N/A')}\n```\n\n"

            if iter_data.get('success'):
                log += f"**Result**: ✅ PASSED ({iter_data.get('match_type')})\n\n"
            else:
                log += f"**Result**: ❌ Failed\n\n"
                if iter_data.get('feedback'):
                    log += f"**Feedback sent**:\n```\n{iter_data['feedback']}\n```\n\n"

        log += "---\n\n"

    log += f"""## Summary

| Metric | Value |
|--------|-------|
| **Total Iterations** | {result['iteration_count']} |
| **Solved In Tier** | {result.get('solved_in_tier', 'N/A')} |
| **First Try** | {'✅' if result.get('first_try') else '❌'} |
| **Tokens** | {result['total_input_tokens']:,} in / {result['total_output_tokens']:,} out |
| **Cost** | ${result['total_cost']:.6f} |
| **Time** | {result['total_time']:.2f}s |
"""

    if result.get("final_dax"):
        log += f"""
## Final DAX
```dax
{result['final_dax']}
```
"""

    return log

def generate_summary_report(all_results, model, timestamp):
    """Generate summary report"""
    total = len(all_results)
    solved = sum(1 for r in all_results if r["solved"])
    first_try = sum(1 for r in all_results if r.get("first_try"))
    tier1_solved = sum(1 for r in all_results if r.get("solved_in_tier") == 1)
    tier2_solved = sum(1 for r in all_results if r.get("solved_in_tier") == 2)
    total_iters = sum(r["iteration_count"] for r in all_results)
    total_cost = sum(r["total_cost"] for r in all_results)
    total_time = sum(r["total_time"] for r in all_results)

    report = f"""# DAX Bench Report (v3 - Dual Tier Feedback)

## Configuration
| Setting | Value |
|---------|-------|
| **Model** | {model} |
| **Timestamp** | {timestamp} |
| **Tier 1** | {TIER1_ITERATIONS} iterations (basic feedback) |
| **Tier 2** | {TIER2_ITERATIONS} iterations (enhanced feedback) |
| **Max Total** | {MAX_ITERATIONS} iterations |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | {solved}/{total} ({100*solved/total:.1f}%) |
| **First-Try Success** | {first_try}/{total} ({100*first_try/total:.1f}%) |
| **Solved in Tier 1** | {tier1_solved}/{total} ({100*tier1_solved/total:.1f}%) |
| **Solved in Tier 2** | {tier2_solved}/{total} ({100*tier2_solved/total:.1f}%) |
| **Total Iterations** | {total_iters} |
| **Avg Iterations** | {total_iters/total:.2f} |
| **Total Cost** | ${total_cost:.4f} |
| **Total Time** | {total_time:.1f}s ({total_time/60:.1f}m) |

---

## Tier Analysis

The dual-tier approach uses:
- **Tier 1**: Simple "try again" feedback - lets model explore freely
- **Tier 2**: Function hints and tips - helps when stuck

| Tier | Solved | % of Total Solves |
|------|--------|-------------------|
| First Try | {first_try} | {100*first_try/max(solved,1):.0f}% |
| Tier 1 (2-{TIER1_ITERATIONS}) | {tier1_solved - first_try} | {100*(tier1_solved-first_try)/max(solved,1):.0f}% |
| Tier 2 ({TIER1_ITERATIONS+1}-{MAX_ITERATIONS}) | {tier2_solved} | {100*tier2_solved/max(solved,1):.0f}% |

---

## Results by Complexity

| Complexity | Solved | Tier 1 | Tier 2 | Failed |
|------------|--------|--------|--------|--------|
"""

    for level in ["basic", "intermediate", "advanced"]:
        level_results = [r for r in all_results if r["complexity"] == level]
        if level_results:
            l_solved = sum(1 for r in level_results if r["solved"])
            l_t1 = sum(1 for r in level_results if r.get("solved_in_tier") == 1)
            l_t2 = sum(1 for r in level_results if r.get("solved_in_tier") == 2)
            l_fail = len(level_results) - l_solved
            report += f"| {level.capitalize()} | {l_solved}/{len(level_results)} | {l_t1} | {l_t2} | {l_fail} |\n"

    report += """
---

## Per-Task Results

| Task | Complexity | Solved | Tier | Iters | Cost |
|------|------------|--------|------|-------|------|
"""

    for r in all_results:
        status = "✅" if r["solved"] else "❌"
        tier = r.get("solved_in_tier", "-")
        report += f"| {r['task_id']} | {r['complexity']} | {status} | {tier} | {r['iteration_count']} | ${r['total_cost']:.4f} |\n"

    report += """
---

## Failed Tasks

"""
    failed = [r for r in all_results if not r["solved"]]
    if failed:
        for r in failed:
            report += f"- **{r['task_id']}**: {r['title']} ({r['category']})\n"
    else:
        report += "*All tasks solved!*\n"

    return report

def main():
    if not API_KEY:
        print("ERROR: OPENROUTER_DAXBENCH_API_KEY not set")
        return

    import sys
    model = sys.argv[1] if len(sys.argv) > 1 else "google/gemini-2.5-flash"

    print(f"DAX Bench Solver v3 - Dual Tier Feedback")
    print(f"Model: {model}")
    print(f"Tier 1: {TIER1_ITERATIONS} iters (basic) | Tier 2: {TIER2_ITERATIONS} iters (enhanced)")
    print("-" * 60)

    tasks = load_all_tasks()
    print(f"Loaded {len(tasks)} tasks\n")

    RUNS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    date_prefix = datetime.now().strftime("%Y-%m-%d_%H%M")
    model_safe = model.replace("/", "_").replace(":", "_")

    all_results = []

    for i, task in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] {task['id']}: {task['title']}")

        result = solve_task(task, model)
        all_results.append(result)

        status = "[OK]" if result["solved"] else "[FAIL]"
        tier = f"T{result['solved_in_tier']}" if result.get("solved_in_tier") else "  "
        iters = result["iteration_count"]
        first = " *" if result.get("first_try") else ""
        print(f"  {status} {tier} {iters} iter(s), ${result['total_cost']:.4f}{first}")

        log_content = generate_task_log(result, timestamp)
        log_file = RUNS_DIR / f"{date_prefix}_{task['id']}_{model_safe}_v3.md"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(log_content)

    summary = generate_summary_report(all_results, model, timestamp)
    summary_file = RUNS_DIR / f"{date_prefix}_SUMMARY_{model_safe}_v3.md"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary)

    json_file = RUNS_DIR / f"{date_prefix}_RESULTS_{model_safe}_v3.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)

    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE (v3 - Dual Tier)")
    print("=" * 60)

    solved = sum(1 for r in all_results if r["solved"])
    first_try = sum(1 for r in all_results if r.get("first_try"))
    tier1 = sum(1 for r in all_results if r.get("solved_in_tier") == 1)
    tier2 = sum(1 for r in all_results if r.get("solved_in_tier") == 2)

    print(f"Solved: {solved}/{len(tasks)} ({100*solved/len(tasks):.1f}%)")
    print(f"  - First try: {first_try}")
    print(f"  - Tier 1 (basic): {tier1}")
    print(f"  - Tier 2 (enhanced): {tier2}")
    print(f"Cost: ${sum(r['total_cost'] for r in all_results):.4f}")
    print(f"Time: {sum(r['total_time'] for r in all_results):.1f}s")
    print(f"\nSummary: {summary_file}")

if __name__ == "__main__":
    main()
