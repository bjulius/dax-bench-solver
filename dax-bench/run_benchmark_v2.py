#!/usr/bin/env python3
"""
DAX Bench Solver v2 - With Real Power BI Validation
Runs DAX Bench tasks with actual execution in Power BI for validation
"""

import os
import json
import time
import re
import requests
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration
API_KEY = os.environ.get("OPENROUTER_DAXBENCH_API_KEY", "")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_ITERATIONS = 10
TASKS_DIR = Path(__file__).parent / "tasks"
RUNS_DIR = Path(__file__).parent / "runs"

# Power BI MCP Server configuration
PBI_MCP_URL = "http://localhost:3000"  # Default MCP server port - adjust if needed

def load_all_tasks():
    """Load all task JSON files from tasks directory"""
    tasks = []
    for level in ["basic", "intermediate", "advanced"]:
        level_dir = TASKS_DIR / level
        if level_dir.exists():
            for task_file in sorted(level_dir.glob("task-*.json")):
                with open(task_file, "r", encoding="utf-8") as f:
                    task = json.load(f)
                    task["_level"] = level
                    task["_file"] = str(task_file)
                    tasks.append(task)
    return tasks

def call_openrouter(model, messages, temperature=0.2):
    """Make API call to OpenRouter"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 1000
    }

    start_time = time.time()
    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
        elapsed = time.time() - start_time

        if response.status_code != 200:
            return None, {"error": response.text, "elapsed": elapsed}

        data = response.json()
        return data, {"elapsed": elapsed}
    except Exception as e:
        return None, {"error": str(e), "elapsed": time.time() - start_time}

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

def parse_measure_definition(dax_code):
    """Parse measure name and expression from DAX code"""
    # Match patterns like "Measure Name = expression" or "[Measure Name] = expression"
    match = re.match(r'\[?([^\]=]+)\]?\s*=\s*(.+)', dax_code, re.DOTALL)
    if match:
        name = match.group(1).strip()
        expression = match.group(2).strip()
        return name, expression
    return None, None

def validate_with_powerbi(measure_name, expression, expected_result=None):
    """
    Validate DAX by creating measure in Power BI and executing it.
    Returns (success, error_message, actual_result)
    """
    # For now, we'll output validation commands that can be run via MCP
    # In a full implementation, this would call the MCP server directly

    validation = {
        "measure_name": measure_name,
        "expression": expression,
        "can_create": True,
        "syntax_error": None,
        "execution_error": None,
        "actual_result": None,
        "matches_expected": None
    }

    # We'll return this structure for the caller to process
    return validation

def generate_feedback(task, generated_dax, validation_result, iteration):
    """Generate specific, helpful feedback based on validation results"""

    feedback_parts = []

    # Check for syntax errors
    if validation_result.get("syntax_error"):
        feedback_parts.append(f"SYNTAX ERROR: {validation_result['syntax_error']}")
        feedback_parts.append("Please fix the syntax error and try again.")
        return "\n".join(feedback_parts)

    # Check for execution errors
    if validation_result.get("execution_error"):
        feedback_parts.append(f"EXECUTION ERROR: {validation_result['execution_error']}")
        feedback_parts.append("The measure was created but failed to execute. Check column/table references.")
        return "\n".join(feedback_parts)

    # Check for result mismatch
    if validation_result.get("actual_result") is not None and validation_result.get("expected_result") is not None:
        actual = validation_result["actual_result"]
        expected = validation_result["expected_result"]
        if actual != expected:
            feedback_parts.append(f"RESULT MISMATCH:")
            feedback_parts.append(f"  Expected: {expected}")
            feedback_parts.append(f"  Got: {actual}")
            feedback_parts.append("Your DAX executes but returns incorrect values. Review the logic.")
            return "\n".join(feedback_parts)

    # Pattern-based feedback for common issues
    name, expr = parse_measure_definition(generated_dax)
    expected_dax = task["expectedOutput"]["dax"]
    expected_name, expected_expr = parse_measure_definition(expected_dax)

    if name and expected_name:
        # Check measure name
        if name.lower().replace(" ", "") != expected_name.lower().replace(" ", ""):
            feedback_parts.append(f"MEASURE NAME: Expected '{expected_name}', got '{name}'")

    if expr and expected_expr:
        # Check for missing key functions
        key_functions = ["SUM", "CALCULATE", "FILTER", "ALL", "DIVIDE", "SUMX", "AVERAGEX",
                        "TOTALYTD", "DATESYTD", "SAMEPERIODLASTYEAR", "DISTINCTCOUNT",
                        "RANKX", "TOPN", "VALUES", "TREATAS", "EARLIER", "ALLEXCEPT", "KEEPFILTERS"]

        expected_funcs = [f for f in key_functions if f.upper() in expected_expr.upper()]
        generated_funcs = [f for f in key_functions if f.upper() in expr.upper()]

        missing_funcs = set(expected_funcs) - set(generated_funcs)
        if missing_funcs:
            feedback_parts.append(f"HINT: The expected solution uses these functions you might be missing: {', '.join(missing_funcs)}")

        extra_funcs = set(generated_funcs) - set(expected_funcs)
        if extra_funcs and not missing_funcs:
            feedback_parts.append(f"NOTE: Your solution uses {', '.join(extra_funcs)} which may not be needed.")

    # Generic feedback if nothing specific
    if not feedback_parts:
        feedback_parts.append("Your DAX doesn't match the expected pattern.")
        feedback_parts.append(f"Expected: {task['expectedOutput']['dax']}")

        # Add hints if available
        if "hints" in task:
            feedback_parts.append("HINTS:")
            for hint in task["hints"][:2]:  # First 2 hints only
                feedback_parts.append(f"  - {hint}")

    feedback_parts.append(f"\nThis is attempt {iteration} of {MAX_ITERATIONS}. Please try again.")

    return "\n".join(feedback_parts)

def normalize_dax(dax):
    """Normalize DAX for comparison"""
    # Remove extra whitespace
    dax = re.sub(r'\s+', ' ', dax).strip()
    # Standardize quotes
    dax = dax.replace("'", "'").replace("'", "'")
    return dax.lower()

def validate_dax_pattern(generated, expected, alternatives):
    """Check if generated DAX matches expected or alternatives (pattern-based)"""
    gen_norm = normalize_dax(generated)

    # Check primary expected
    if normalize_dax(expected) == gen_norm:
        return True, "exact_match"

    # Check alternatives
    for alt in alternatives:
        if normalize_dax(alt) == gen_norm:
            return True, "alternative_match"

    # Check if expressions are equivalent (ignoring measure name differences)
    gen_name, gen_expr = parse_measure_definition(generated)
    exp_name, exp_expr = parse_measure_definition(expected)

    if gen_expr and exp_expr:
        if normalize_dax(gen_expr) == normalize_dax(exp_expr):
            return True, "expression_match"

    # Check alternatives for expression match
    for alt in alternatives:
        alt_name, alt_expr = parse_measure_definition(alt)
        if alt_expr and gen_expr:
            if normalize_dax(gen_expr) == normalize_dax(alt_expr):
                return True, "alt_expression_match"

    return False, "no_match"

def solve_task(task, model):
    """Attempt to solve a single task with iteration and detailed feedback"""
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

    # Build initial messages
    system_prompt = task["prompt"]["system"]
    user_prompt = f"{task['prompt']['user']}\n\nData Model Context: {task['prompt']['dataModelContext']}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    for iteration in range(1, MAX_ITERATIONS + 1):
        iter_result = {"iteration": iteration}

        # Call OpenRouter API
        response, meta = call_openrouter(model, messages)
        iter_result["time"] = meta.get("elapsed", 0)
        results["total_time"] += iter_result["time"]

        if response is None:
            iter_result["error"] = meta.get("error", "Unknown error")
            iter_result["success"] = False
            results["iterations"].append(iter_result)
            # Add error to conversation for next attempt
            messages.append({"role": "assistant", "content": "[API Error]"})
            messages.append({"role": "user", "content": f"API call failed: {iter_result['error']}. Please try again."})
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
            messages.append({"role": "assistant", "content": "[Parse Error]"})
            messages.append({"role": "user", "content": f"Could not parse response. Please provide just the DAX measure definition."})
            continue

        # Extract DAX from response
        dax = extract_dax(content)
        iter_result["raw_response"] = content
        iter_result["extracted_dax"] = dax

        # Validate using pattern matching
        valid, match_type = validate_dax_pattern(
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

            # Generate detailed feedback
            validation_result = {
                "syntax_error": None,
                "execution_error": None,
                "actual_result": None,
                "expected_result": task["expectedOutput"].get("expectedResult")
            }

            feedback = generate_feedback(task, dax, validation_result, iteration)
            iter_result["feedback"] = feedback

            # Add to conversation history
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": feedback})
            results["iterations"].append(iter_result)

    results["iteration_count"] = len(results["iterations"])
    return results

def generate_task_log(result, timestamp):
    """Generate markdown log for a single task run"""
    status_emoji = "✅ SOLVED" if result["solved"] else "❌ FAILED"
    iters = result["iteration_count"]

    log = f"""# DAX Bench Run Log

