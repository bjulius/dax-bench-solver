#!/usr/bin/env python3
"""
Run DAX Bench for multiple models - Phase 1: Get API responses
Saves responses to JSON for MCP validation phase
"""

import os
import json
import time
import re
import requests
from pathlib import Path
from datetime import datetime

API_KEY = os.environ.get('OPENROUTER_DAXBENCH_API_KEY', '')
OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
TASKS_DIR = Path(__file__).parent / 'tasks'
RUNS_DIR = Path(__file__).parent / 'runs'

MODELS = [
    'anthropic/claude-opus-4.5',
    'anthropic/claude-sonnet-4.5',
    'anthropic/claude-haiku-4.5',
    'mistralai/mistral-small-3.1-24b-instruct'
]

def load_all_tasks():
    tasks = []
    for level in ['basic', 'intermediate', 'advanced']:
        level_dir = TASKS_DIR / level
        if level_dir.exists():
            for task_file in sorted(level_dir.glob('task-*.json')):
                with open(task_file, 'r', encoding='utf-8') as f:
                    task = json.load(f)
                    task['_level'] = level
                    tasks.append(task)
    return tasks

def extract_dax(response_text):
    code_match = re.search(r'```(?:dax)?\s*(.*?)```', response_text, re.DOTALL | re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()
    measure_match = re.search(r'(\[?\w+[\w\s%-]*\]?\s*=\s*.+)', response_text, re.DOTALL)
    if measure_match:
        return measure_match.group(1).strip()
    return response_text.strip()

def parse_measure(dax_code):
    match = re.match(r'\[?([^\]=]+)\]?\s*=\s*(.+)', dax_code, re.DOTALL)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None

def call_model(model, task):
    messages = [
        {'role': 'system', 'content': task['prompt']['system']},
        {'role': 'user', 'content': f"{task['prompt']['user']}\n\nData Model Context: {task['prompt']['dataModelContext']}"}
    ]

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/bigfootdax',
        'X-Title': 'DAX Bench v4'
    }
    payload = {
        'model': model,
        'messages': messages,
        'temperature': 0.2,
        'max_tokens': 2000
    }

    start = time.time()
    try:
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
        elapsed = time.time() - start

        if resp.status_code != 200:
            return {'error': resp.text[:200], 'time': elapsed, 'task_id': task['id'], 'model': model}

        data = resp.json()
        content = data['choices'][0]['message']['content']
        usage = data.get('usage', {})
        dax = extract_dax(content)
        name, expr = parse_measure(dax)

        return {
            'task_id': task['id'],
            'task_title': task['title'],
            'complexity': task['complexity'],
            'category': task['category'],
            'model': model,
            'dax': dax,
            'measure_name': name,
            'expression': expr,
            'raw_response': content,
            'input_tokens': usage.get('prompt_tokens', 0),
            'output_tokens': usage.get('completion_tokens', 0),
            'cost': usage.get('cost', 0),
            'time': elapsed
        }
    except Exception as e:
        return {'error': str(e), 'time': time.time() - start, 'task_id': task['id'], 'model': model}


def main():
    if not API_KEY:
        print('ERROR: OPENROUTER_DAXBENCH_API_KEY not set')
        return

    # Load tasks
    tasks = load_all_tasks()
    print(f'Loaded {len(tasks)} tasks')
    print(f'Running benchmark for {len(MODELS)} models')
    print('Models:', [m.split('/')[-1] for m in MODELS])
    print('=' * 60)

    # Run all model/task combinations
    all_results = []
    total = len(MODELS) * len(tasks)
    completed = 0

    for model in MODELS:
        model_short = model.split('/')[-1]
        print(f'\n>>> {model_short}')
        model_results = []

        for task in tasks:
            result = call_model(model, task)
            all_results.append(result)
            model_results.append(result)
            completed += 1

            status = 'OK' if result.get('expression') else 'ERR'
            print(f'  [{completed}/{total}] {task["id"]}: {status} ({result.get("time", 0):.1f}s)')

        # Quick summary for this model
        ok_count = sum(1 for r in model_results if r.get('expression'))
        print(f'  >>> {model_short}: {ok_count}/{len(tasks)} parsed OK')

    # Save results for validation
    RUNS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    output_file = RUNS_DIR / f'{timestamp}_api_responses_v4.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f'\n\n{"="*60}')
    print(f'Saved {len(all_results)} responses to {output_file}')
    print('Ready for MCP validation phase')


if __name__ == '__main__':
    main()
