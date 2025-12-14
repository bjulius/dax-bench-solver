#!/usr/bin/env python3
"""
DAX Bench Solver with Power BI Validation
Generates DAX via OpenRouter, outputs for MCP validation, reads back results
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

    response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
    if response.status_code != 200:
        return None, response.text
    return response.json(), None

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

def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python solve_with_pbi.py <task-id> [model]")
        print("Example: python solve_with_pbi.py task-015 google/gemini-2.5-flash")
        return

    task_id = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "google/gemini-2.5-flash"

    task = load_task(task_id)
    if not task:
        print(f"Task not found: {task_id}")
        return

    print(f"=" * 60)
    print(f"TASK: {task['id']} - {task['title']}")
    print(f"Complexity: {task['complexity']} | Category: {task['category']}")
    print(f"Model: {model}")
    print(f"=" * 60)
    print(f"\nExpected DAX:\n{task['expectedOutput']['dax']}\n")

    messages = [
        {"role": "system", "content": task["prompt"]["system"]},
        {"role": "user", "content": f"{task['prompt']['user']}\n\nContext: {task['prompt']['dataModelContext']}"}
    ]

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n{'='*60}")
        print(f"ITERATION {iteration}")
        print(f"{'='*60}")

        # Call OpenRouter
        response, error = call_openrouter(model, messages)
        if error:
            print(f"API Error: {error}")
            continue

        content = response["choices"][0]["message"]["content"]
        dax = extract_dax(content)
        name, expr = parse_measure(dax)

        print(f"\nGenerated DAX:")
        print(f"```dax")
        print(dax)
        print(f"```")

        if name and expr:
            print(f"\n--- VALIDATION COMMANDS (run these in Claude) ---")
            print(f"1. Create measure:")
            print(f'   mcp__powerbi-desktop__manage_measure(operation="create", table="Sales", name="{name}", expression="{expr.replace(chr(34), chr(39))}")')
            print(f"\n2. Test execution:")
            print(f'   mcp__powerbi-desktop__run_dax(query="EVALUATE ROW(\\"Result\\", [{name}])")')
            print(f"\n3. If error, delete and retry:")
            print(f'   mcp__powerbi-desktop__manage_measure(operation="delete", table="Sales", name="{name}")')

        print(f"\n--- FEEDBACK INPUT ---")
        print("Enter validation result (or 'pass' if correct, 'quit' to stop):")
        print("Examples:")
        print("  pass")
        print("  error: Column 'Net Price' not found")
        print("  wrong: expected 1234, got 5678")

        try:
            feedback = input("> ").strip()
        except EOFError:
            print("\n[Non-interactive mode - stopping]")
            break

        if feedback.lower() == 'pass':
            print(f"\n{'='*60}")
            print(f"SUCCESS! Solved in {iteration} iteration(s)")
            print(f"{'='*60}")
            break
        elif feedback.lower() == 'quit':
            print("Stopped by user")
            break
        else:
            # Add feedback to conversation
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"Validation failed: {feedback}\nPlease fix and try again."})
    else:
        print(f"\nFailed after {MAX_ITERATIONS} iterations")

if __name__ == "__main__":
    main()
