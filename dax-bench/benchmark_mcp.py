#!/usr/bin/env python3
"""
DAX Bench MCP Integration Module

This module provides functions for running DAX benchmarks with real Power BI validation.
It's designed to be called step-by-step by Claude Code, which has access to MCP tools.

Usage (from Claude Code):
    1. Load this module's functions
    2. Call get_model_response() to get a model's DAX answer
    3. Use MCP tools (manage_measure, run_dax) to validate
    4. Call record_result() to save the outcome
"""

import os
import json
import time
import re
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

# Configuration
API_KEY = os.environ.get("OPENROUTER_DAXBENCH_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TASKS_DIR = Path(__file__).parent / "tasks"
RUNS_DIR = Path(__file__).parent / "runs"
MEASURES_TABLE = "_Measures"


def load_task(task_id: str) -> Optional[dict]:
    """Load a single task by ID (e.g., 'task-001' or just '1')"""
    # Normalize task ID
    if not task_id.startswith("task-"):
        task_id = f"task-{task_id.zfill(3)}"

    for level in ["basic", "intermediate", "advanced"]:
        task_file = TASKS_DIR / level / f"{task_id}.json"
        if task_file.exists():
            with open(task_file, "r", encoding="utf-8") as f:
                task = json.load(f)
                task["_level"] = level
                task["_file"] = str(task_file)
                return task
    return None


def load_all_tasks() -> List[dict]:
    """Load all tasks from the tasks directory"""
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


def get_model_response(task: dict, model: str, previous_attempts: List[dict] = None) -> dict:
    """
    Get a model's DAX response for a task.

    Args:
        task: The task definition
        model: OpenRouter model ID (e.g., 'google/gemini-2.5-pro')
        previous_attempts: List of previous attempts with feedback for iteration

    Returns:
        dict with 'dax', 'raw_response', 'tokens', 'cost', 'time', 'error'
    """
    if not API_KEY:
        return {"error": "OPENROUTER_DAXBENCH_API_KEY not set"}

    # Build messages
    messages = [
        {"role": "system", "content": task["prompt"]["system"]},
        {"role": "user", "content": f"{task['prompt']['user']}\n\nData Model Context: {task['prompt']['dataModelContext']}"}
    ]

    # Add previous attempts if iterating
    if previous_attempts:
        for attempt in previous_attempts:
            messages.append({"role": "assistant", "content": attempt.get("raw_response", attempt.get("dax", ""))})
            messages.append({"role": "user", "content": attempt.get("feedback", "Please try again.")})

    # Call OpenRouter
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/bigfootdax",
        "X-Title": "DAX Bench Solver"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 2000
    }

    start_time = time.time()
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
        elapsed = time.time() - start_time

        if response.status_code != 200:
            return {"error": response.text, "time": elapsed}

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        # Extract DAX from response
        dax = extract_dax(content)

        return {
            "dax": dax,
            "raw_response": content,
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "cost": usage.get("cost", 0),
            "time": elapsed
        }

    except Exception as e:
        return {"error": str(e), "time": time.time() - start_time}


