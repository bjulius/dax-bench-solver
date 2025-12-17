#!/usr/bin/env python3
"""
DAX Bench - Mistral Benchmark Runner
Runs Mistral through all 30 DAX tasks with iterative feedback.

This script handles:
1. Loading tasks and schema context
2. Calling OpenRouter API for Mistral responses
3. Static validation against DAX function list
4. Outputting results for MCP validation
"""

import os
import json
import time
import re
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

# Configuration
API_KEY = os.environ.get("OPENROUTER_DAXBENCH_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MISTRAL_MODEL = "mistralai/mistral-small-3.1-24b-instruct"

BASE_DIR = Path(__file__).parent
TASKS_DIR = BASE_DIR / "tasks"
RUNS_DIR = BASE_DIR / "runs"

# Load DAX functions reference
with open(BASE_DIR / "dax_functions_reference.json", "r") as f:
    DAX_FUNCTIONS = json.load(f)
VALID_FUNCTIONS = set(f.upper() for f in DAX_FUNCTIONS["valid_functions"])
EXCEL_FUNCTIONS = set(f.upper() for f in DAX_FUNCTIONS["common_excel_functions_not_in_dax"])
SQL_FUNCTIONS = set(f.upper() for f in DAX_FUNCTIONS["common_sql_functions_not_in_dax"])

# Load reference values
with open(BASE_DIR / "reference_values.json", "r") as f:
    REFERENCE_VALUES = json.load(f)

# Schema context (formatted from Power BI model)
SCHEMA_CONTEXT = """
## Power BI Model Schema

### Tables and Columns:

**Sales** (Fact table)
- Order Number (Int64), Line Number (Int64)
- Order Date (DateTime), Delivery Date (DateTime)
- CustomerKey (Int64), StoreKey (Int64), ProductKey (Int64)
- Quantity (Int64), Unit Price (Decimal), Net Price (Decimal), Unit Cost (Decimal)
- Currency Code (String), Exchange Rate (Double)

**Product** (Dimension)
- ProductKey (Int64), Product Code (String), Product Name (String)
- Manufacturer (String), Brand (String), Color (String)
- Weight (Double), Unit Cost (Decimal), Unit Price (Decimal)
- Subcategory Code (String), Subcategory (String)
- Category Code (String), Category (String)

**Customer** (Dimension)
- CustomerKey (Int64), Gender (String), Name (String)
- Address (String), City (String), State Code (String), State (String)
- Zip Code (String), Country Code (String), Country (String)
- Continent (String), Birthday (DateTime), Age (Int64)

**Date** (Dimension - marked as date table)
- Date (DateTime, Key), Year (Int64), Month (Int64), Quarter (Int64)
- Day (Int64), Day Name (String), Day of Week (Int64)
- Month Name (String), Week of Year (Int64)
- Fiscal Year (Int64), Fiscal Quarter (Int64), Fiscal Month (Int64)

**Store** (Dimension)
- StoreKey (Int64), Store Code (Int64), Country (String)
- State (String), Name (String), Square Meters (Int64)
- Open Date (DateTime), Close Date (DateTime), Status (String)

**Budget** (Disconnected table)
- Year (Int64), Budget Amount (Decimal)

### Relationships:
- Sales[CustomerKey] -> Customer[CustomerKey] (Many-to-One)
- Sales[ProductKey] -> Product[ProductKey] (Many-to-One)
- Sales[StoreKey] -> Store[StoreKey] (Many-to-One)
- Sales[Order Date] -> Date[Date] (Many-to-One)

### Existing Measures:
- [Total Sales] = SUM(Sales[Net Price])
- [Total Net Price] = SUM(Sales[Net Price])
"""


def load_all_tasks() -> List[dict]:
    """Load all 30 task JSON files."""
    tasks = []
    for level in ["basic", "intermediate", "advanced"]:
        level_dir = TASKS_DIR / level
        if level_dir.exists():
            for task_file in sorted(level_dir.glob("task-*.json")):
                with open(task_file, "r", encoding="utf-8") as f:
                    task = json.load(f)
                    task["_level"] = level
                    tasks.append(task)
    return sorted(tasks, key=lambda t: int(t["id"].split("-")[1]))


def call_openrouter(messages: List[dict], temperature: float = 0.2) -> Tuple[Optional[str], dict]:
    """Make API call to OpenRouter with Mistral model."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/bigfootdax",
        "X-Title": "DAX Bench Mistral"
    }
    payload = {
        "model": MISTRAL_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2000
    }

    start_time = time.time()
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
        elapsed = time.time() - start_time

        if response.status_code != 200:
            return None, {"error": response.text, "elapsed": elapsed, "status": response.status_code}

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return content, {
            "elapsed": elapsed,
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "cost": usage.get("total_cost", 0)
        }
    except Exception as e:
        return None, {"error": str(e), "elapsed": time.time() - start_time}


def extract_dax(response_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract measure name and expression from model response."""
    # Clean markdown code blocks
    text = response_text.strip()
    code_match = re.search(r'```(?:dax)?\s*(.*?)```', text, re.DOTALL | re.IGNORECASE)
    if code_match:
        text = code_match.group(1).strip()

    # Parse measure = expression
    match = re.match(r'\[?([^\]=\n]+)\]?\s*=\s*(.+)', text, re.DOTALL)
    if match:
        name = match.group(1).strip()
        expr = match.group(2).strip()
        return name, expr

    # If no equals sign, assume the whole thing is the expression
    return None, text


def extract_functions_from_dax(expression: str) -> List[str]:
    """Extract all function calls from a DAX expression."""
    # Match word followed by opening paren
    pattern = r'\b([A-Z][A-Z0-9_.]*)\s*\('
    matches = re.findall(pattern, expression, re.IGNORECASE)
    return [m.upper() for m in matches]


def static_validate(expression: str) -> Tuple[bool, List[str]]:
    """
    Validate DAX expression against known function list.
    Returns (is_valid, list_of_errors).
    """
    functions = extract_functions_from_dax(expression)
    errors = []

    for func in functions:
        func_upper = func.upper()
        if func_upper in EXCEL_FUNCTIONS:
            errors.append(f"'{func}' is an Excel function, not DAX. Use CALCULATE with FILTER or SUMX instead.")
        elif func_upper in SQL_FUNCTIONS:
            errors.append(f"'{func}' is a SQL function, not DAX. Use RANKX with DENSE parameter for ranking.")
        elif func_upper not in VALID_FUNCTIONS:
            # Check for common typos
            if func_upper == "SAMEPERIODLASTDAY":
                errors.append(f"'{func}' does not exist. Use SAMEPERIODLASTYEAR or DATEADD for date comparisons.")
            elif func_upper == "DENSITYRANK" or func_upper == "DENSERANK":
                errors.append(f"'{func}' does not exist. Use RANKX with DENSE parameter: RANKX(table, expr, , DESC, DENSE)")
            else:
                errors.append(f"'{func}' is not a valid DAX function.")

    return len(errors) == 0, errors


def run_single_task(task: dict, max_iterations: int = 10) -> dict:
    """
    Run a single task with iterative feedback.
    Returns result dict with all attempts and final status.
    """
    task_id = task["id"]
    print(f"\n{'='*60}")
    print(f"Running {task_id}: {task['title']}")
    print(f"Complexity: {task['complexity']}")
    print(f"{'='*60}")

    result = {
        "task_id": task_id,
        "title": task["title"],
        "complexity": task["complexity"],
        "category": task["category"],
        "attempts": [],
        "final_status": "pending",
        "final_expression": None,
        "iterations": 0,
        "total_time": 0,
        "total_tokens": {"input": 0, "output": 0}
    }

    # Build initial prompt
    system_prompt = task["prompt"]["system"]
    user_prompt = f"{task['prompt']['user']}\n\n{SCHEMA_CONTEXT}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Iteration {iteration} ---")

        # Call API
        response_text, meta = call_openrouter(messages)
        result["total_time"] += meta.get("elapsed", 0)
        result["total_tokens"]["input"] += meta.get("input_tokens", 0)
        result["total_tokens"]["output"] += meta.get("output_tokens", 0)

        if response_text is None:
            attempt = {
                "iteration": iteration,
                "error": meta.get("error", "API call failed"),
                "status": "api_error"
            }
            result["attempts"].append(attempt)
            print(f"API Error: {meta.get('error')}")
            continue

        # Extract DAX
        measure_name, expression = extract_dax(response_text)

        if not expression:
            attempt = {
                "iteration": iteration,
                "response": response_text[:500],
                "error": "Could not extract DAX expression from response",
                "status": "parse_error"
            }
            result["attempts"].append(attempt)

            # Add feedback for next iteration
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": "I couldn't parse your response. Please provide ONLY the DAX measure in the format: MeasureName = Expression"})
            continue

        print(f"Extracted: {measure_name} = {expression[:100]}...")

        # Static validation
        is_valid, errors = static_validate(expression)

        attempt = {
            "iteration": iteration,
            "measure_name": measure_name,
            "expression": expression,
            "static_valid": is_valid,
            "static_errors": errors if not is_valid else [],
            "status": "static_pass" if is_valid else "static_fail"
        }

        if not is_valid:
            print(f"Static validation FAILED: {errors}")
            result["attempts"].append(attempt)

            # Add feedback for next iteration
            error_msg = "Your DAX expression contains errors:\n" + "\n".join(f"- {e}" for e in errors)
            error_msg += "\n\nPlease correct these errors and provide a valid DAX expression."

            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": error_msg})
            continue

        print(f"Static validation PASSED")

        # If we reach here, static validation passed
        # Mark for MCP validation (to be done externally)
        attempt["status"] = "ready_for_mcp"
        attempt["mcp_query"] = f'EVALUATE ROW("Result", {expression})'
        result["attempts"].append(attempt)
        result["final_expression"] = expression
        result["final_status"] = "static_pass"
        result["iterations"] = iteration

        print(f"Ready for MCP validation")
        break

    if result["final_status"] == "pending":
        result["final_status"] = "max_iterations"
        result["iterations"] = max_iterations

    return result


