"""
BigfootDAX Benchmark Runner
===========================
Runs DAX generation tasks against multiple LLM models via OpenRouter,
validates results against Power BI, and compares to R/Python reference values.
"""

import json
import os
import time
import requests
from datetime import datetime
from pathlib import Path

# Configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_DAXBENCH_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Fix Unicode output on Windows
import sys
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# Models to benchmark
MODELS = {
    "deepseek-v3": "deepseek/deepseek-chat-v3.1",
    "haiku-4.5": "anthropic/claude-haiku-4.5",
    "opus-4.5": "anthropic/claude-opus-4.5"
}

def load_reference_values():
    """Load BigfootDAX reference values."""
    with open("bigfoot_reference_values.json", "r") as f:
        return json.load(f)

def build_prompt(task, schema):
    """Build the prompt for a BigfootDAX task."""
    system_prompt = """You are a DAX (Data Analysis Expressions) expert. Generate valid DAX measures for Power BI.

IMPORTANT RULES:
1. Return ONLY the DAX measure definition, no explanations
2. Use proper DAX syntax with table and column references like TableName[ColumnName]
3. Use DIVIDE() instead of / to handle division by zero
4. The model has these tables: bfro_reports, DateTable, _Measures
5. bfro_reports columns: date, state, county, number, temperature_high, classification, etc.
6. DateTable columns: Date, Year, Month, Quarter, etc.
7. There is a relationship: bfro_reports[date] -> DateTable[Date]

Format your response as:
```dax
MeasureName = <expression>
```"""

    user_prompt = f"""{task['prompt']}

Data Model Context:
- Table 'bfro_reports' contains {schema.get('record_count', 4586)} Bigfoot sighting reports
- Columns include: state, county, date, number (report ID), temperature_high, classification
- DateTable is related to bfro_reports[date]
- Expected result: {task.get('expected_value', 'N/A')}

Generate the DAX measure:"""

    return system_prompt, user_prompt

def call_openrouter(model_id: str, system_prompt: str, user_prompt: str, max_retries: int = 3):
    """Call OpenRouter API with retry logic."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/bigfootdax",
        "X-Title": "BigfootDAX Benchmark"
    }

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 2000
    }

    for attempt in range(max_retries):
        try:
            start_time = time.time()
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
            elapsed = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "content": data["choices"][0]["message"]["content"],
                    "usage": data.get("usage", {}),
                    "elapsed": elapsed,
                    "model": model_id
                }
            else:
                print(f"  API error (attempt {attempt+1}): {response.status_code} - {response.text[:200]}")
                time.sleep(2 ** attempt)
        except Exception as e:
            print(f"  Request error (attempt {attempt+1}): {e}")
            time.sleep(2 ** attempt)

    return {"success": False, "error": "Max retries exceeded", "model": model_id}

def parse_dax_response(response_text: str):
    """Extract DAX measure from model response."""
    import re

    # Try to find code block
    code_match = re.search(r'```(?:dax)?\s*(.*?)```', response_text, re.DOTALL | re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()

    # Try to find measure pattern directly
    measure_match = re.search(r'(\w+[\w\s]*)\s*=\s*(.+)', response_text, re.DOTALL)
    if measure_match:
        return response_text.strip()

    return response_text.strip()

def run_benchmark(tasks_to_run=None):
    """Run the full benchmark across all models and tasks."""
    ref = load_reference_values()
    tasks = ref["tasks"]
    schema = ref.get("schema", {})
    schema["record_count"] = ref.get("record_count", 4586)

    if tasks_to_run:
        tasks = {k: v for k, v in tasks.items() if k in tasks_to_run}

    results = {model_name: {} for model_name in MODELS}

    print("=" * 70)
    print("BigfootDAX Benchmark")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Tasks: {len(tasks)} | Models: {len(MODELS)}")
    print("=" * 70)

    for model_name, model_id in MODELS.items():
        print(f"\n{'='*70}")
        print(f"Model: {model_name} ({model_id})")
        print("=" * 70)

        for task_id, task in tasks.items():
            print(f"\n  [{task_id}] {task['title']}...")

            system_prompt, user_prompt = build_prompt(task, schema)
            response = call_openrouter(model_id, system_prompt, user_prompt)

            if response["success"]:
                dax = parse_dax_response(response["content"])
                results[model_name][task_id] = {
                    "task_title": task["title"],
                    "expected": task.get("expected_value"),
                    "dax_generated": dax,
                    "tokens": response.get("usage", {}),
                    "time": response.get("elapsed", 0),
                    "status": "generated"
                }
                print(f"    ✓ Generated ({response.get('elapsed', 0):.1f}s)")
                print(f"    DAX: {dax[:80]}..." if len(dax) > 80 else f"    DAX: {dax}")
            else:
                results[model_name][task_id] = {
                    "task_title": task["title"],
                    "expected": task.get("expected_value"),
                    "error": response.get("error"),
                    "status": "failed"
                }
                print(f"    ✗ Failed: {response.get('error')}")

            # Rate limiting
            time.sleep(1)

    # Save results
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    output_file = f"runs/bigfoot_benchmark_{timestamp}.json"
    os.makedirs("runs", exist_ok=True)

    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "models": list(MODELS.keys()),
            "tasks": list(tasks.keys()),
            "results": results
        }, f, indent=2)

    print(f"\n\nResults saved to: {output_file}")
    return results

if __name__ == "__main__":
    if not OPENROUTER_API_KEY:
        print("ERROR: Set OPENROUTER_DAXBENCH_API_KEY or OPENROUTER_API_KEY env var")
        sys.exit(1)

    # Run benchmark
    results = run_benchmark()

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for model_name, model_results in results.items():
        generated = sum(1 for r in model_results.values() if r.get("status") == "generated")
        print(f"{model_name}: {generated}/{len(model_results)} tasks generated")
