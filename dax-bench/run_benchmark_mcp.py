#!/usr/bin/env python3
"""
DAX Bench - Full Benchmark with MCP Validation Output
Generates validation commands for Claude to execute via MCP.

This outputs JSON that Claude reads and validates via Power BI MCP tools.
"""

import os
import json
import time
import re
import requests
from datetime import datetime
from pathlib import Path

API_KEY = os.environ.get("OPENROUTER_DAXBENCH_API_KEY", "")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_ITERATIONS = 10
TASKS_DIR = Path(__file__).parent / "tasks"
RUNS_DIR = Path(__file__).parent / "runs"


def load_all_tasks():
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
        return None, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)


def extract_dax(response_text):
    code_match = re.search(r'```(?:dax)?\s*(.*?)```', response_text, re.DOTALL | re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()
    measure_match = re.search(r'(\[?\w+[\w\s%-]*\]?\s*=\s*.+)', response_text, re.DOTALL)
    if measure_match:
        return measure_match.group(1).strip()
    return response_text.strip()


def parse_dax(dax):
    if dax.strip().upper().startswith('VAR'):
        return None, dax.strip()
    match = re.match(r'\[?([^\]=]+)\]?\s*=\s*(.+)', dax, re.DOTALL)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, dax.strip()


def detect_type(expression, task):
    expr_upper = expression.upper().strip()
    tags = task.get("tags", [])

    if "calculated-column" in tags:
        return "calc_column"
    if "table" in tags:
        return "table"

    table_funcs = ['SUMMARIZE', 'SUMMARIZECOLUMNS', 'SELECTCOLUMNS', 'ADDCOLUMNS',
                   'UNION', 'INTERSECT', 'EXCEPT', 'CROSSJOIN', 'GENERATE',
                   'DATATABLE', 'FILTER(', 'TOPN', 'NATURALINNERJOIN']

    for func in table_funcs:
        if expr_upper.startswith(func):
            return "table"

    if 'EARLIER(' in expr_upper:
        return "calc_column"

    return "measure"


def build_query(name, expression, dax_type, task):
    if dax_type == "table":
        return f"EVALUATE {expression}"
    elif dax_type == "calc_column":
        table_refs = re.findall(r"(\w+)\[", expression)
        base_table = table_refs[0] if table_refs else "Product"
        safe_name = name or "Result"
        return f'EVALUATE TOPN(5, ADDCOLUMNS({base_table}, "{safe_name}", {expression}))'
    else:
        safe_name = name or "Result"
        return f'EVALUATE ROW("{safe_name}", {expression})'


def main():
    import sys

    if not API_KEY:
        print("ERROR: OPENROUTER_DAXBENCH_API_KEY not set")
        return

    model = sys.argv[1] if len(sys.argv) > 1 else "anthropic/claude-opus-4.5"

    tasks = load_all_tasks()
    print(f"DAX Bench - {len(tasks)} tasks")
    print(f"Model: {model}")
    print(f"Max iterations: {MAX_ITERATIONS}")
    print("=" * 60)

    RUNS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    model_safe = model.replace("/", "_")

    # Output file for Claude to read and validate
    output_file = RUNS_DIR / f"{timestamp}_mcp_validation_{model_safe}.json"

    all_results = []

    for i, task in enumerate(tasks, 1):
        print(f"\n[{i}/{len(tasks)}] {task['id']}: {task['title']}")

        result = {
            "task_id": task["id"],
            "title": task["title"],
            "complexity": task["complexity"],
            "category": task["category"],
            "iterations": []
        }

        messages = [
            {"role": "system", "content": task["prompt"]["system"]},
            {"role": "user", "content": f"{task['prompt']['user']}\n\nData Model Context: {task['prompt']['dataModelContext']}"}
        ]

        solved = False
        for iteration in range(1, MAX_ITERATIONS + 1):
            iter_data = {"iteration": iteration}

            # Call LLM
            start = time.time()
            response, error = call_openrouter(model, messages)
            iter_data["time"] = time.time() - start

            if error:
                iter_data["error"] = error
                print(f"  Iter {iteration}: API Error - {error[:50]}")
                result["iterations"].append(iter_data)
                continue

            try:
                content = response["choices"][0]["message"]["content"]
                usage = response.get("usage", {})
                iter_data["tokens"] = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
                iter_data["cost"] = usage.get("cost", 0)
            except:
                iter_data["error"] = "Parse error"
                result["iterations"].append(iter_data)
                continue

            dax = extract_dax(content)
            name, expression = parse_dax(dax)

            iter_data["dax"] = dax
            iter_data["name"] = name
            iter_data["expression"] = expression[:200] if expression else None

            if not expression:
                iter_data["status"] = "parse_error"
                print(f"  Iter {iteration}: Parse error")
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": "Could not parse DAX. Please provide: MeasureName = <expression>"})
                result["iterations"].append(iter_data)
                continue

            # Build validation query
            dax_type = detect_type(expression, task)
            query = build_query(name, expression, dax_type, task)

            iter_data["dax_type"] = dax_type
            iter_data["validation_query"] = query
            iter_data["status"] = "pending_validation"

            result["iterations"].append(iter_data)

            # For now, mark as needing validation - Claude will validate
            print(f"  Iter {iteration}: Generated ({dax_type}) - needs MCP validation")

            # Only do one iteration for now - validation will determine if we need more
            solved = True
            break

        result["needs_validation"] = True
        result["solved"] = solved
        all_results.append(result)

    # Save for Claude to validate
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "model": model,
            "total_tasks": len(tasks),
            "results": all_results
        }, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Generated {len(all_results)} tasks for validation")
    print(f"Output: {output_file}")
    print(f"\nClaude should now validate each task using run_dax MCP tool")


if __name__ == "__main__":
    main()
