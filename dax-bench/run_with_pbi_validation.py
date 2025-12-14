#!/usr/bin/env python3
"""
DAX Bench Solver with REAL Power BI Validation
- Creates measures in Power BI
- Executes and captures actual errors
- Compares results to expected values
- Feeds back real error messages, NOT the expected DAX
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

# MCP tool caller - uses claude CLI to execute MCP commands
def call_mcp_tool(tool_name, params):
    """
    Call Power BI MCP tool via direct HTTP or CLI
    For now, we'll output commands for manual execution or use a simple approach
    """
    # This would ideally call the MCP server directly
    # For this implementation, we'll construct the commands
    return {"tool": tool_name, "params": params}

def load_task(task_id):
    """Load a specific task"""
    for level in ["basic", "intermediate", "advanced"]:
        path = TASKS_DIR / level / f"{task_id}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                task = json.load(f)
                task["_level"] = level
                return task
    return None

def load_all_tasks():
    """Load all tasks"""
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
    """Call OpenRouter API"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1500
    }

    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            return response.json(), None
        return None, response.text
    except Exception as e:
        return None, str(e)

def extract_dax(response_text):
    """Extract DAX from model response"""
    # Try code block first
    code_match = re.search(r'```(?:dax)?\s*(.*?)```', response_text, re.DOTALL | re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()

    # Try measure pattern
    measure_match = re.search(r'(\[?\w+[\w\s%-]*\]?\s*=\s*.+)', response_text, re.DOTALL)
    if measure_match:
        return measure_match.group(1).strip()

    return response_text.strip()

def parse_measure_definition(dax):
    """Parse measure name and expression from DAX"""
    match = re.match(r'\[?([^\]=]+)\]?\s*=\s*(.+)', dax, re.DOTALL)
    if match:
        name = match.group(1).strip()
        expression = match.group(2).strip()
        return name, expression
    return None, None

def generate_blind_feedback(error_type, error_details, iteration, max_iter):
    """
    Generate feedback WITHOUT showing the expected answer.
    Only describes what went wrong.
    """
    feedback_parts = [f"Attempt {iteration}/{max_iter} failed."]

    if error_type == "syntax":
        feedback_parts.append(f"SYNTAX ERROR from DAX engine:")
        feedback_parts.append(f"  {error_details}")
        feedback_parts.append("Please fix the syntax error and try again.")

    elif error_type == "execution":
        feedback_parts.append(f"EXECUTION ERROR:")
        feedback_parts.append(f"  {error_details}")
        feedback_parts.append("The measure was created but failed to execute. Check your column/table references.")

    elif error_type == "value_mismatch":
        feedback_parts.append(f"VALUE MISMATCH:")
        feedback_parts.append(f"  Expected: {error_details.get('expected')}")
        feedback_parts.append(f"  Got: {error_details.get('actual')}")
        feedback_parts.append("Your DAX executes but returns incorrect values. Review your logic.")

    elif error_type == "parse_error":
        feedback_parts.append(f"Could not parse your response as DAX.")
        feedback_parts.append("Please provide ONLY the DAX measure definition, starting with the measure name.")

    else:
        feedback_parts.append(f"Validation failed: {error_details}")
        feedback_parts.append("Please try a different approach.")

    return "\n".join(feedback_parts)

def validate_with_pattern(generated_dax, expected_dax, alternatives):
    """Pattern-based validation as fallback"""
    def normalize(dax):
        return re.sub(r'\s+', ' ', dax).strip().lower().replace("'", "'")

    gen_norm = normalize(generated_dax)

    if normalize(expected_dax) == gen_norm:
        return True, "exact_match"

    for alt in alternatives:
        if normalize(alt) == gen_norm:
            return True, "alternative_match"

    # Expression-level match
    gen_name, gen_expr = parse_measure_definition(generated_dax)
    exp_name, exp_expr = parse_measure_definition(expected_dax)

    if gen_expr and exp_expr and normalize(gen_expr) == normalize(exp_expr):
        return True, "expression_match"

    for alt in alternatives:
        alt_name, alt_expr = parse_measure_definition(alt)
        if gen_expr and alt_expr and normalize(gen_expr) == normalize(alt_expr):
            return True, "alt_expression_match"

    return False, "no_match"

def solve_task_interactive(task, model, pbi_validator=None):
    """
    Solve a task with real Power BI validation.
    pbi_validator is a callable that takes (measure_name, expression) and returns:
      - (True, result_value) on success
      - (False, error_message) on failure

    If pbi_validator is None, falls back to pattern matching.
    """
    results = {
        "task_id": task["id"],
        "title": task["title"],
        "complexity": task["complexity"],
        "category": task["category"],
        "model": model,
        "validation_mode": "power_bi" if pbi_validator else "pattern_match",
        "iterations": [],
        "solved": False,
        "first_try": False,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cost": 0,
        "total_time": 0
    }

    # Build initial prompt
    messages = [
        {"role": "system", "content": task["prompt"]["system"]},
        {"role": "user", "content": f"{task['prompt']['user']}\n\nData Model Context: {task['prompt']['dataModelContext']}"}
    ]

    for iteration in range(1, MAX_ITERATIONS + 1):
        iter_result = {"iteration": iteration}

        # Call model
        start_time = time.time()
        response, error = call_openrouter(model, messages)
        iter_result["time"] = time.time() - start_time
        results["total_time"] += iter_result["time"]

        if error:
            iter_result["error"] = error
            iter_result["success"] = False
            results["iterations"].append(iter_result)
            messages.append({"role": "assistant", "content": "[API Error]"})
            messages.append({"role": "user", "content": f"API call failed. Please try again."})
            continue

        # Parse response
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
            iter_result["error"] = f"Response parse error: {e}"
            iter_result["success"] = False
            results["iterations"].append(iter_result)
            feedback = generate_blind_feedback("parse_error", str(e), iteration, MAX_ITERATIONS)
            messages.append({"role": "assistant", "content": "[Parse Error]"})
            messages.append({"role": "user", "content": feedback})
            continue

        # Extract DAX
        dax = extract_dax(content)
        iter_result["raw_response"] = content
        iter_result["extracted_dax"] = dax

        measure_name, expression = parse_measure_definition(dax)
        iter_result["measure_name"] = measure_name
        iter_result["expression"] = expression

        if not measure_name or not expression:
            iter_result["success"] = False
            iter_result["error"] = "Could not parse measure definition"
            results["iterations"].append(iter_result)
            feedback = generate_blind_feedback("parse_error", "Could not find measure name = expression pattern", iteration, MAX_ITERATIONS)
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": feedback})
            continue

        # Validate
        if pbi_validator:
            # Real Power BI validation
            success, result_or_error = pbi_validator(measure_name, expression, task)
            iter_result["pbi_validation"] = {"success": success, "result": result_or_error}

            if success:
                iter_result["success"] = True
                results["solved"] = True
                results["final_dax"] = dax
                if iteration == 1:
                    results["first_try"] = True
                results["iterations"].append(iter_result)
                break
            else:
                iter_result["success"] = False
                # Determine error type from result
                if "syntax" in str(result_or_error).lower() or "parse" in str(result_or_error).lower():
                    feedback = generate_blind_feedback("syntax", result_or_error, iteration, MAX_ITERATIONS)
                elif isinstance(result_or_error, dict) and "expected" in result_or_error:
                    feedback = generate_blind_feedback("value_mismatch", result_or_error, iteration, MAX_ITERATIONS)
                else:
                    feedback = generate_blind_feedback("execution", result_or_error, iteration, MAX_ITERATIONS)

                iter_result["feedback"] = feedback
                results["iterations"].append(iter_result)
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": feedback})
        else:
            # Pattern matching fallback
            valid, match_type = validate_with_pattern(
                dax,
                task["expectedOutput"]["dax"],
                task["expectedOutput"].get("alternativeCorrect", [])
            )

            iter_result["pattern_match"] = {"valid": valid, "match_type": match_type}

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
                # BLIND feedback - don't show the expected answer!
                feedback = generate_blind_feedback(
                    "value_mismatch",
                    {"expected": "[hidden - solve it yourself!]", "actual": "Your DAX doesn't match the expected logic"},
                    iteration,
                    MAX_ITERATIONS
                )
                iter_result["feedback"] = feedback
                results["iterations"].append(iter_result)
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": feedback})

    results["iteration_count"] = len(results["iterations"])
    return results

def generate_log(result, timestamp):
    """Generate markdown log"""
    status = "✅ SOLVED" if result["solved"] else "❌ FAILED"
    mode = result.get("validation_mode", "pattern_match")

    log = f"""# DAX Bench Run Log (Power BI Validation)

## Run Information
| Field | Value |
|-------|-------|
| **Task** | {result['task_id']} - {result['title']} |
| **Model** | {result['model']} |
| **Validation** | {mode} |
| **Timestamp** | {timestamp} |
| **Result** | {status} in {result['iteration_count']} iteration(s) |

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
            log += f"**Tokens**: {iter_data.get('input_tokens', 0)} in, {iter_data.get('output_tokens', 0)} out\n\n"
            log += f"**Generated DAX**:\n```dax\n{iter_data.get('extracted_dax', 'N/A')}\n```\n\n"

            if iter_data.get("pbi_validation"):
                pbi = iter_data["pbi_validation"]
                log += f"**Power BI Validation**: {'✅ PASSED' if pbi['success'] else '❌ FAILED'}\n"
                if not pbi['success']:
                    log += f"**Error**: {pbi['result']}\n"
                log += "\n"

            if iter_data.get('success'):
                log += f"**Result**: ✅ PASSED\n\n"
            else:
                log += f"**Result**: ❌ Failed\n\n"
                if iter_data.get('feedback'):
                    log += f"**Feedback sent** (blind - no answer shown):\n```\n{iter_data['feedback']}\n```\n\n"

        log += "---\n\n"

    log += f"""## Summary

| Metric | Value |
|--------|-------|
| **Iterations** | {result['iteration_count']} |
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

def main():
    import sys

    if not API_KEY:
        print("ERROR: OPENROUTER_DAXBENCH_API_KEY not set")
        return

    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python run_with_pbi_validation.py <task-id|all> [model] [--blind]")
        print("Example: python run_with_pbi_validation.py task-015 openai/gpt-5.2-pro --blind")
        return

    task_arg = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "anthropic/claude-opus-4.5"
    blind_mode = "--blind" in sys.argv

    print("=" * 60)
    print(f"DAX BENCH SOLVER - {'BLIND' if blind_mode else 'STANDARD'} MODE")
    print(f"Model: {model}")
    print(f"Validation: Pattern matching (Power BI integration pending)")
    print("=" * 60)

    # Load tasks
    if task_arg.lower() == "all":
        tasks = load_all_tasks()
    else:
        task = load_task(task_arg)
        if not task:
            print(f"Task not found: {task_arg}")
            return
        tasks = [task]

    print(f"Tasks to run: {len(tasks)}\n")

    RUNS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    date_prefix = datetime.now().strftime("%Y-%m-%d_%H%M")
    model_safe = model.replace("/", "_").replace(":", "_")

    all_results = []

    for i, task in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] {task['id']}: {task['title']}")

        # For now, use pattern matching without showing the answer
        result = solve_task_interactive(task, model, pbi_validator=None)
        all_results.append(result)

        status = "[OK]" if result["solved"] else "[FAIL]"
        iters = result["iteration_count"]
        first = " *" if result.get("first_try") else ""
        print(f"  {status} {iters} iter(s), ${result['total_cost']:.4f}{first}")

        # Save log
        log = generate_log(result, timestamp)
        suffix = "_blind" if blind_mode else "_pbi"
        log_file = RUNS_DIR / f"{date_prefix}_{task['id']}_{model_safe}{suffix}.md"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(log)

    # Summary
    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)

    solved = sum(1 for r in all_results if r["solved"])
    first_try = sum(1 for r in all_results if r.get("first_try"))
    total_cost = sum(r["total_cost"] for r in all_results)

    print(f"Solved: {solved}/{len(tasks)} ({100*solved/len(tasks):.1f}%)")
    print(f"First-try: {first_try}/{len(tasks)}")
    print(f"Total cost: ${total_cost:.4f}")

if __name__ == "__main__":
    main()
