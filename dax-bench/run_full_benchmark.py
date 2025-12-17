#!/usr/bin/env python3
"""
DAX Bench - Full Benchmark with Schema Context
Generates DAX via OpenRouter with proper schema context.
Outputs validation commands for MCP execution.
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
RUNS_DIR = Path(__file__).parent / "runs"

# Compact schema context
SCHEMA_CONTEXT = """## Power BI Data Model

### Tables

**Sales** (fact table)
- Order Number (Int), Line Number (Int), Order Date (DateTime), Delivery Date (DateTime)
- CustomerKey (Int), StoreKey (Int), ProductKey (Int)
- Quantity (Int), Unit Price (Decimal), Net Price (Decimal), Unit Cost (Decimal)
- Currency Code (String), Exchange Rate (Double)

**Customer** (dimension)
- CustomerKey (Int), Gender, Name, City, State, Country, Continent, Birthday (DateTime), Age (Int)

**Product** (dimension)
- ProductKey (Int), Product Code, Product Name, Manufacturer, Brand, Color
- Unit Cost (Decimal), Unit Price (Decimal), Subcategory, Category

**Store** (dimension)
- StoreKey (Int), Store Code (Int), Name, Country, State
- Square Meters (Int), Open Date, Close Date, Status

**'Date'** (date table - use single quotes)
- Date (DateTime) [PRIMARY KEY - use for time intelligence]
- Year (Int), Month (Int), Day (Int), Day Name, Month Name
- Quarter (Int), Week of Year (Int)
- Fiscal Year, Fiscal Quarter, Fiscal Month
- Start of Year, End of Year, Start of Month, End of Month

**Budget** (disconnected table)
- Year (Int), Budget Amount (Decimal)

### Relationships
- Sales[CustomerKey] -> Customer[CustomerKey]
- Sales[ProductKey] -> Product[ProductKey]
- Sales[StoreKey] -> Store[StoreKey]
- Sales[Order Date] -> 'Date'[Date]

