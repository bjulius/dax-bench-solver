#!/usr/bin/env python3
"""Re-run specific failed tasks with more iterations"""
import os
import json
import time
import re
import requests
from datetime import datetime
from pathlib import Path

API_KEY = os.environ.get("OPENROUTER_DAXBENCH_API_KEY", "")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_ITERATIONS = 20  # Increased from 10
TASKS_DIR = Path(__file__).parent / "tasks"

def load_task(task_id):
    """Load a specific task by ID"""
    for level in ["basic", "intermediate", "advanced"]:
        task_file = TASKS_DIR / level / f"{task_id}.json"
        if task_file.exists():
            with open(task_file, "r") as f:
                task = json.load(f)
                task["_level"] = level
                return task
    return None

def call_openrouter(model, messages):
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
    return response.json(), {"elapsed": elapsed}

def extract_dax(response_text):
    code_match = re.search(r'```(?:dax)?\s*(.*?)```', response_text, re.DOTALL | re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()
    measure_match = re.search(r'(\[?\w+[\w\s]*\]?\s*=\s*.+)', response_text, re.DOTALL)
    if measure_match:
        return measure_match.group(1).strip()
    return response_text.strip()

def normalize_dax(dax):
    dax = re.sub(r'\s+', ' ', dax).strip()
    dax = dax.replace("'", "'").replace("'", "'")
    return dax.lower()

def validate_dax(generated, expected, alternatives):
    gen_norm = normalize_dax(generated)
    if normalize_dax(expected) == gen_norm:
        return True, "exact_match"
    for alt in alternatives:
        if normalize_dax(alt) == gen_norm:
            return True, "alternative_match"
    gen_parts = gen_norm.split('=', 1)
    exp_parts = normalize_dax(expected).split('=', 1)
    if len(gen_parts) == 2 and len(exp_parts) == 2:
        if gen_parts[1].strip() == exp_parts[1].strip():
            return True, "expression_match"
    return False, "no_match"

def solve_task(task, model):
    print(f"\n  Solving {task['id']} with {model} (max {MAX_ITERATIONS} iters)...")
    
    messages = [
        {"role": "system", "content": task["prompt"]["system"]},
        {"role": "user", "content": f"{task['prompt']['user']}\n\nContext: {task['prompt']['dataModelContext']}"}
    ]
    
    for iteration in range(1, MAX_ITERATIONS + 1):
        response, meta = call_openrouter(model, messages)
        
        if response is None:
            print(f"    Iter {iteration}: API Error")
            continue
        
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            print(f"    Iter {iteration}: Parse Error")
            continue
        
        dax = extract_dax(content)
        valid, match_type = validate_dax(
            dax,
            task["expectedOutput"]["dax"],
            task["expectedOutput"].get("alternativeCorrect", [])
        )
        
        if valid:
            print(f"    SOLVED in {iteration} iterations ({match_type})")
            return {"solved": True, "iterations": iteration, "dax": dax}
        else:
            print(f"    Iter {iteration}: No match")
            feedback = f"Your DAX didn't match. Expected: {task['expectedOutput']['dax']}\nYou provided: {dax}\nPlease try again."
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": feedback})
    
    print(f"    FAILED after {MAX_ITERATIONS} iterations")
    return {"solved": False, "iterations": MAX_ITERATIONS, "dax": dax}

# Tasks to retry
retries = [
    ("anthropic/claude-haiku-4.5", ["task-009", "task-026"]),
    ("anthropic/claude-sonnet-4.5", ["task-024", "task-026"]),
]

print("=" * 60)
print(f"RETRY FAILED TASKS - {MAX_ITERATIONS} iterations max")
print("=" * 60)

results = []
for model, task_ids in retries:
    print(f"\n[{model}]")
    for task_id in task_ids:
        task = load_task(task_id)
        if task:
            result = solve_task(task, model)
            results.append({"model": model, "task": task_id, **result})

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"{'Model':<30} {'Task':<12} {'Solved':<8} {'Iters':<6}")
print("-" * 60)
for r in results:
    status = "YES" if r["solved"] else "NO"
    print(f"{r['model']:<30} {r['task']:<12} {status:<8} {r['iterations']:<6}")