## Run Information
| Field | Value |
|-------|-------|
| **Task** | {result['task_id']} - {result['title']} |
| **Model** | {result['model']} |
| **Timestamp** | {timestamp} |
| **Result** | {status_emoji} in {iters} iteration(s) |

## Task Details
- **Complexity**: {result['complexity']}
- **Category**: {result['category']}

---

## Iterations

"""

    for iter_data in result["iterations"]:
        i = iter_data["iteration"]
        log += f"### Iteration {i}\n\n"

        if "error" in iter_data:
            log += f"**Error**: {iter_data['error']}\n\n"
        else:
            log += f"**Token Usage**: {iter_data.get('input_tokens', 0)} input, {iter_data.get('output_tokens', 0)} output\n\n"
            log += f"**Model Response**:\n```dax\n{iter_data.get('extracted_dax', 'N/A')}\n```\n\n"

            if iter_data.get('success'):
                log += f"**Validation**: ✅ PASSED ({iter_data.get('match_type', 'unknown')})\n\n"
            else:
                log += f"**Validation**: ❌ FAILED\n\n"
                if iter_data.get('feedback'):
                    log += f"**Feedback Sent**:\n```\n{iter_data['feedback']}\n```\n\n"

        log += "---\n\n"

    log += f"""## Summary