### DAX Conventions
- Quote table names with spaces: 'Date', 'Currency Exchange'
- Use 'Date'[Date] for time intelligence (TOTALYTD, SAMEPERIODLASTYEAR)
- Use DIVIDE() for safe division
- Use VALUES() with quotes: VALUES('Date'[Year])
"""


def load_all_tasks():
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


def call_openrouter(model, messages):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://daxbench.dev",
        "X-Title": "DAX Bench"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1500
    }
    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            data = response.json()
            return data, None
        return None, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)


def extract_dax(response_text):
    # Try code block first
    code_match = re.search(r'```(?:dax)?\s*(.*?)```', response_text, re.DOTALL | re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()
    # Try measure pattern
    measure_match = re.search(r'(\[?\w+[\w\s%-]*\]?\s*=\s*.+)', response_text, re.DOTALL)
    if measure_match:
        return measure_match.group(1).strip()
    return response_text.strip()


def parse_dax(dax):
    if dax.strip().upper().startswith('VAR'):
        return None, dax.strip()
    match = re.match(r'\[?([^\]=]+)\]?\s*=\s*(.+)', dax, re.DOTALL)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, dax.strip()


def detect_type(expression, task):
    expr_upper = expression.upper().strip()
    tags = task.get("tags", [])

    if "calculated-column" in tags:
        return "calc_column"
    if "table" in tags:
        return "table"

    table_funcs = ['SUMMARIZE', 'SUMMARIZECOLUMNS', 'SELECTCOLUMNS', 'ADDCOLUMNS(',
                   'UNION', 'INTERSECT', 'EXCEPT', 'CROSSJOIN', 'GENERATE',
                   'DATATABLE', 'TOPN', 'NATURALINNERJOIN']

    for func in table_funcs:
        if expr_upper.startswith(func):
            return "table"

    if 'EARLIER(' in expr_upper:
        return "calc_column"

    return "measure"


def build_query(name, expression, dax_type, task):
    if dax_type == "table":
        return f"EVALUATE {expression}"
    elif dax_type == "calc_column":
        table_refs = re.findall(r"(\w+)\[", expression)
        base_table = table_refs[0] if table_refs else "Product"
        safe_name = name or "Result"
        return f'EVALUATE TOPN(5, ADDCOLUMNS({base_table}, "{safe_name}", {expression}))'
    else:
        safe_name = name or "Result"
        return f'EVALUATE ROW("{safe_name}", {expression})'


def main():
    import sys

    if not API_KEY:
        print("ERROR: OPENROUTER_DAXBENCH_API_KEY not set")
        return

    model = sys.argv[1] if len(sys.argv) > 1 else "anthropic/claude-opus-4.5"

    # Allow running specific tasks
    task_filter = sys.argv[2] if len(sys.argv) > 2 else None

    all_tasks = load_all_tasks()

    if task_filter:
        tasks = [t for t in all_tasks if t["id"] == task_filter]
        if not tasks:
            print(f"Task not found: {task_filter}")
            return
    else:
        tasks = all_tasks

    print(f"DAX Bench - {len(tasks)} tasks")
    print(f"Model: {model}")
    print("=" * 70)

    RUNS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    model_safe = model.replace("/", "_")

    results = []
    total_cost = 0.0
    total_time = 0.0

    for i, task in enumerate(tasks, 1):
        print(f"\n[{i}/{len(tasks)}] {task['id']}: {task['title']}")

        # Build prompt with schema context
        system_prompt = task["prompt"]["system"]
        user_prompt = f"{task['prompt']['user']}\n\n{SCHEMA_CONTEXT}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Call LLM
        start = time.time()
        response, error = call_openrouter(model, messages)
        elapsed = time.time() - start
        total_time += elapsed

        result = {
            "task_id": task["id"],
            "title": task["title"],
            "complexity": task["complexity"],
            "category": task["category"],
            "time": elapsed
        }

        if error:
            result["status"] = "api_error"
            result["error"] = error
            print(f"  ERROR: {error[:50]}")
            results.append(result)
            continue

        try:
            content = response["choices"][0]["message"]["content"]
            usage = response.get("usage", {})
            cost = usage.get("cost", 0) or 0
            result["tokens"] = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
            result["cost"] = cost
            total_cost += cost
        except:
            result["status"] = "parse_error"
            print(f"  ERROR: Could not parse response")
            results.append(result)
            continue

        # Extract DAX
        dax = extract_dax(content)
        name, expression = parse_dax(dax)

        result["raw_response"] = content[:500]
        result["dax"] = dax
        result["name"] = name
        result["expression"] = expression

        if not expression:
            result["status"] = "no_expression"
            print(f"  ERROR: No expression found")
            results.append(result)
            continue

        # Build validation query
        dax_type = detect_type(expression, task)
        query = build_query(name, expression, dax_type, task)

        result["dax_type"] = dax_type
        result["validation_query"] = query
        result["status"] = "pending_validation"

        print(f"  OK: {dax_type} - {name or 'unnamed'}")
        print(f"  Query: {query[:60]}...")

        results.append(result)

    # Save results for MCP validation
    output_file = RUNS_DIR / f"{timestamp}_benchmark_{model_safe}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "model": model,
            "total_tasks": len(tasks),
            "total_cost": total_cost,
            "total_time": total_time,
            "results": results
        }, f, indent=2)

    # Print summary
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)

    pending = sum(1 for r in results if r.get("status") == "pending_validation")
    errors = sum(1 for r in results if r.get("status") not in ["pending_validation"])

    print(f"Pending validation: {pending}/{len(tasks)}")
    print(f"Errors: {errors}/{len(tasks)}")
    print(f"Total cost: ${total_cost:.4f}")
    print(f"Total time: {total_time:.1f}s")
    print(f"\nOutput: {output_file}")
    print("\nNext: Validate each task using run_dax MCP tool")


if __name__ == "__main__":
    main()
