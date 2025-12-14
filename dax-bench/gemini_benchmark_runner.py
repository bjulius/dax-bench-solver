#!/usr/bin/env python3
"""
Gemini 2.5 Flash Benchmark Runner
Outputs DAX for each task for Power BI validation via MCP
"""

import os
import json
import requests
import re
from pathlib import Path

API_KEY = os.environ.get('OPENROUTER_DAXBENCH_API_KEY', '')
MODEL = 'google/gemini-2.5-flash'
BASE_URL = 'https://openrouter.ai/api/v1/chat/completions'
TASKS_DIR = Path(__file__).parent / 'tasks'
MAX_ITERATIONS = 5


def load_task(task_id):
    """Load a task by ID."""
    for level in ['basic', 'intermediate', 'advanced']:
        path = TASKS_DIR / level / f'{task_id}.json'
        if path.exists():
            with open(path, 'r') as f:
                task = json.load(f)
                task['_level'] = level
                return task
    return None


def load_all_measure_tasks():
    """Load all measure-based tasks (skip table/column tasks)."""
    tasks = []
    skip_tasks = ['task-011', 'task-012', 'task-013', 'task-014', 'task-015', 'task-016', 'task-018']

    for level in ['basic', 'intermediate', 'advanced']:
        level_dir = TASKS_DIR / level
        if level_dir.exists():
            for task_file in sorted(level_dir.glob('task-*.json')):
                task_id = task_file.stem
                if task_id not in skip_tasks:
                    with open(task_file, 'r') as f:
                        task = json.load(f)
                        task['_level'] = level
                        tasks.append(task)
    return tasks


def call_model(messages):
    """Call Gemini via OpenRouter."""
    response = requests.post(
        BASE_URL,
        headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'},
        json={
            'model': MODEL,
            'messages': messages,
            'temperature': 0.2,
            'max_tokens': 800
        },
        timeout=90
    )
    if response.status_code == 200:
        data = response.json()
        content = data['choices'][0]['message']['content']
        usage = data.get('usage', {})
        return content, usage, None
    return None, None, f'{response.status_code}: {response.text[:200]}'


def extract_dax(text):
    """Extract DAX measure from response."""
    # Try code block first
    match = re.search(r'```(?:dax)?\s*(.*?)```', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Try measure pattern (Name = Expression)
    match = re.search(r'^([A-Za-z][\w\s%-]*\s*=\s*.+)', text, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(1).strip()

    return text.strip()


def parse_measure(dax):
    """Parse measure name and expression."""
    # Handle multi-line expressions
    dax = dax.replace('\r\n', '\n').strip()

    match = re.match(r'^([A-Za-z][\w\s%-]*?)\s*=\s*(.+)', dax, re.DOTALL)
    if match:
        name = match.group(1).strip()
        expr = match.group(2).strip()
        return name, expr
    return None, None


def solve_task(task):
    """
    Attempt to solve a task. Returns dict with results.
    """
    result = {
        'task_id': task['id'],
        'title': task['title'],
        'level': task['_level'],
        'iterations': [],
        'solved': False,
        'final_dax': None,
        'measure_name': None,
        'expression': None,
    }

    messages = [
        {'role': 'system', 'content': task['prompt']['system']},
        {'role': 'user', 'content': f"{task['prompt']['user']}\n\nData Model Context: {task['prompt']['dataModelContext']}"}
    ]

    for iteration in range(1, MAX_ITERATIONS + 1):
        content, usage, error = call_model(messages)

        iter_result = {'iteration': iteration}

        if error:
            iter_result['error'] = error
            result['iterations'].append(iter_result)
            continue

        iter_result['raw_response'] = content
        iter_result['tokens'] = usage

        dax = extract_dax(content)
        name, expr = parse_measure(dax)

        iter_result['extracted_dax'] = dax
        iter_result['measure_name'] = name
        iter_result['expression'] = expr

        result['iterations'].append(iter_result)

        if name and expr:
            result['final_dax'] = dax
            result['measure_name'] = name
            result['expression'] = expr
            result['solved'] = True
            result['iteration_count'] = iteration
            break

        # Add feedback for next iteration
        feedback = "Could not parse a valid DAX measure from your response. Please provide ONLY the DAX measure definition in the format: MeasureName = Expression"
        messages.append({'role': 'assistant', 'content': content})
        messages.append({'role': 'user', 'content': feedback})

    return result


def main():
    if not API_KEY:
        print('ERROR: OPENROUTER_DAXBENCH_API_KEY not set')
        return

    import sys

    if len(sys.argv) > 1:
        task_id = sys.argv[1]
        task = load_task(task_id)
        if not task:
            print(f'Task not found: {task_id}')
            return
        tasks = [task]
    else:
        tasks = load_all_measure_tasks()

    print(f'Running {len(tasks)} tasks with Gemini 2.5 Flash')
    print('=' * 60)

    results = []

    for i, task in enumerate(tasks, 1):
        print(f'\n[{i}/{len(tasks)}] {task["id"]}: {task["title"]}')

        result = solve_task(task)
        results.append(result)

        if result['solved']:
            iters = result.get('iteration_count', len(result['iterations']))
            print(f'  [OK] Iteration {iters}')
            print(f'  Name: {result["measure_name"]}')
            print(f'  Expr: {result["expression"][:60]}...' if len(result.get('expression', '')) > 60 else f'  Expr: {result.get("expression", "N/A")}')
        else:
            print(f'  [FAIL] Could not extract valid DAX')

    # Summary
    print('\n' + '=' * 60)
    solved = sum(1 for r in results if r['solved'])
    print(f'SOLVED: {solved}/{len(results)}')

    # Output JSON for further processing
    output_file = Path(__file__).parent / 'gemini_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nResults saved to: {output_file}')


if __name__ == '__main__':
    main()