def main():
    """Run benchmark on all tasks."""
    if not API_KEY:
        print("ERROR: OPENROUTER_DAXBENCH_API_KEY not set!")
        return

    print("="*70)
    print("DAX Bench - Mistral Benchmark Runner")
    print(f"Model: {MISTRAL_MODEL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*70)

    tasks = load_all_tasks()
    print(f"\nLoaded {len(tasks)} tasks")

    results = []
    start_time = time.time()

    for task in tasks:
        result = run_single_task(task)
        results.append(result)

        # Save intermediate results
        output_file = RUNS_DIR / f"mistral_benchmark_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(output_file, "w") as f:
            json.dump({
                "model": MISTRAL_MODEL,
                "timestamp": datetime.now().isoformat(),
                "status": "in_progress",
                "results": results
            }, f, indent=2)

    total_time = time.time() - start_time

    # Final summary
    static_pass = sum(1 for r in results if r["final_status"] == "static_pass")
    static_fail = sum(1 for r in results if r["final_status"] != "static_pass")
    first_try = sum(1 for r in results if r["iterations"] == 1 and r["final_status"] == "static_pass")
    avg_iterations = sum(r["iterations"] for r in results) / len(results)

    summary = {
        "model": MISTRAL_MODEL,
        "timestamp": datetime.now().isoformat(),
        "status": "complete",
        "summary": {
            "total_tasks": len(results),
            "static_pass": static_pass,
            "static_fail": static_fail,
            "first_try_success": first_try,
            "first_try_rate": round(first_try / len(results) * 100, 1),
            "avg_iterations": round(avg_iterations, 2),
            "total_time": round(total_time, 2)
        },
        "results": results
    }

    # Save final results
    output_file = RUNS_DIR / f"mistral_benchmark_{datetime.now().strftime('%Y%m%d_%H%M')}_final.json"
    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "="*70)
    print("BENCHMARK COMPLETE")
    print("="*70)
    print(f"Static Pass: {static_pass}/{len(results)} ({static_pass/len(results)*100:.1f}%)")
    print(f"First-try Success: {first_try}/{len(results)} ({first_try/len(results)*100:.1f}%)")
    print(f"Avg Iterations: {avg_iterations:.2f}")
    print(f"Total Time: {total_time:.1f}s")
    print(f"Results saved to: {output_file}")

    # Output expressions ready for MCP validation
    print("\n" + "="*70)
    print("EXPRESSIONS READY FOR MCP VALIDATION:")
    print("="*70)
    for r in results:
        if r["final_expression"]:
            print(f"\n{r['task_id']}: {r['title']}")
            print(f"  Expression: {r['final_expression'][:100]}...")

    return summary


if __name__ == "__main__":
    main()
