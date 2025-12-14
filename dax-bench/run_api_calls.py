#!/usr/bin/env python3
"""
DAX Bench API Caller - Makes OpenRouter API calls with schema context.

This script calls OpenRouter for each model/task combination and saves
the responses for later validation against Power BI.

Usage:
    python run_api_calls.py [--models opus,sonnet,haiku,mistral] [--tasks 1-30]
"""

import os
import json
import time
import re
import requests
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Configuration
API_KEY = os.environ.get("OPENROUTER_DAXBENCH_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TASKS_DIR = Path(__file__).parent / "tasks"
RUNS_DIR = Path(__file__).parent / "runs"

# Models to test (correct OpenRouter model IDs)
MODELS = {
    "opus": "anthropic/claude-opus-4.5",
    "sonnet": "anthropic/claude-sonnet-4.5",
    "haiku": "anthropic/claude-haiku-4.5",
    "mistral": "mistralai/mistral-small-3.1-24b-instruct",
    "gemini": "google/gemini-2.5-flash",
}

# Schema context (compact format with proper quoting)
SCHEMA_CONTEXT = """## Power BI Data Model

### Tables

**Sales** (fact)
Columns: Order Number, Line Number, Order Date, Delivery Date, CustomerKey, StoreKey, ProductKey, Quantity, Unit Price, Net Price, Unit Cost, Currency Code, Exchange Rate

**Customer** (dimension)
Columns: CustomerKey, Gender, Name, Address, City, State Code, State, Zip Code, Country Code, Country, Continent, Birthday, Age

**Product** (dimension)
Columns: ProductKey, Product Code, Product Name, Manufacturer, Brand, Color, Weight Unit Measure, Weight, Unit Cost, Unit Price, Subcategory Code, Subcategory, Category Code, Category

**Store** (dimension)
Columns: StoreKey, Store Code, Country, State, Name, Square Meters, Open Date, Close Date, Status

**'Date'** (date dimension)
Columns: Date [PK], Year, Start of Year, End of Year, Month, Start of Month, End of Month, Days in Month, Day, Day Name, Day of Week, Day of Year, Month Name, Quarter, Start of Quarter, End of Quarter, Week of Year, Week of Month, Start of Week, End of Week, Fiscal Year, Fiscal Quarter, Fiscal Month

**'Currency Exchange'** (dimension)
Columns: Date, FromCurrency, ToCurrency, Exchange

### Relationships
- Sales[CustomerKey] -> Customer[CustomerKey]
- Sales[ProductKey] -> Product[ProductKey]
- Sales[StoreKey] -> Store[StoreKey]
- Sales[Order Date] -> 'Date'[Date]
- 'Currency Exchange'[Date] -> 'Date'[Date]

### DAX Conventions
- Quote table names with spaces or reserved words: 'Date', 'Currency Exchange'
- Use 'Date'[Date] for time intelligence functions (TOTALYTD, SAMEPERIODLASTYEAR, etc.)
- Use DIVIDE() instead of / for safe division
- Use VALUES() or DISTINCT() with quotes: VALUES('Date'[Year])
"""


def load_tasks() -> List[dict]:
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


def parse_task_range(task_spec: str) -> List[str]:
    """Parse task specification into list of task IDs."""
    task_ids = []
    for part in task_spec.split(","):
        part = part.strip()
        if "-" in part and not part.startswith("task-"):
            start, end = part.split("-")
            for i in range(int(start), int(end) + 1):
                task_ids.append(f"task-{i:03d}")
        elif part.startswith("task-"):
            task_ids.append(part)
        else:
            task_ids.append(f"task-{int(part):03d}")
    return task_ids


def call_openrouter(model: str, messages: List[dict],
                    temperature: float = 0.2) -> Tuple[Optional[dict], dict]:
    """Make API call to OpenRouter."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/bigfootdax",
        "X-Title": "DAX Bench with Schema"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2000
    }

    start_time = time.time()
    try:
        response = requests.post(OPENROUTER_URL, headers=headers,
                                json=payload, timeout=120)
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
    code_match = re.search(r'```(?:dax)?\s*(.*?)```', response_text,
                          re.DOTALL | re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()

    # Otherwise look for measure pattern
    measure_match = re.search(r'(\[?\w+[\w\s]*\]?\s*=\s*.+)', response_text,
                             re.DOTALL)
    if measure_match:
        return measure_match.group(1).strip()

    return response_text.strip()


def main():
    parser = argparse.ArgumentParser(description="Run DAX Bench API calls")
    parser.add_argument("--models", "-m", type=str, default="opus,sonnet,haiku,mistral",
                       help="Comma-separated list of models to run")
    parser.add_argument("--tasks", "-t", type=str, default=None,
                       help="Task IDs to run (e.g., '1-10', 'task-001')")
    parser.add_argument("--delay", "-d", type=float, default=0.5,
                       help="Delay between API calls (seconds)")
    args = parser.parse_args()

    # Check API key
    if not API_KEY:
        print("ERROR: OPENROUTER_DAXBENCH_API_KEY not set")
        return 1

    # Parse models
    model_names = [m.strip() for m in args.models.split(",")]
    selected_models = {name: MODELS[name] for name in model_names if name in MODELS}

    if not selected_models:
        print(f"ERROR: No valid models. Available: {', '.join(MODELS.keys())}")
        return 1

    # Load and filter tasks
    all_tasks = load_tasks()
    print(f"Loaded {len(all_tasks)} tasks")

    if args.tasks:
        task_ids = set(parse_task_range(args.tasks))
        tasks = [t for t in all_tasks if t["id"] in task_ids]
    else:
        tasks = all_tasks

    print(f"Running {len(tasks)} tasks with {len(selected_models)} models")
    print(f"Models: {', '.join(selected_models.keys())}")
    print(f"Total API calls: {len(tasks) * len(selected_models)}")
    print()

    # Run benchmarks
    results = []
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")

    for model_name, model_id in selected_models.items():
        print(f"\n{'='*50}")
        print(f"Running {model_name} ({model_id})")
        print("="*50)

        for i, task in enumerate(tasks, 1):
            task_id = task["id"]

            # Build prompt with schema context
            system_prompt = task["prompt"]["system"]
            user_prompt = f"{task['prompt']['user']}\n\n{SCHEMA_CONTEXT}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Call API
            print(f"  [{i}/{len(tasks)}] {task_id}: {task['title'][:40]}...", end=" ")
            response, meta = call_openrouter(model_id, messages)

            result = {
                "task_id": task_id,
                "title": task["title"],
                "complexity": task["complexity"],
                "category": task["category"],
                "model": model_id,
                "model_short": model_name,
                "time": meta.get("elapsed", 0),
                "error": meta.get("error"),
                "valid": None,  # To be filled by validation
            }

            if response:
                try:
                    content = response["choices"][0]["message"]["content"]
                    usage = response.get("usage", {})
                    result["input_tokens"] = usage.get("prompt_tokens", 0)
                    result["output_tokens"] = usage.get("completion_tokens", 0)
                    result["dax"] = extract_dax(content)
                    result["raw_response"] = content
                    print(f"OK ({meta['elapsed']:.2f}s)")
                except (KeyError, IndexError) as e:
                    result["error"] = f"Parse error: {e}"
                    print(f"PARSE ERROR")
            else:
                print(f"API ERROR: {result['error'][:50]}...")

            results.append(result)

            # Delay between calls
            if args.delay > 0:
                time.sleep(args.delay)

    # Save results
    RUNS_DIR.mkdir(exist_ok=True)
    output_file = RUNS_DIR / f"{timestamp}_api_responses_with_schema.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*50}")
    print(f"COMPLETE")
    print("="*50)
    print(f"Saved {len(results)} results to {output_file}")
    print()

    # Summary
    by_model = {}
    for r in results:
        model = r["model_short"]
        if model not in by_model:
            by_model[model] = {"total": 0, "errors": 0}
        by_model[model]["total"] += 1
        if r.get("error"):
            by_model[model]["errors"] += 1

    print("Summary:")
    for model, stats in by_model.items():
        success = stats["total"] - stats["errors"]
        print(f"  {model}: {success}/{stats['total']} API calls successful")

    print(f"\nNext step: Validate responses against Power BI using MCP tools")
    return 0


if __name__ == "__main__":
    exit(main())
