#!/usr/bin/env python3
"""
Validate all DAX expressions against Power BI.

This script is designed to output validation commands that Claude Code
can execute using MCP tools.

Usage:
    python validate_all.py [--start 0] [--count 120]
"""

import json
import re
from pathlib import Path


def clean_expression(expr: str) -> str:
    """Clean up expression artifacts."""
    expr = re.sub(r'<budget:[^>]*>[^<]*</budget:[^>]*>', '', expr)
    expr = re.sub(r'<[^>]*>', '', expr)
    expr = re.sub(r'Human:.*', '', expr, flags=re.DOTALL)
    expr = re.sub(r'<measure_dependency>.*?</measure_dependency>', '', expr, flags=re.DOTALL)
    return expr.strip()


def is_table_expression(expr: str) -> bool:
    """Check if expression returns a table (invalid for measure)."""
    table_funcs = ['SUMMARIZE', 'SELECTCOLUMNS', 'UNION', 'CROSSJOIN', 'FILTER', 'TOPN']
    expr_upper = expr.strip().upper()
    for func in table_funcs:
        if expr_upper.startswith(func):
            return True
    return False


def has_undefined_references(expr: str) -> bool:
    """Check for references to undefined tables."""
    return 'Budget[' in expr or 'Budget Amount' in expr


def main():
    runs_dir = Path(__file__).parent / "runs"

    with open(runs_dir / "combined_api_responses_with_schema.json") as f:
        results = json.load(f)

    validated = []

    for r in results:
        task_id = r.get("task_id", "")
        model = r.get("model_short", "")
        dax = r.get("dax", "")

        if not dax:
            validated.append({
                **r,
                "valid": False,
                "error": "No DAX expression",
                "validation_method": "static"
            })
            continue

        # Parse measure name and expression
        match = re.match(r'\[?([^\]=]+)\]?\s*=\s*(.+)', dax, re.DOTALL)
        if not match:
            validated.append({
                **r,
                "valid": False,
                "error": "Could not parse measure",
                "validation_method": "static"
            })
            continue

        name = match.group(1).strip()
        expr = clean_expression(match.group(2).strip())

        # Static analysis
        error = None

        if name.startswith("VAR "):
            error = "Measure name incorrectly parsed (includes VAR)"
        elif is_table_expression(expr):
            error = "Expression returns a table, not a scalar value"
        elif has_undefined_references(expr):
            error = "References undefined 'Budget' table"
        elif "[Total Net Price" in expr or "[Net Price]" in expr and "Sales[Net Price]" not in expr:
            error = "References undefined measure or missing table qualifier"

        validated.append({
            **r,
            "parsed_name": name,
            "parsed_expression": expr,
            "valid": error is None,
            "error": error,
            "validation_method": "static" if error else "pending_powerbi"
        })

    # Statistics
    total = len(validated)
    valid_static = sum(1 for v in validated if v["valid"])
    invalid_static = sum(1 for v in validated if not v["valid"])

    print(f"Total expressions: {total}")
    print(f"Passed static analysis: {valid_static}")
    print(f"Failed static analysis: {invalid_static}")
    print()

    # By model
    by_model = {}
    for v in validated:
        model = v.get("model_short", "unknown")
        if model not in by_model:
            by_model[model] = {"total": 0, "valid": 0}
        by_model[model]["total"] += 1
        if v["valid"]:
            by_model[model]["valid"] += 1

    print("By model (static analysis):")
    for model, stats in sorted(by_model.items()):
        pct = 100 * stats["valid"] / stats["total"]
        print(f"  {model}: {stats['valid']}/{stats['total']} ({pct:.1f}%)")

    # Save validated results
    output_file = runs_dir / "validated_results_static.json"
    with open(output_file, "w") as f:
        json.dump(validated, f, indent=2)

    print(f"\nSaved to {output_file}")

    # Print expressions that need Power BI validation
    pending = [v for v in validated if v.get("validation_method") == "pending_powerbi"]
    print(f"\n{len(pending)} expressions need Power BI validation")

    return validated


if __name__ == "__main__":
    main()
