#!/usr/bin/env python3
"""Run specific missing tasks for a model"""
import os
import json
import time
import re
import requests
from datetime import datetime
from pathlib import Path

API_KEY = os.environ.get('OPENROUTER_DAXBENCH_API_KEY', '')
BASE_URL = 'https://openrouter.ai/api/v1/chat/completions'
MAX_ITERATIONS = 10
TASKS_DIR = Path(__file__).parent / 'tasks'
RUNS_DIR = Path(__file__).parent / 'runs'
MODEL = 'google/gemini-2.5-pro'

def call_openrouter(model, messages, temperature=0.2):
    headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
    payload = {'model': model, 'messages': messages, 'temperature': temperature, 'max_tokens': 1000}
    start = time.time()
    try:
        resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=120)
        elapsed = time.time() - start
        if resp.status_code != 200:
            return None, {'error': resp.text, 'elapsed': elapsed}
        return resp.json(), {'elapsed': elapsed}
    except Exception as e:
        return None, {'error': str(e), 'elapsed': time.time() - start}

def extract_dax(text):
    m = re.search(r'```(?:dax)?\s*(.*?)```', text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r'(\[?\w+[\w\s]*\]?\s*=\s*.+)', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()

def normalize_dax(dax):
    return re.sub(r'\s+', ' ', dax).strip().lower()

def parse_measure(dax):
    m = re.match(r'\[?([^\]=]+)\]?\s*=\s*(.+)', dax, re.DOTALL)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None, None

def validate_dax(gen, exp, alts):
    gn = normalize_dax(gen)
    if normalize_dax(exp) == gn:
        return True
    for alt in alts:
        if normalize_dax(alt) == gn:
            return True
    _, ge = parse_measure(gen)
    _, ee = parse_measure(exp)
    if ge and ee and normalize_dax(ge) == normalize_dax(ee):
        return True
    for alt in alts:
        _, ae = parse_measure(alt)
        if ae and ge and normalize_dax(ge) == normalize_dax(ae):
            return True
    return False

def main():
    if not API_KEY:
        print("ERROR: OPENROUTER_DAXBENCH_API_KEY not set")
        return

    # Load specific tasks
    tasks_to_run = []
    for task_id in ['task-028', 'task-030']:
        task_file = TASKS_DIR / 'advanced' / f'{task_id}.json'
        with open(task_file, 'r') as f:
            task = json.load(f)
            tasks_to_run.append(task)

    print(f'Running 2 missing tasks for {MODEL}')
    print('-' * 50)

    for task in tasks_to_run:
        print(f"\n{task['id']}: {task['title']}")
        sys_prompt = task['prompt']['system']
        usr_prompt = f"{task['prompt']['user']}\n\nData Model Context: {task['prompt']['dataModelContext']}"
        messages = [{'role': 'system', 'content': sys_prompt}, {'role': 'user', 'content': usr_prompt}]

        solved = False
        final_dax = None
        for iteration in range(1, MAX_ITERATIONS + 1):
            resp, meta = call_openrouter(MODEL, messages)
            if resp is None:
                print(f'  Iter {iteration}: API Error - {meta.get("error", "Unknown")[:100]}')
                messages.append({'role': 'assistant', 'content': '[Error]'})
                messages.append({'role': 'user', 'content': 'API call failed. Try again.'})
                continue

            content = resp['choices'][0]['message']['content']
            dax = extract_dax(content)
            valid = validate_dax(dax, task['expectedOutput']['dax'], task['expectedOutput'].get('alternativeCorrect', []))

            if valid:
                print(f'  Iter {iteration}: SOLVED')
                solved = True
                final_dax = dax
                break
            else:
                print(f'  Iter {iteration}: Incorrect, retrying...')
                feedback = f"Your DAX doesn't match expected. Expected pattern: {task['expectedOutput']['dax'][:150]}..."
                if task.get('hints'):
                    feedback += f"\nHints: {task['hints'][0]}"
                messages.append({'role': 'assistant', 'content': content})
                messages.append({'role': 'user', 'content': feedback})

        # Save result
        ts = datetime.now().strftime('%Y-%m-%d_%H%M')
        model_safe = MODEL.replace('/', '_')
        status = "SOLVED" if solved else "FAILED"

        log = f"""# DAX Bench Run - {task['id']}

| Field | Value |
|-------|-------|
| **Task** | {task['id']} - {task['title']} |
| **Model** | {MODEL} |
| **Timestamp** | {datetime.now().isoformat()} |
| **Result** | {'✅ ' + status if solved else '❌ ' + status} |

## Final DAX
```dax
{final_dax if final_dax else 'N/A'}
```
"""
        with open(RUNS_DIR / f'{ts}_{task["id"]}_{model_safe}.md', 'w', encoding='utf-8') as f:
            f.write(log)

        if solved:
            print(f'  ✅ Saved result')
        else:
            print(f'  ❌ FAILED after {MAX_ITERATIONS} iterations')

    print('\nDone!')

if __name__ == '__main__':
    main()