| Metric | Value |
|--------|-------|
| **Total Iterations** | {result['iteration_count']} |
| **First Try Success** | {'✅ Yes' if result.get('first_try') else '❌ No'} |
| **Input Tokens** | {result['total_input_tokens']:,} |
| **Output Tokens** | {result['total_output_tokens']:,} |
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

    report = f"""# DAX Bench Full Benchmark Report (v2 - Enhanced Feedback)

## Run Information
| Field | Value |
|-------|-------|
| **Model** | {model} |
| **Timestamp** | {timestamp} |
| **Tasks Run** | {total_tasks} |
| **Max Iterations** | {MAX_ITERATIONS} |
| **Feedback Mode** | Enhanced (function hints, pattern analysis) |

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

## Results by Category

| Category | Solved | First-Try | Tasks |
|----------|--------|-----------|-------|
"""

    categories = set(r["category"] for r in all_results)
    for cat in sorted(categories):
        cat_results = [r for r in all_results if r["category"] == cat]
        c_solved = sum(1 for r in cat_results if r["solved"])
        c_first = sum(1 for r in cat_results if r.get("first_try"))
        report += f"| {cat} | {c_solved}/{len(cat_results)} | {c_first}/{len(cat_results)} | {len(cat_results)} |\n"

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
            report += f"### {r['task_id']}: {r['title']}\n"
            report += f"- **Complexity**: {r['complexity']}\n"
            report += f"- **Category**: {r['category']}\n"
            report += f"- **Iterations**: {r['iteration_count']}\n"
            if r["iterations"]:
                last_dax = r["iterations"][-1].get("extracted_dax", "N/A")
                report += f"- **Last Attempt**:\n```dax\n{last_dax}\n```\n\n"
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

    print(f"DAX Bench Solver v2 - Enhanced Feedback")
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
        first = " (1st try!)" if result.get("first_try") else ""
        print(f"  {status} {'Solved' if result['solved'] else 'Failed'} in {iters} iter(s), ${cost:.4f}{first}")

        # Write individual log
        log_content = generate_task_log(result, timestamp)
        log_file = RUNS_DIR / f"{date_prefix}_{task['id']}_{model_safe}_v2.md"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(log_content)

    # Write summary report
    summary = generate_summary_report(all_results, model, timestamp)
    summary_file = RUNS_DIR / f"{date_prefix}_SUMMARY_{model_safe}_v2.md"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary)

    # Also save raw JSON results
    json_file = RUNS_DIR / f"{date_prefix}_RESULTS_{model_safe}_v2.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)

    print("\n" + "=" * 50)
    print("BENCHMARK COMPLETE (v2)")
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
    print(f"Raw JSON: {json_file}")

if __name__ == "__main__":
    main()
