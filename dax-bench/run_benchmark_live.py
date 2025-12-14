#!/usr/bin/env python3
"""
DAX Bench Live Runner - Runs benchmarks with live Power BI validation.

This script is designed to be run from Claude Code with MCP tools available.
It uses the schema extractor to provide model context and validates each
generated DAX expression against the live Power BI model.

Usage (from Claude Code):
    python run_benchmark_live.py --models opus,sonnet,haiku,mistral --tasks 1-30
"""

import os
import sys
import json
import time
import re
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

from schema_extractor import extract_schema

# Configuration
API_KEY = os.environ.get("OPENROUTER_DAXBENCH_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TASKS_DIR = Path(__file__).parent / "tasks"
RUNS_DIR = Path(__file__).parent / "runs"

# Model mapping
MODELS = {
    "opus": "anthropic/claude-opus-4-5-20251101",
    "sonnet": "anthropic/claude-sonnet-4-5-20241022",
    "haiku": "anthropic/claude-haiku-4-5-20251022",
    "mistral": "mistralai/mistral-small-3.1-24b-instruct",
    "gemini": "google/gemini-2.5-flash",
}


def load_all_tasks() -> List[dict]:
    """Load all task JSON files."""
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


def call_openrouter(model: str, messages: List[dict], temperature: float = 0.2) -> Tuple[Optional[dict], dict]:
    """Make API call to OpenRouter."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/bigfootdax",
        "X-Title": "DAX Bench Live"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2000
    }

    start_time = time.time()
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
        elapsed = time.time() - start_time

        if response.status_code != 200:
            return None, {"error": response.text, "elapsed": elapsed}

        data = response.json()
        return data, {"elapsed": elapsed}
    except Exception as e:
        return None, {"error": str(e), "elapsed": time.time() - start_time}


def extract_dax(response_text: str) -> str:
    """Extract DAX code from model response."""
    # Try code block first
    code_match = re.search(r'```(?:dax)?\s*(.*?)```', response_text, re.DOTALL | re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()

    # Otherwise look for measure pattern
    measure_match = re.search(r'(\[?\w+[\w\s]*\]?\s*=\s*.+)', response_text, re.DOTALL)
    if measure_match:
        return measure_match.group(1).strip()

    return response_text.strip()


def parse_measure(dax_code: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse measure name and expression from DAX code."""
    match = re.match(r'\[?([^\]=]+)\]?\s*=\s*(.+)', dax_code, re.DOTALL)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None


def run_benchmark_task(task: dict, model_id: str, schema_context: str,
                       mcp_create_measure, mcp_run_dax, mcp_delete_measure) -> dict:
    """
    Run a single benchmark task with live Power BI validation.

    Args:
        task: Task definition dict
        model_id: OpenRouter model ID
        schema_context: Formatted schema context for prompt
        mcp_create_measure: MCP function to create measures
        mcp_run_dax: MCP function to run DAX queries
        mcp_delete_measure: MCP function to delete measures

    Returns:
        Result dict with validation status
    """
    result = {
        "task_id": task["id"],
        "title": task["title"],
        "complexity": task["complexity"],
        "category": task["category"],
        "model": model_id,
        "valid": False,
        "dax": None,
        "error": None,
        "actual_result": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "time": 0,
    }

    # Build prompt with schema context
    system_prompt = task["prompt"]["system"]
    user_prompt = f"{task['prompt']['user']}\n\n{schema_context}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Call OpenRouter
    response, meta = call_openrouter(model_id, messages)
    result["time"] = meta.get("elapsed", 0)

    if response is None:
        result["error"] = meta.get("error", "API call failed")
        return result

    # Extract response
    try:
        content = response["choices"][0]["message"]["content"]
        usage = response.get("usage", {})
        result["input_tokens"] = usage.get("prompt_tokens", 0)
        result["output_tokens"] = usage.get("completion_tokens", 0)
    except (KeyError, IndexError) as e:
        result["error"] = f"Parse error: {e}"
        return result

    # Extract DAX
    dax = extract_dax(content)
    result["dax"] = dax

    measure_name, expression = parse_measure(dax)
    if not measure_name or not expression:
        result["error"] = "Could not parse measure from response"
        return result

    # Create test measure name
    model_short = model_id.split("/")[-1].split("-")[0][:6]
    test_name = f"_bench_{model_short}_{task['id'].replace('-', '')}"

    # Validate with Power BI
    try:
        # Create measure
        create_result = mcp_create_measure(
            table="_Measures",
            name=test_name,
            expression=expression
        )

        # Check for syntax errors
        if isinstance(create_result, dict) and create_result.get("error"):
            result["error"] = f"Syntax error: {create_result['error']}"
            return result

        # Execute measure
        exec_result = mcp_run_dax(f'EVALUATE ROW("Result", [{test_name}])')

        if isinstance(exec_result, dict) and exec_result.get("error"):
            result["error"] = f"Execution error: {exec_result['error']}"
            mcp_delete_measure(table="_Measures", name=test_name)
            return result

        # Success!
        result["valid"] = True
        result["actual_result"] = exec_result

        # Clean up test measure
        mcp_delete_measure(table="_Measures", name=test_name)

    except Exception as e:
        result["error"] = f"Validation error: {e}"

    return result


def main():
    """Main entry point - prints usage info when run standalone."""
    print("DAX Bench Live Runner")
    print("=" * 50)
    print()
    print("This script is designed to be orchestrated by Claude Code.")
    print("It requires MCP tool functions to be passed for Power BI validation.")
    print()
    print("To run benchmarks, use Claude Code to:")
    print("1. Get schema from Power BI: mcp__powerbi-desktop__get_model_info")
    print("2. Format with schema_extractor.extract_schema()")
    print("3. Call run_benchmark_task() for each model/task combination")
    print("4. Use results_analyzer.py to generate reports")
    print()
    print(f"Available models: {', '.join(MODELS.keys())}")
    print(f"Tasks available: {len(load_all_tasks())}")

    if not API_KEY:
        print()
        print("WARNING: OPENROUTER_DAXBENCH_API_KEY not set!")
    else:
        print()
        print("API key configured.")


if __name__ == "__main__":
    main()
