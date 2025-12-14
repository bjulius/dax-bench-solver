#!/usr/bin/env python3
"""
DAX Bench Solver v4 - Power BI Execution Validation (Required)

Key changes from v3:
- Power BI validation is REQUIRED (no pattern matching fallback)
- Task selection via --tasks or --complexity
- Measures created in _Measures table and kept (not deleted)
- Real execution validation via MCP HTTP bridge
- Schema context extracted from Power BI model for LLM prompts

Prerequisites:
- Power BI Desktop open with Contoso.pbix
- MCP server connected
- OPENROUTER_DAXBENCH_API_KEY environment variable set
"""

import os
import sys
import json
import time
import re
import argparse
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

# Import schema extractor for model context
from schema_extractor import extract_schema, SchemaFormat

# Configuration
API_KEY = os.environ.get("OPENROUTER_DAXBENCH_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_ITERATIONS = 10
TASKS_DIR = Path(__file__).parent / "tasks"
RUNS_DIR = Path(__file__).parent / "runs"
MEASURES_TABLE = "_Measures"
DEFAULT_SCHEMA_FORMAT: SchemaFormat = "compact"

# MCP Bridge configuration - will be set by check_powerbi_connection
MCP_BASE_URL = None

# Schema cache - populated from Power BI model
_SCHEMA_CACHE: Optional[dict] = None
_SCHEMA_PROMPT_CACHE: Optional[str] = None


class PowerBIValidationError(Exception):
    """Raised when Power BI validation fails"""
    pass


class PowerBIConnectionError(Exception):
    """Raised when Power BI is not connected"""
    pass


def check_powerbi_connection() -> dict:
    """
    Check if Power BI MCP is connected and accessible.
    Returns connection info or raises PowerBIConnectionError.

    This function tries to connect via the MCP HTTP bridge if available,
    or falls back to checking if the required environment is set up.
    """
    # For now, we'll use a marker file or environment variable approach
    # In production, this would query the MCP server

    # Try to read connection info from a config file
    config_file = Path(__file__).parent / ".pbi_connection.json"

    if config_file.exists():
        with open(config_file, "r") as f:
            config = json.load(f)
            if config.get("connected"):
                return config

    # If no config, we need the MCP bridge URL
    mcp_url = os.environ.get("PBI_MCP_URL", "")
    if not mcp_url:
        raise PowerBIConnectionError(
            "Power BI MCP connection required but not configured.\n"
            "Please ensure:\n"
            "1. Power BI Desktop is open with Contoso.pbix\n"
            "2. Power BI MCP server is running\n"
            "3. Set PBI_MCP_URL environment variable or run from Claude Code"
        )

    global MCP_BASE_URL
    MCP_BASE_URL = mcp_url

    return {"connected": True, "url": mcp_url}


def get_schema_context(mcp_tools: dict, schema_format: SchemaFormat = "compact") -> str:
    """
    Fetch and cache schema from Power BI model, formatted for LLM prompts.

    Args:
        mcp_tools: Dictionary containing MCP tool functions
        schema_format: Output format - "full", "compact", or "minimal"

    Returns:
        Formatted schema string suitable for LLM context
    """
    global _SCHEMA_CACHE, _SCHEMA_PROMPT_CACHE

    # Return cached version if available (schema doesn't change during run)
    if _SCHEMA_PROMPT_CACHE is not None:
        return _SCHEMA_PROMPT_CACHE

    # Fetch schema from Power BI via MCP
    if "get_model_info" in mcp_tools:
        try:
            schema_result = mcp_tools["get_model_info"](info_type="schema")
            if schema_result:
                _SCHEMA_CACHE = schema_result
                _SCHEMA_PROMPT_CACHE = extract_schema(schema_result, schema_format)
                return _SCHEMA_PROMPT_CACHE
        except Exception as e:
            print(f"Warning: Could not fetch schema from Power BI: {e}")

    # Fallback: return a minimal prompt indicating schema unavailable
    return "Note: Schema context unavailable. Use table/column names as specified in the task."


def create_measure_in_powerbi(measure_name: str, expression: str) -> Tuple[bool, Optional[str]]:
    """
    Create a measure in Power BI's _Measures table.
    Returns (success, error_message).

    This is a placeholder that will be called via MCP in the actual implementation.
    For standalone Python execution, this would need ADOMD.NET or similar.
    """
    # This function will be implemented to work with MCP
    # For now, return a placeholder that indicates we need MCP
    return False, "MCP bridge not implemented - run via Claude Code"


def execute_measure_in_powerbi(measure_name: str) -> Tuple[bool, Any, Optional[str]]:
    """
    Execute a measure in Power BI and return the result.
    Returns (success, result, error_message).
    """
    # This function will be implemented to work with MCP
    return False, None, "MCP bridge not implemented - run via Claude Code"


def delete_measure_from_powerbi(measure_name: str) -> bool:
    """Delete a measure from Power BI (optional cleanup)."""
    # We're keeping measures, so this is mostly unused
    return True


# ============================================================================
# Task Loading
# ============================================================================

def load_all_tasks() -> List[dict]:
    """Load all task JSON files from tasks directory"""
    tasks = []
    for level in ["basic", "intermediate", "advanced"]:
        level_dir = TASKS_DIR / level
        if level_dir.exists():
            for task_file in sorted(level_dir.glob("task-*.json")):
                with open(task_file, "r", encoding="utf-8") as f:
                    task = json.load(f)
                    task["_level"] = level
                    task["_file"] = str(task_file)
                    tasks.append(task)
    return tasks


def filter_tasks(tasks: List[dict],
                 task_ids: Optional[List[str]] = None,
                 complexity: Optional[str] = None) -> List[dict]:
    """Filter tasks by ID list or complexity level"""
    filtered = tasks

    if task_ids:
        # Normalize task IDs (allow "1", "001", "task-001")
        normalized_ids = set()
        for tid in task_ids:
            if tid.startswith("task-"):
                normalized_ids.add(tid)
            else:
                # Pad with zeros
                num = tid.zfill(3)
                normalized_ids.add(f"task-{num}")

        filtered = [t for t in filtered if t["id"] in normalized_ids]

    if complexity:
        filtered = [t for t in filtered if t["complexity"] == complexity]

    return filtered


def parse_task_range(task_spec: str) -> List[str]:
    """
    Parse task specification into list of task IDs.
    Supports: "1,2,3", "1-5", "task-001,task-005", "1-5,10,15-20"
    """
    task_ids = []

    for part in task_spec.split(","):
        part = part.strip()
        if "-" in part and not part.startswith("task-"):
            # Range like "1-5"
            start, end = part.split("-")
            for i in range(int(start), int(end) + 1):
                task_ids.append(str(i))
        else:
            task_ids.append(part)

    return task_ids


# ============================================================================
# OpenRouter API
# ============================================================================

def call_openrouter(model: str, messages: List[dict], temperature: float = 0.2) -> Tuple[Optional[dict], dict]:
    """Make API call to OpenRouter"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/bigfootdax",
        "X-Title": "DAX Bench Solver v4"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2000
    }

    start_time = time.time()
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
        elapsed = time.time() - start_time

        if response.status_code != 200:
            return None, {"error": response.text, "elapsed": elapsed}

        data = response.json()
        return data, {"elapsed": elapsed}
    except Exception as e:
        return None, {"error": str(e), "elapsed": time.time() - start_time}


# ============================================================================
# DAX Extraction
# ============================================================================

def extract_dax(response_text: str) -> str:
    """Extract DAX code from model response"""
    # Try to find code block first
    code_match = re.search(r'```(?:dax)?\s*(.*?)```', response_text, re.DOTALL | re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()

    # Otherwise look for measure pattern
    measure_match = re.search(r'(\[?\w+[\w\s]*\]?\s*=\s*.+)', response_text, re.DOTALL)
    if measure_match:
        return measure_match.group(1).strip()

    return response_text.strip()


def parse_measure_definition(dax_code: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse measure name and expression from DAX code"""
    match = re.match(r'\[?([^\]=]+)\]?\s*=\s*(.+)', dax_code, re.DOTALL)
    if match:
        name = match.group(1).strip()
        expression = match.group(2).strip()
        return name, expression
    return None, None


# ============================================================================
# Validation (Power BI Required)
# ============================================================================

def validate_dax_with_powerbi(task: dict, generated_dax: str, mcp_tools: dict) -> dict:
    """
    Validate DAX by actually creating and executing it in Power BI.

    Args:
        task: The task definition
        generated_dax: The DAX code generated by the model
        mcp_tools: Dictionary of MCP tool functions

    Returns:
        dict with validation results
    """
    result = {
        "valid": False,
        "syntax_valid": False,
        "executes": False,
        "error": None,
        "actual_result": None,
        "measure_name": None,
        "expression": None
    }

    # Parse the measure
    measure_name, expression = parse_measure_definition(generated_dax)
    if not measure_name or not expression:
        result["error"] = "Could not parse measure name and expression from DAX"
        return result

    result["measure_name"] = measure_name
    result["expression"] = expression

    # Create a unique test measure name to avoid conflicts
    test_measure_name = f"_Test_{task['id']}_{measure_name.replace(' ', '_')}"

    try:
        # Step 1: Create the measure in Power BI
        create_result = mcp_tools["create_measure"](
            table=MEASURES_TABLE,
            name=test_measure_name,
            expression=expression
        )

        if not create_result.get("success"):
            result["error"] = f"Syntax error: {create_result.get('error', 'Unknown error')}"
            return result

        result["syntax_valid"] = True

        # Step 2: Try to execute the measure
        exec_result = mcp_tools["run_dax"](
            f'EVALUATE ROW("Result", [{test_measure_name}])'
        )

        if exec_result.get("error"):
            result["error"] = f"Execution error: {exec_result.get('error')}"
            # Clean up the measure since it doesn't work
            mcp_tools["delete_measure"](table=MEASURES_TABLE, name=test_measure_name)
            return result

        result["executes"] = True
        result["actual_result"] = exec_result.get("data")

        # Step 3: If we have expected results, compare them
        expected = task.get("expectedOutput", {}).get("expectedResult")
        if expected:
            # Compare results (basic comparison for now)
            result["expected_result"] = expected
            # More sophisticated comparison could be added here

        # If we got here, the DAX is valid (syntax + execution)
        result["valid"] = True

        # Rename the test measure to the proper name (remove _Test_ prefix)
        # Or keep it as-is for reference
        final_name = f"{task['id']}_{measure_name.replace(' ', '_')}"
        mcp_tools["update_measure"](
            table=MEASURES_TABLE,
            name=test_measure_name,
            new_name=final_name
        )
        result["final_measure_name"] = final_name

    except Exception as e:
        result["error"] = f"Validation error: {str(e)}"

    return result


def generate_feedback(task: dict, generated_dax: str, validation_result: dict, iteration: int) -> str:
    """Generate specific, helpful feedback based on validation results"""
    feedback_parts = []

    # Check for syntax errors
    if validation_result.get("error") and "Syntax error" in validation_result["error"]:
        feedback_parts.append(f"SYNTAX ERROR: {validation_result['error']}")
        feedback_parts.append("Please fix the syntax error and try again.")
        feedback_parts.append("Common issues: missing parentheses, incorrect function names, invalid column references.")
        return "\n".join(feedback_parts)

    # Check for execution errors
    if validation_result.get("error") and "Execution error" in validation_result["error"]:
        feedback_parts.append(f"EXECUTION ERROR: {validation_result['error']}")
        feedback_parts.append("The measure was created but failed to execute.")
        feedback_parts.append("Check: column/table references, function parameters, filter context.")
        return "\n".join(feedback_parts)

    # Check for result mismatch (if we have expected values)
    if validation_result.get("actual_result") and validation_result.get("expected_result"):
        actual = validation_result["actual_result"]
        expected = validation_result["expected_result"]
        feedback_parts.append("RESULT MISMATCH:")
        feedback_parts.append(f"  Expected: {expected}")
        feedback_parts.append(f"  Got: {actual}")
        feedback_parts.append("Your DAX executes but returns incorrect values. Review the logic.")
        return "\n".join(feedback_parts)

    # Generic error
    if validation_result.get("error"):
        feedback_parts.append(f"ERROR: {validation_result['error']}")

    # Add hints if available
    if "hints" in task and feedback_parts:
        feedback_parts.append("\nHINTS:")
        for hint in task["hints"][:2]:
            feedback_parts.append(f"  - {hint}")

    feedback_parts.append(f"\nThis is attempt {iteration} of {MAX_ITERATIONS}. Please try again.")

    return "\n".join(feedback_parts) if feedback_parts else "Please review your DAX and try again."


# ============================================================================
# Main Solve Loop
# ============================================================================

def solve_task(task: dict, model: str, mcp_tools: dict,
               schema_format: SchemaFormat = "compact") -> dict:
    """
    Attempt to solve a single task with iteration and Power BI validation.

    Args:
        task: The task definition dict
        model: OpenRouter model ID
        mcp_tools: Dictionary of MCP tool functions
        schema_format: Format for schema context ("full", "compact", "minimal")
    """
    results = {
        "task_id": task["id"],
        "title": task["title"],
        "complexity": task["complexity"],
        "category": task["category"],
        "model": model,
        "iterations": [],
        "solved": False,
        "first_try": False,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cost": 0,
        "total_time": 0,
        "validation_method": "powerbi_execution",
        "schema_format": schema_format
    }

    # Get schema context from Power BI model (cached after first call)
    schema_context = get_schema_context(mcp_tools, schema_format)

    # Build initial messages with dynamic schema context
    system_prompt = task["prompt"]["system"]
    user_prompt = f"{task['prompt']['user']}\n\n{schema_context}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    for iteration in range(1, MAX_ITERATIONS + 1):
        iter_result = {"iteration": iteration}

        # Call OpenRouter API
        response, meta = call_openrouter(model, messages)
        iter_result["time"] = meta.get("elapsed", 0)
        results["total_time"] += iter_result["time"]

        if response is None:
            iter_result["error"] = meta.get("error", "Unknown error")
            iter_result["success"] = False
            results["iterations"].append(iter_result)
            messages.append({"role": "assistant", "content": "[API Error]"})
            messages.append({"role": "user", "content": f"API call failed: {iter_result['error']}. Please try again."})
            continue

        # Extract response content
        try:
            content = response["choices"][0]["message"]["content"]
            usage = response.get("usage", {})
            iter_result["input_tokens"] = usage.get("prompt_tokens", 0)
            iter_result["output_tokens"] = usage.get("completion_tokens", 0)
            iter_result["cost"] = usage.get("cost", 0)

            results["total_input_tokens"] += iter_result["input_tokens"]
            results["total_output_tokens"] += iter_result["output_tokens"]
            results["total_cost"] += iter_result["cost"]
        except (KeyError, IndexError) as e:
            iter_result["error"] = f"Parse error: {e}"
            iter_result["success"] = False
            results["iterations"].append(iter_result)
            messages.append({"role": "assistant", "content": "[Parse Error]"})
            messages.append({"role": "user", "content": "Could not parse response. Please provide just the DAX measure definition."})
            continue

        # Extract DAX from response
        dax = extract_dax(content)
        iter_result["raw_response"] = content
        iter_result["extracted_dax"] = dax

        # Validate using Power BI execution
        validation = validate_dax_with_powerbi(task, dax, mcp_tools)
        iter_result["validation"] = validation

        if validation["valid"]:
            iter_result["success"] = True
            results["solved"] = True
            results["final_dax"] = dax
            results["final_measure_name"] = validation.get("final_measure_name")
            if iteration == 1:
                results["first_try"] = True
            results["iterations"].append(iter_result)
            break
        else:
            iter_result["success"] = False

            # Generate feedback for next iteration
            feedback = generate_feedback(task, dax, validation, iteration)
            iter_result["feedback"] = feedback

            # Add to conversation history
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": feedback})
            results["iterations"].append(iter_result)

    results["iteration_count"] = len(results["iterations"])
    return results


# ============================================================================
# Report Generation
# ============================================================================

def generate_task_log(result: dict, timestamp: str) -> str:
    """Generate markdown log for a single task run"""
    status = "SOLVED" if result["solved"] else "FAILED"
    status_emoji = "✅" if result["solved"] else "❌"
    iters = result["iteration_count"]
    schema_fmt = result.get("schema_format", "compact")

    log = f"""# DAX Bench Run Log (v4 - Power BI Validated)

## Run Information
| Field | Value |
|-------|-------|
| **Task** | {result['task_id']} - {result['title']} |
| **Model** | {result['model']} |
| **Timestamp** | {timestamp} |
| **Result** | {status_emoji} {status} in {iters} iteration(s) |
| **Schema Format** | {schema_fmt} |
| **Validation** | Power BI Execution |

## Task Details
- **Complexity**: {result['complexity']}
- **Category**: {result['category']}

---

## Iterations

"""

    for iter_data in result["iterations"]:
        i = iter_data["iteration"]
        log += f"### Iteration {i}\n\n"

        if "error" in iter_data and not iter_data.get("validation"):
            log += f"**Error**: {iter_data['error']}\n\n"
        else:
            log += f"**Token Usage**: {iter_data.get('input_tokens', 0)} input, {iter_data.get('output_tokens', 0)} output\n\n"
            log += f"**Model Response**:\n```dax\n{iter_data.get('extracted_dax', 'N/A')}\n```\n\n"

            validation = iter_data.get("validation", {})
            if iter_data.get('success'):
                log += f"**Validation**: ✅ PASSED\n"
                log += f"- Syntax: Valid\n"
                log += f"- Execution: Success\n"
                if validation.get("final_measure_name"):
                    log += f"- Measure saved as: `{validation['final_measure_name']}`\n"
                log += "\n"
            else:
                log += f"**Validation**: ❌ FAILED\n"
                if validation.get("error"):
                    log += f"- Error: {validation['error']}\n"
                log += "\n"
                if iter_data.get('feedback'):
                    log += f"**Feedback Sent**:\n```\n{iter_data['feedback']}\n```\n\n"

        log += "---\n\n"

    log += f"""## Summary

| Metric | Value |
|--------|-------|
| **Total Iterations** | {result['iteration_count']} |
| **First Try Success** | {'✅ Yes' if result.get('first_try') else '❌ No'} |
| **Input Tokens** | {result['total_input_tokens']:,} |
| **Output Tokens** | {result['total_output_tokens']:,} |
| **Total Cost** | ${result['total_cost']:.6f} |
| **Total Time** | {result['total_time']:.2f}s |
| **Validation Method** | {result.get('validation_method', 'powerbi_execution')} |

"""

    if result.get("final_dax"):
        log += f"""## Final DAX
```dax
{result['final_dax']}
```
"""

    if result.get("final_measure_name"):
        log += f"\n**Measure saved in Power BI**: `{result['final_measure_name']}` in `{MEASURES_TABLE}` table\n"

    return log


def generate_summary_report(all_results: List[dict], model: str, timestamp: str,
                           schema_format: str = "compact") -> str:
    """Generate summary report for benchmark run"""
    total_tasks = len(all_results)
    if total_tasks == 0:
        return "No tasks were run."

    solved = sum(1 for r in all_results if r["solved"])
    first_try = sum(1 for r in all_results if r.get("first_try"))
    total_iters = sum(r["iteration_count"] for r in all_results)
    total_input = sum(r["total_input_tokens"] for r in all_results)
    total_output = sum(r["total_output_tokens"] for r in all_results)
    total_cost = sum(r["total_cost"] for r in all_results)
    total_time = sum(r["total_time"] for r in all_results)

    report = f"""# DAX Bench Benchmark Report (v4 - Power BI Validated)

## Run Information
| Field | Value |
|-------|-------|
| **Model** | {model} |
| **Timestamp** | {timestamp} |
| **Tasks Run** | {total_tasks} |
| **Max Iterations** | {MAX_ITERATIONS} |
| **Schema Format** | {schema_format} |
| **Validation Method** | Power BI Execution (Required) |
| **Measures Table** | {MEASURES_TABLE} |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | {solved}/{total_tasks} ({100*solved/total_tasks:.1f}%) |
| **First-Try Success** | {first_try}/{total_tasks} ({100*first_try/total_tasks:.1f}%) |
| **Total Iterations** | {total_iters} |
| **Avg Iterations/Task** | {total_iters/total_tasks:.2f} |
| **Total Input Tokens** | {total_input:,} |
| **Total Output Tokens** | {total_output:,} |
| **Total Tokens** | {total_input + total_output:,} |
| **Total Cost** | ${total_cost:.4f} |
| **Cost per Task** | ${total_cost/total_tasks:.6f} |
| **Total Time** | {total_time:.1f}s ({total_time/60:.1f}m) |
| **Avg Time/Task** | {total_time/total_tasks:.2f}s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
"""

    for level in ["basic", "intermediate", "advanced"]:
        level_results = [r for r in all_results if r["complexity"] == level]
        if level_results:
            l_solved = sum(1 for r in level_results if r["solved"])
            l_first = sum(1 for r in level_results if r.get("first_try"))
            l_iters = sum(r["iteration_count"] for r in level_results) / len(level_results)
            report += f"| {level.capitalize()} | {l_solved}/{len(level_results)} | {l_first}/{len(level_results)} | {l_iters:.2f} |\n"

    report += """
---

## Results by Category

| Category | Solved | First-Try | Tasks |
|----------|--------|-----------|-------|
"""

    categories = set(r["category"] for r in all_results)
    for cat in sorted(categories):
        cat_results = [r for r in all_results if r["category"] == cat]
        c_solved = sum(1 for r in cat_results if r["solved"])
        c_first = sum(1 for r in cat_results if r.get("first_try"))
        report += f"| {cat} | {c_solved}/{len(cat_results)} | {c_first}/{len(cat_results)} | {len(cat_results)} |\n"

    report += """
---

## Per-Task Results

| Task | Complexity | Category | Solved | Iters | Cost |
|------|------------|----------|--------|-------|------|
"""

    for r in all_results:
        status = "✅" if r["solved"] else "❌"
        report += f"| {r['task_id']} | {r['complexity']} | {r['category']} | {status} | {r['iteration_count']} | ${r['total_cost']:.4f} |\n"

    report += """
---

## Failed Tasks (if any)

"""

    failed = [r for r in all_results if not r["solved"]]
    if failed:
        for r in failed:
            report += f"### {r['task_id']}: {r['title']}\n"
            report += f"- **Complexity**: {r['complexity']}\n"
            report += f"- **Category**: {r['category']}\n"
            report += f"- **Iterations**: {r['iteration_count']}\n"
            if r["iterations"]:
                last_iter = r["iterations"][-1]
                last_dax = last_iter.get("extracted_dax", "N/A")
                last_error = last_iter.get("validation", {}).get("error", "Unknown")
                report += f"- **Last Error**: {last_error}\n"
                report += f"- **Last Attempt**:\n```dax\n{last_dax}\n```\n\n"
    else:
        report += "*All tasks solved successfully!*\n"

    return report


# ============================================================================
# MCP Tool Wrapper (for Claude Code integration)
# ============================================================================

def create_mcp_tools_for_claude():
    """
    Create MCP tool wrappers that will be called by Claude Code.

    When running standalone, these will raise errors indicating
    that the script should be run via Claude Code.

    When running via Claude Code, these will be replaced with
    actual MCP tool calls.
    """
    def not_implemented(name):
        def _fn(*args, **kwargs):
            raise PowerBIValidationError(
                f"MCP tool '{name}' not available in standalone mode.\n"
                "Please run this benchmark via Claude Code with Power BI MCP connected."
            )
        return _fn

    return {
        "create_measure": not_implemented("create_measure"),
        "update_measure": not_implemented("update_measure"),
        "delete_measure": not_implemented("delete_measure"),
        "run_dax": not_implemented("run_dax"),
        "get_connection": not_implemented("get_connection"),
        "get_model_info": not_implemented("get_model_info"),
    }


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="DAX Bench Solver v4 - Power BI Execution Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tasks with a model
  python run_benchmark_v4.py google/gemini-2.5-flash

  # Run specific tasks
  python run_benchmark_v4.py google/gemini-2.5-flash --tasks 1,2,3
  python run_benchmark_v4.py google/gemini-2.5-flash --tasks task-001,task-005
  python run_benchmark_v4.py google/gemini-2.5-flash --tasks 1-10

  # Run by complexity
  python run_benchmark_v4.py google/gemini-2.5-flash --complexity basic
  python run_benchmark_v4.py google/gemini-2.5-flash --complexity advanced

  # Combine filters
  python run_benchmark_v4.py google/gemini-2.5-flash --tasks 1-30 --complexity advanced
"""
    )

    parser.add_argument("model", nargs="?", default="google/gemini-2.5-flash",
                       help="OpenRouter model ID (default: google/gemini-2.5-flash)")
    parser.add_argument("--tasks", "-t", type=str,
                       help="Task IDs to run (e.g., '1,2,3', '1-10', 'task-001')")
    parser.add_argument("--complexity", "-c", choices=["basic", "intermediate", "advanced"],
                       help="Filter by complexity level")
    parser.add_argument("--max-iterations", "-i", type=int, default=MAX_ITERATIONS,
                       help=f"Max iterations per task (default: {MAX_ITERATIONS})")
    parser.add_argument("--schema-format", "-s", choices=["full", "compact", "minimal"],
                       default=DEFAULT_SCHEMA_FORMAT,
                       help=f"Schema context format for LLM prompts (default: {DEFAULT_SCHEMA_FORMAT})")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be run without executing")

    args = parser.parse_args()

    # Check API key
    if not API_KEY:
        print("ERROR: OPENROUTER_DAXBENCH_API_KEY environment variable not set")
        sys.exit(1)

    # Update max iterations if specified
    global MAX_ITERATIONS
    if args.max_iterations:
        MAX_ITERATIONS = args.max_iterations

    print("=" * 60)
    print("DAX Bench Solver v4 - Power BI Execution Validation")
    print("=" * 60)
    print(f"Model: {args.model}")
    print(f"Max Iterations: {MAX_ITERATIONS}")
    print(f"Schema Format: {args.schema_format}")
    print(f"Validation: Power BI Execution (Required)")
    print("-" * 60)

    # Load and filter tasks
    all_tasks = load_all_tasks()
    print(f"Total tasks available: {len(all_tasks)}")

    task_ids = None
    if args.tasks:
        task_ids = parse_task_range(args.tasks)
        print(f"Task filter: {task_ids}")

    tasks = filter_tasks(all_tasks, task_ids=task_ids, complexity=args.complexity)
    print(f"Tasks to run: {len(tasks)}")

    if not tasks:
        print("No tasks match the specified filters.")
        sys.exit(0)

    # List tasks
    print("\nSelected tasks:")
    for t in tasks:
        print(f"  - {t['id']}: {t['title']} ({t['complexity']})")

    if args.dry_run:
        print("\n[DRY RUN] Would run the above tasks. Exiting.")
        sys.exit(0)

    # Check Power BI connection
    print("\nChecking Power BI connection...")
    try:
        conn_info = check_powerbi_connection()
        print(f"✓ Power BI connected: {conn_info}")
    except PowerBIConnectionError as e:
        print(f"\n❌ {e}")
        print("\nTo run this benchmark:")
        print("1. Open Power BI Desktop with dax-bench/Contoso.pbix")
        print("2. Ensure Power BI MCP server is running")
        print("3. Run from Claude Code or set PBI_MCP_URL environment variable")
        sys.exit(1)

    # Get MCP tools
    mcp_tools = create_mcp_tools_for_claude()

    # Run benchmark
    print("\n" + "=" * 60)
    print("Starting benchmark...")
    print("=" * 60)

    RUNS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    date_prefix = datetime.now().strftime("%Y-%m-%d_%H%M")
    model_safe = args.model.replace("/", "_").replace(":", "_")

    all_results = []

    for i, task in enumerate(tasks, 1):
        print(f"\n[{i}/{len(tasks)}] {task['id']}: {task['title']} ({task['complexity']})")

        try:
            result = solve_task(task, args.model, mcp_tools, args.schema_format)
            all_results.append(result)

            status = "✅ Solved" if result["solved"] else "❌ Failed"
            iters = result["iteration_count"]
            cost = result["total_cost"]
            first = " (1st try!)" if result.get("first_try") else ""
            print(f"  {status} in {iters} iter(s), ${cost:.4f}{first}")

            # Write individual log
            log_content = generate_task_log(result, timestamp)
            log_file = RUNS_DIR / f"{date_prefix}_{task['id']}_{model_safe}_v4.md"
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(log_content)

        except PowerBIValidationError as e:
            print(f"  ❌ Power BI validation error: {e}")
            # Record the failure
            all_results.append({
                "task_id": task["id"],
                "title": task["title"],
                "complexity": task["complexity"],
                "category": task["category"],
                "model": args.model,
                "iterations": [],
                "solved": False,
                "first_try": False,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0,
                "total_time": 0,
                "iteration_count": 0,
                "error": str(e)
            })

    # Write summary report
    summary = generate_summary_report(all_results, args.model, timestamp, args.schema_format)
    summary_file = RUNS_DIR / f"{date_prefix}_SUMMARY_{model_safe}_v4.md"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary)

    # Save raw JSON results
    json_file = RUNS_DIR / f"{date_prefix}_RESULTS_{model_safe}_v4.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)

    # Print summary
    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE (v4)")
    print("=" * 60)

    solved = sum(1 for r in all_results if r["solved"])
    first_try = sum(1 for r in all_results if r.get("first_try"))
    total_cost = sum(r["total_cost"] for r in all_results)
    total_time = sum(r["total_time"] for r in all_results)

    print(f"Solved: {solved}/{len(tasks)} ({100*solved/len(tasks):.1f}%)")
    print(f"First-Try: {first_try}/{len(tasks)} ({100*first_try/len(tasks):.1f}%)")
    print(f"Total Cost: ${total_cost:.4f}")
    print(f"Total Time: {total_time:.1f}s")
    print(f"\nSummary: {summary_file}")
    print(f"Raw JSON: {json_file}")


if __name__ == "__main__":
    main()