def extract_dax(response_text: str) -> str:
    """Extract DAX code from model response"""
    # Try code block first
    code_match = re.search(r'```(?:dax)?\s*(.*?)```', response_text, re.DOTALL | re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()

    # Look for measure pattern
    measure_match = re.search(r'(\[?\w+[\w\s]*\]?\s*=\s*.+)', response_text, re.DOTALL)
    if measure_match:
        return measure_match.group(1).strip()

    return response_text.strip()


def parse_measure_definition(dax_code: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse measure name and expression from DAX code"""
    match = re.match(r'\[?([^\]=]+)\]?\s*=\s*(.+)', dax_code, re.DOTALL)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None


def generate_feedback(error_type: str, error_msg: str, task: dict, iteration: int, max_iters: int = 10) -> str:
    """Generate feedback message for the model based on validation error"""

    if error_type == "syntax":
        feedback = f"""SYNTAX ERROR: {error_msg}

Please fix the syntax error and try again. Common issues:
- Missing or mismatched parentheses
- Incorrect function names (check spelling)
- Invalid column/table references (use 'TableName'[ColumnName] format)
- Missing commas between function arguments"""

    elif error_type == "execution":
        feedback = f"""EXECUTION ERROR: {error_msg}

The measure was created but failed to execute. Check:
- Column and table names exist in the model
- Function parameters are the correct type
- Filter context is appropriate"""

    elif error_type == "reference":
        feedback = f"""REFERENCE ERROR: {error_msg}

The measure references a column or table that doesn't exist.
Available tables: Sales, Date, Product, Customer, Store, Currency Exchange"""

    else:
        feedback = f"""ERROR: {error_msg}

Please review your DAX and try again."""

    # Add hints from task if available
    if task.get("hints"):
        feedback += "\n\nHINTS:"
        for hint in task["hints"][:2]:
            feedback += f"\n  - {hint}"

    feedback += f"\n\nThis is attempt {iteration} of {max_iters}. Please provide the corrected DAX measure."

    return feedback


def record_result(
    task: dict,
    model: str,
    solved: bool,
    iterations: List[dict],
    final_dax: Optional[str] = None,
    final_measure_name: Optional[str] = None
) -> str:
    """
    Record the result of a benchmark task.

    Args:
        task: The task definition
        model: OpenRouter model ID
        solved: Whether the task was solved
        iterations: List of iteration results
        final_dax: The final DAX that passed validation
        final_measure_name: Name of the measure saved in Power BI

    Returns:
        Path to the saved log file
    """
    RUNS_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    date_prefix = datetime.now().strftime("%Y-%m-%d_%H%M")
    model_safe = model.replace("/", "_").replace(":", "_")

    # Calculate totals
    total_tokens_in = sum(i.get("input_tokens", 0) for i in iterations)
    total_tokens_out = sum(i.get("output_tokens", 0) for i in iterations)
    total_cost = sum(i.get("cost", 0) for i in iterations)
    total_time = sum(i.get("time", 0) for i in iterations)

    result = {
        "task_id": task["id"],
        "title": task["title"],
        "complexity": task["complexity"],
        "category": task["category"],
        "model": model,
        "solved": solved,
        "first_try": solved and len(iterations) == 1,
        "iteration_count": len(iterations),
        "iterations": iterations,
        "total_input_tokens": total_tokens_in,
        "total_output_tokens": total_tokens_out,
        "total_cost": total_cost,
        "total_time": total_time,
        "final_dax": final_dax,
        "final_measure_name": final_measure_name,
        "validation_method": "powerbi_execution"
    }

    # Generate log
    status = "SOLVED" if solved else "FAILED"
    status_emoji = "✅" if solved else "❌"

    log = f"""# DAX Bench Run Log (v4 - Power BI Validated)

## Run Information
| Field | Value |
|-------|-------|
| **Task** | {task['id']} - {task['title']} |
| **Model** | {model} |
| **Timestamp** | {timestamp} |
| **Result** | {status_emoji} {status} in {len(iterations)} iteration(s) |
| **Validation** | Power BI Execution |

## Task Details
- **Complexity**: {task['complexity']}
- **Category**: {task['category']}

---

## Iterations

"""

    for i, iter_data in enumerate(iterations, 1):
        log += f"### Iteration {i}\n\n"
        log += f"**Token Usage**: {iter_data.get('input_tokens', 0)} input, {iter_data.get('output_tokens', 0)} output\n"
        log += f"**Time**: {iter_data.get('time', 0):.2f}s\n\n"
        log += f"**Model Response**:\n```dax\n{iter_data.get('dax', 'N/A')}\n```\n\n"

        if iter_data.get("valid"):
            log += f"**Validation**: ✅ PASSED\n\n"
        else:
            log += f"**Validation**: ❌ FAILED\n"
            if iter_data.get("error"):
                log += f"- Error: {iter_data['error']}\n\n"
            if iter_data.get("feedback"):
                log += f"**Feedback Sent**:\n```\n{iter_data['feedback']}\n```\n\n"

        log += "---\n\n"

    log += f"""## Summary

| Metric | Value |
|--------|-------|
| **Total Iterations** | {len(iterations)} |
| **First Try Success** | {'✅ Yes' if result['first_try'] else '❌ No'} |
| **Input Tokens** | {total_tokens_in:,} |
| **Output Tokens** | {total_tokens_out:,} |
| **Total Cost** | ${total_cost:.6f} |
| **Total Time** | {total_time:.2f}s |

"""

    if final_dax:
        log += f"""## Final DAX
```dax
{final_dax}
```
"""

    if final_measure_name:
        log += f"\n**Measure saved in Power BI**: `{final_measure_name}` in `{MEASURES_TABLE}` table\n"

    # Save files
    log_file = RUNS_DIR / f"{date_prefix}_{task['id']}_{model_safe}_v4.md"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(log)

    json_file = RUNS_DIR / f"{date_prefix}_{task['id']}_{model_safe}_v4.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    return str(log_file)


# Convenience function to get task prompts
def get_task_prompt(task: dict) -> str:
    """Get the full prompt for a task (useful for debugging)"""
    return f"""System: {task['prompt']['system']}

User: {task['prompt']['user']}

Data Model Context: {task['prompt']['dataModelContext']}"""


# Export useful constants
__all__ = [
    'load_task',
    'load_all_tasks',
    'get_model_response',
    'extract_dax',
    'parse_measure_definition',
    'generate_feedback',
    'record_result',
    'get_task_prompt',
    'MEASURES_TABLE',
    'TASKS_DIR',
    'RUNS_DIR'
]
