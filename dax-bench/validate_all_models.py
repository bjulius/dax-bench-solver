import json
import subprocess
import sys

# Load data
with open('runs/2025-12-14_0117_api_responses_v4.json', 'r') as f:
    data = json.load(f)

# Table-returning task IDs
TABLE_TASKS = ['task-011', 'task-012', 'task-013', 'task-014']

# Results storage
results = {}

models = [
    'anthropic/claude-opus-4.5',
    'anthropic/claude-sonnet-4.5', 
    'anthropic/claude-haiku-4.5',
    'mistralai/mistral-small-3.1-24b-instruct'
]

for model in models:
    results[model] = {
        'passed': [],
        'failed': [],
        'total_tokens': 0,
        'total_cost': 0,
        'total_time': 0
    }
    
    tasks = [r for r in data if r['model'] == model]
    for t in tasks:
        # Track metrics
        results[model]['total_tokens'] += t['input_tokens'] + t['output_tokens']
        results[model]['total_cost'] += t['cost']
        results[model]['total_time'] += t['time']

# Save for tracking
with open('runs/validation_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("Models to validate:", len(models))
for model in models:
    tasks = [r for r in data if r['model'] == model]
    print(f"  {model.split('/')[-1]}: {len(tasks)} tasks")
    print(f"    Total cost: ${results[model]['total_cost']:.4f}")
    print(f"    Total time: {results[model]['total_time']:.2f}s")
