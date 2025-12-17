#!/usr/bin/env python3
"""
DAX Bench - Live MCP Validation Benchmark
Uses Power BI MCP tools for real validation with iterative feedback.

This script is designed to be run with Claude Code as the MCP bridge.
It outputs validation commands that Claude executes, then reads back results.

Usage:
    python benchmark_mcp_live.py <task-id|all> [model]

Examples:
    python benchmark_mcp_live.py task-001 anthropic/claude-opus-4.5
    python benchmark_mcp_live.py all anthropic/claude-haiku-4.5
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

# MCP Validation Queue - write commands here for Claude to execute
MCP_QUEUE_FILE = RUNS_DIR / "mcp_validation_queue.json"
MCP_RESULT_FILE = RUNS_DIR / "mcp_validation_result.json"


def load_task(task_id):
    """Load a specific task by ID"""
    for level in ["basic", "intermediate", "advanced"]:
        task_file = TASKS_DIR / level / f"{task_id}.json"
        if task_file.exists():
            with open(task_file, "r", encoding="utf-8") as f:
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

    # Try measure/table pattern
    measure_match = re.search(r'(\[?\w+[\w\s%-]*\]?\s*=\s*.+)', response_text, re.DOTALL)
    if measure_match:
        return measure_match.group(1).strip()

    return response_text.strip()


def parse_dax_definition(dax):
    """Parse name and expression from DAX definition"""
    # Handle VAR ... RETURN patterns that start with VAR
    if dax.strip().upper().startswith('VAR'):
        # This is likely just an expression, no name
        return None, dax.strip()

    match = re.match(r'\[?([^\]=]+)\]?\s*=\s*(.+)', dax, re.DOTALL)
    if match:
        name = match.group(1).strip()
        expression = match.group(2).strip()
        return name, expression
    return None, dax.strip()


def detect_dax_type(expression, task):
    """
    Detect what type of DAX this is based on the expression and task.
    Returns: 'measure', 'table', 'calc_column'
    """
    expr_upper = expression.upper().strip()

    # Check task hints
    task_tags = task.get("tags", [])
    if "calculated-column" in task_tags:
        return "calc_column"
    if "table" in task_tags:
        return "table"

    # Table-returning functions at the start
    table_functions = ['SUMMARIZE', 'SUMMARIZECOLUMNS', 'SELECTCOLUMNS', 'ADDCOLUMNS',
                       'UNION', 'INTERSECT', 'EXCEPT', 'CROSSJOIN', 'GENERATE',
                       'GENERATEALL', 'DATATABLE', 'FILTER', 'ALL', 'VALUES',
                       'DISTINCT', 'TOPN', 'SAMPLE', 'NATURALINNERJOIN',
                       'NATURALLEFTOUTERJOIN', 'CALCULATETABLE']

    for func in table_functions:
        if expr_upper.startswith(func + '(') or expr_upper.startswith(func + ' ('):
            return "table"

    # Check for EARLIER which indicates calc column context
    if 'EARLIER(' in expr_upper or 'EARLIEST(' in expr_upper:
        return "calc_column"

    return "measure"


def build_validation_query(name, expression, dax_type, task):
    """
    Build the appropriate DAX query for validation based on type.
    """
    if dax_type == "table":
        # Table expression - execute directly
        return f"EVALUATE {expression}"

    elif dax_type == "calc_column":
        # Calculated column - wrap in ADDCOLUMNS to provide row context
        # Need to determine which table to iterate over
        # Look for table references in expression
        table_refs = re.findall(r"(\w+)\[", expression)
        if table_refs:
            base_table = table_refs[0]
        else:
            # Try to get from task context
            base_table = "Product"  # Default fallback

        return f'EVALUATE TOPN(5, ADDCOLUMNS({base_table}, "{name}", {expression}))'

    else:
        # Measure - wrap in ROW
        return f'EVALUATE ROW("{name}", {expression})'


def write_mcp_command(command_type, params):
    """Write MCP command to queue file for Claude to execute"""
    command = {
        "timestamp": datetime.now().isoformat(),
        "type": command_type,
        "params": params,
        "status": "pending"
    }
    with open(MCP_QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(command, f, indent=2)
    return command


def read_mcp_result(timeout=30):
    """Read MCP result from result file (Claude writes this)"""
    start = time.time()
    while time.time() - start < timeout:
        if MCP_RESULT_FILE.exists():
            try:
                with open(MCP_RESULT_FILE, "r", encoding="utf-8") as f:
                    result = json.load(f)
                # Clear the result file
                MCP_RESULT_FILE.unlink()
                return result
            except:
                pass
        time.sleep(0.5)
    return {"error": "Timeout waiting for MCP result"}


def validate_with_mcp(name, expression, dax_type, task):
    """
    Validate DAX using Power BI MCP.
    Returns (success: bool, result_or_error: str)
    """
    query = build_validation_query(name, expression, dax_type, task)

    # Write command for Claude to execute
    write_mcp_command("run_dax", {"query": query})

    print(f"\n  [MCP] Validating: {query[:60]}...")
    print(f"  [MCP] Waiting for validation result...")

    # Wait for result
    result = read_mcp_result(timeout=60)

    if "error" in result:
        return False, result["error"]

    if result.get("success"):
        return True, result.get("data", "OK")

    return False, result.get("message", "Validation failed")


def generate_blind_feedback(error_type, error_details, iteration, max_iter):
    """Generate feedback WITHOUT showing the expected answer."""
    lines = [f"Attempt {iteration}/{max_iter} failed."]

    if error_type == "syntax":
        lines.append(f"DAX SYNTAX ERROR: {error_details}")
        lines.append("Check your function names, parentheses, and column references.")
    elif error_type == "execution":
        lines.append(f"EXECUTION ERROR: {error_details}")
        lines.append("The DAX syntax is valid but execution failed. Check table/column names.")
    elif error_type == "parse":
        lines.append("Could not parse your response as a DAX definition.")
        lines.append("Please provide: MeasureName = <expression>")
    else:
        lines.append(f"Error: {error_details}")

    lines.append("\nPlease fix and try again.")
    return "\n".join(lines)


def solve_task_with_mcp(task, model):
    """Solve a task using real Power BI MCP validation"""
    results = {
        "task_id": task["id"],
        "title": task["title"],
        "complexity": task["complexity"],
        "category": task["category"],
        "model": model,
        "validation_mode": "power_bi_mcp",
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

        # Call LLM
        start_time = time.time()
        response, error = call_openrouter(model, messages)
        iter_result["time"] = time.time() - start_time
        results["total_time"] += iter_result["time"]

        if error:
            iter_result["error"] = error
            iter_result["success"] = False
            results["iterations"].append(iter_result)
            messages.append({"role": "assistant", "content": "[API Error]"})
            messages.append({"role": "user", "content": f"API error: {error}. Please try again."})
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
            iter_result["error"] = f"Parse error: {e}"
            iter_result["success"] = False
            results["iterations"].append(iter_result)
            continue

        # Extract DAX
        dax = extract_dax(content)
        iter_result["raw_response"] = content
        iter_result["extracted_dax"] = dax

        name, expression = parse_dax_definition(dax)
        iter_result["name"] = name
        iter_result["expression"] = expression

        if not expression:
            iter_result["success"] = False
            feedback = generate_blind_feedback("parse", "No expression found", iteration, MAX_ITERATIONS)
            iter_result["feedback"] = feedback
            results["iterations"].append(iter_result)
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": feedback})
            continue

        # Detect DAX type
        dax_type = detect_dax_type(expression, task)
        iter_result["dax_type"] = dax_type

        # Validate with Power BI MCP
        success, result_or_error = validate_with_mcp(
            name or task["title"].replace(" ", ""),
            expression,
            dax_type,
            task
        )

        iter_result["mcp_result"] = {"success": success, "details": str(result_or_error)[:500]}

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
            # Determine error type
            error_str = str(result_or_error).lower()
            if "syntax" in error_str or "parse" in error_str:
                error_type = "syntax"
            else:
                error_type = "execution"

            feedback = generate_blind_feedback(error_type, result_or_error, iteration, MAX_ITERATIONS)
            iter_result["feedback"] = feedback
            results["iterations"].append(iter_result)
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": feedback})

    results["iteration_count"] = len(results["iterations"])
    return results


def main():
    import sys

    if not API_KEY:
        print("ERROR: Set OPENROUTER_DAXBENCH_API_KEY environment variable")
        return

    if len(sys.argv) < 2:
        print(__doc__)
        return

    task_arg = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "anthropic/claude-opus-4.5"

    print("=" * 70)
    print("DAX BENCH - LIVE MCP VALIDATION")
    print("=" * 70)
    print(f"Model: {model}")
    print(f"Max Iterations: {MAX_ITERATIONS}")
    print(f"Validation: Power BI MCP (real execution)")
    print("=" * 70)

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
        print(f"\n[{i}/{len(tasks)}] {task['id']}: {task['title']}")
        print(f"  Complexity: {task['complexity']} | Category: {task['category']}")

        result = solve_task_with_mcp(task, model)
        all_results.append(result)

        status = "SOLVED" if result["solved"] else "FAILED"
        iters = result["iteration_count"]
        first = " (first-try!)" if result.get("first_try") else ""
        print(f"  [{status}] {iters} iteration(s), ${result['total_cost']:.4f}{first}")

        # Save individual result
        result_file = RUNS_DIR / f"{date_prefix}_{task['id']}_{model_safe}_mcp.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    # Summary
    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)

    solved = sum(1 for r in all_results if r["solved"])
    first_try = sum(1 for r in all_results if r.get("first_try"))
    total_cost = sum(r["total_cost"] for r in all_results)
    total_time = sum(r["total_time"] for r in all_results)

    print(f"\nSolved: {solved}/{len(tasks)} ({100*solved/len(tasks):.1f}%)")
    print(f"First-Try: {first_try}/{len(tasks)} ({100*first_try/len(tasks):.1f}%)")
    print(f"Total Cost: ${total_cost:.4f}")
    print(f"Total Time: {total_time:.1f}s")

    # Save summary
    summary = {
        "timestamp": timestamp,
        "model": model,
        "total_tasks": len(tasks),
        "solved": solved,
        "first_try": first_try,
        "total_cost": total_cost,
        "total_time": total_time,
        "results": all_results
    }
    summary_file = RUNS_DIR / f"{date_prefix}_SUMMARY_{model_safe}_mcp.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary saved: {summary_file}")


if __name__ == "__main__":
    main()
