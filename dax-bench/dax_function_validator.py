"""
DAX Function Validator
Validates DAX expressions against official DAX.guide function list
"""

import json
import re
from pathlib import Path
from typing import NamedTuple


class ValidationResult(NamedTuple):
    expression: str
    is_valid: bool
    invalid_functions: list[str]
    deprecated_functions: list[str]
    warnings: list[str]


def load_function_reference() -> dict:
    """Load the DAX function reference file."""
    ref_path = Path(__file__).parent / "dax_functions_reference.json"
    with open(ref_path, "r") as f:
        return json.load(f)


def extract_functions_from_expression(expression: str) -> set[str]:
    """
    Extract all function names from a DAX expression.
    Looks for patterns like FUNCTION_NAME(
    """
    # Pattern: word characters followed by opening paren (not preceded by [ which indicates column)
    pattern = r'(?<!\[)\b([A-Z][A-Z0-9_.]*)\s*\('
    matches = re.findall(pattern, expression.upper())
    return set(matches)


def validate_dax_expression(expression: str, reference: dict = None) -> ValidationResult:
    """
    Validate a DAX expression against the official function list.

    Returns ValidationResult with:
    - is_valid: True if all functions are valid DAX
    - invalid_functions: List of functions not in DAX
    - deprecated_functions: List of functions that work but are not recommended
    - warnings: Additional notes
    """
    if reference is None:
        reference = load_function_reference()

    valid_functions = set(f.upper() for f in reference["valid_functions"])
    deprecated = reference.get("deprecated_functions", {})

    # Extract functions from expression
    used_functions = extract_functions_from_expression(expression)

    invalid_functions = []
    deprecated_functions = []
    warnings = []

    for func in used_functions:
        func_upper = func.upper()

        if func_upper not in valid_functions:
            invalid_functions.append(func)

            # Check if it's a known Excel/SQL function
            excel_funcs = [f.upper() for f in reference.get("common_excel_functions_not_in_dax", [])]
            sql_funcs = [f.upper() for f in reference.get("common_sql_functions_not_in_dax", [])]

            if func_upper in excel_funcs:
                warnings.append(f"{func} is an Excel function, not DAX")
            elif func_upper in sql_funcs:
                warnings.append(f"{func} is a SQL function, not DAX")
            else:
                warnings.append(f"{func} is not a valid DAX function")

        elif func_upper in [d.upper() for d in deprecated.keys()]:
            deprecated_functions.append(func)
            dep_info = deprecated.get(func_upper, deprecated.get(func, {}))
            if dep_info:
                warnings.append(f"{func}: {dep_info.get('reason', 'Deprecated')}")

    is_valid = len(invalid_functions) == 0

    return ValidationResult(
        expression=expression,
        is_valid=is_valid,
        invalid_functions=invalid_functions,
        deprecated_functions=deprecated_functions,
        warnings=warnings
    )


def validate_expressions_from_file(filepath: str) -> dict:
    """
    Validate all expressions from a validation queue JSON file.
    """
    reference = load_function_reference()

    with open(filepath, "r") as f:
        expressions = json.load(f)

    results = {
        "total": len(expressions),
        "valid": 0,
        "invalid": 0,
        "has_deprecated": 0,
        "details": []
    }

    for item in expressions:
        expr = item.get("expression", "")
        task_id = item.get("task_id", "unknown")
        model = item.get("model", "unknown")

        result = validate_dax_expression(expr, reference)

        if result.is_valid:
            results["valid"] += 1
        else:
            results["invalid"] += 1

        if result.deprecated_functions:
            results["has_deprecated"] += 1

        if not result.is_valid or result.deprecated_functions:
            results["details"].append({
                "task_id": task_id,
                "model": model,
                "is_valid": result.is_valid,
                "invalid_functions": result.invalid_functions,
                "deprecated_functions": result.deprecated_functions,
                "warnings": result.warnings
            })

    return results


def get_dax_replacement_suggestions(invalid_function: str) -> str:
    """
    Provide replacement suggestions for common invalid functions.
    """
    replacements = {
        "SUMIF": "Use CALCULATE(SUM(column), filter_condition)",
        "SUMIFS": "Use CALCULATE(SUM(column), filter1, filter2, ...)",
        "COUNTIF": "Use CALCULATE(COUNTROWS(table), filter_condition)",
        "COUNTIFS": "Use CALCULATE(COUNTROWS(table), filter1, filter2, ...)",
        "AVERAGEIF": "Use CALCULATE(AVERAGE(column), filter_condition)",
        "SUMPRODUCT": "Use SUMX(table, expression1 * expression2)",
        "VLOOKUP": "Use LOOKUPVALUE(result_column, search_column, search_value)",
        "DENSE_RANK": "Use RANKX(table, expression, , DESC, DENSE)",
        "ROW_NUMBER": "Use RANKX(table, expression, , , SKIP)",
        "SAMEPERIODLASTDAY": "Use DATEADD('Date'[Date], -1, DAY)",
        "EARLIER": "Use VAR to capture the value before the nested context",
        "EARLIEST": "Use VAR to capture the value before the nested context"
    }

    return replacements.get(invalid_function.upper(), "Check DAX.guide for alternatives")


# Quick test functions
def test_expression(expr: str) -> None:
    """Quick test a single expression."""
    result = validate_dax_expression(expr)
    print(f"\nExpression: {expr[:60]}...")
    print(f"Valid: {result.is_valid}")
    if result.invalid_functions:
        print(f"Invalid functions: {result.invalid_functions}")
    if result.deprecated_functions:
        print(f"Deprecated: {result.deprecated_functions}")
    if result.warnings:
        for w in result.warnings:
            print(f"  Warning: {w}")


if __name__ == "__main__":
    # Test some expressions
    test_cases = [
        "SUM(Sales[Amount])",  # Valid
        "SUMIF(Sales[Category], \"Audio\", Sales[Amount])",  # Invalid - Excel
        "CALCULATE(SUM(Sales[Amount]), SAMEPERIODLASTYEAR('Date'[Date]))",  # Valid
        "DENSE_RANK(ORDER(SUM(Sales[Amount]), DESC))",  # Invalid - SQL
        "RANKX(ALL(Product), SUM(Sales[Amount]), , DESC, DENSE)",  # Valid
        "COUNTROWS(FILTER(T, T[Col] <= EARLIER(T[Col])))",  # Valid but deprecated
        "SAMEPERIODLASTDAY('Date'[Date])"  # Invalid - invented
    ]

    print("=" * 60)
    print("DAX Function Validator Test")
    print("=" * 60)

    for expr in test_cases:
        test_expression(expr)

    print("\n" + "=" * 60)
    print("Validating queue file...")
    print("=" * 60)

    queue_path = Path(__file__).parent / "runs" / "validation_queue.json"
    if queue_path.exists():
        results = validate_expressions_from_file(str(queue_path))
        print(f"\nTotal expressions: {results['total']}")
        print(f"Valid: {results['valid']}")
        print(f"Invalid: {results['invalid']}")
        print(f"Has deprecated: {results['has_deprecated']}")

        if results['details']:
            print(f"\nProblematic expressions:")
            for detail in results['details'][:10]:  # Show first 10
                print(f"  {detail['model']}/{detail['task_id']}: {detail['warnings']}")
