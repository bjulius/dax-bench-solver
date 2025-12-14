# Power BI Validation Skill

Wrapper for Power BI MCP tools needed to validate DAX expressions against a live Power BI Desktop model.

## Purpose

Provide a self-contained interface for:
- Creating and managing measures in Power BI
- Executing DAX queries for validation
- Fetching model schema for LLM context
- Checking Power BI connection status

## When to Invoke This Skill

Use this skill when:
- Validating generated DAX expressions
- Running DAX benchmarks that require execution validation
- Checking if DAX syntax is correct
- Getting actual query results from Power BI model

## Prerequisites

- **Power BI Desktop**: Open with the target .pbix file
- **Power BI MCP Server**: Connected and running (port configured)
- **Claude Code**: Running with MCP integration

## Core Operations

### 1. Check Connection

Verify Power BI MCP is connected and accessible:

```python
# Returns connection info or raises error
result = check_powerbi_connection()
# {"connected": True, "model_id": "port:database", "model_name": "..."}
```

### 2. Get Model Schema

Fetch complete model schema for LLM prompts:

```python
schema = get_model_info(info_type="schema")
# Returns dict with tables, columns, relationships, measures
```

### 3. Create Measure

Create a DAX measure in the model:

```python
result = create_measure(
    table="_Measures",
    name="MyMeasure",
    expression="SUM(Sales[Amount])"
)
# {"success": True} or {"success": False, "error": "..."}
```

### 4. Execute DAX Query

Run a DAX query and return results:

```python
result = run_dax("EVALUATE ROW(\"Result\", [MyMeasure])")
# {"data": [{"Result": 12345.67}]} or {"error": "..."}
```

### 5. Update Measure

Rename or modify an existing measure:

```python
result = update_measure(
    table="_Measures",
    name="OldName",
    new_name="NewName"
)
```

### 6. Delete Measure

Remove a measure from the model:

```python
result = delete_measure(table="_Measures", name="MyMeasure")
```

## MCP Tool Mapping

| Skill Operation | MCP Tool | Parameters |
|-----------------|----------|------------|
| `check_connection` | `manage_model_connection` | `operation: "get_current"` |
| `get_model_info` | `get_model_info` | `info_type: "schema"` |
| `create_measure` | `manage_measure` | `operation: "create"` |
| `update_measure` | `manage_measure` | `operation: "update"` |
| `delete_measure` | `manage_measure` | `operation: "delete"` |
| `run_dax` | `run_dax` | `query: "..."` |

## Python Wrapper

Save to `dax-bench/powerbi_validation.py`:

```python
"""
Power BI Validation - MCP Tool Wrapper
Provides validation functions for DAX expressions.
"""

from typing import Any, Optional, Dict, Tuple


class PowerBIValidator:
    """
    Wrapper for Power BI MCP tools.

    When running via Claude Code, the mcp_tools dict is populated
    with actual MCP function references.
    """

    def __init__(self, mcp_tools: Dict[str, callable]):
        self.tools = mcp_tools
        self._connected = False

    def check_connection(self) -> Dict[str, Any]:
        """Check if Power BI is connected."""
        if "get_connection" in self.tools:
            result = self.tools["get_connection"](operation="get_current")
            self._connected = result.get("connected", False)
            return result
        raise RuntimeError("MCP tools not available")

    def get_schema(self) -> Dict[str, Any]:
        """Get model schema for LLM context."""
        return self.tools["get_model_info"](info_type="schema")

    def create_measure(self, table: str, name: str,
                       expression: str) -> Dict[str, Any]:
        """Create a measure in the model."""
        try:
            result = self.tools["create_measure"](
                operation="create",
                table=table,
                name=name,
                expression=expression
            )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_dax(self, query: str) -> Dict[str, Any]:
        """Execute a DAX query."""
        try:
            result = self.tools["run_dax"](query=query)
            return {"data": result, "error": None}
        except Exception as e:
            return {"data": None, "error": str(e)}

    def validate_measure(self, table: str, name: str,
                         expression: str) -> Dict[str, Any]:
        """
        Validate a DAX expression by creating and executing it.
        Returns validation result with syntax/execution status.
        """
        result = {
            "valid": False,
            "syntax_valid": False,
            "executes": False,
            "error": None,
            "value": None
        }

        # Step 1: Create measure
        create = self.create_measure(table, name, expression)
        if not create["success"]:
            result["error"] = f"Syntax error: {create['error']}"
            return result

        result["syntax_valid"] = True

        # Step 2: Execute measure
        query = f'EVALUATE ROW("Result", [{name}])'
        exec_result = self.run_dax(query)

        if exec_result["error"]:
            result["error"] = f"Execution error: {exec_result['error']}"
            # Clean up invalid measure
            self.delete_measure(table, name)
            return result

        result["executes"] = True
        result["valid"] = True
        result["value"] = exec_result["data"]

        return result

    def update_measure(self, table: str, name: str,
                       new_name: Optional[str] = None,
                       expression: Optional[str] = None) -> Dict[str, Any]:
        """Update a measure name or expression."""
        kwargs = {"operation": "update", "table": table, "name": name}
        if new_name:
            kwargs["newName"] = new_name
        if expression:
            kwargs["expression"] = expression
        return self.tools["update_measure"](**kwargs)

    def delete_measure(self, table: str, name: str) -> bool:
        """Delete a measure."""
        try:
            self.tools["delete_measure"](
                operation="delete",
                table=table,
                name=name
            )
            return True
        except Exception:
            return False
```

## Integration with Other Skills

### Called by: dax-bench-solver

```python
from powerbi_validation import PowerBIValidator

# Initialize with MCP tools
validator = PowerBIValidator(mcp_tools)

# Validate a generated DAX expression
result = validator.validate_measure(
    table="_Measures",
    name="Test_Revenue",
    expression="SUM(Sales[Net Price])"
)

if result["valid"]:
    print(f"Valid! Result: {result['value']}")
else:
    print(f"Invalid: {result['error']}")
```

### Uses: schema-extractor

```python
from schema_extractor import extract_schema

# Get schema via validator
schema = validator.get_schema()

# Format for LLM prompt
context = extract_schema(schema, format="compact")
```

## Validation Flow

```
1. Parse DAX expression → extract measure name and body
2. Create test measure in _Measures table
3. If creation fails → syntax error
4. Execute: EVALUATE ROW("Result", [MeasureName])
5. If execution fails → runtime error
6. If success → measure is valid, optionally rename to final name
```

## Error Categories

| Error Type | Cause | Example |
|------------|-------|---------|
| **Syntax Error** | Invalid DAX syntax | Missing parenthesis, unknown function |
| **Reference Error** | Invalid table/column reference | `Sales[NonExistent]` |
| **Type Error** | Type mismatch | `SUM("text")` |
| **Context Error** | Invalid filter context | `EARLIER` without row context |

## Example Output

### Successful Validation
```json
{
  "valid": true,
  "syntax_valid": true,
  "executes": true,
  "error": null,
  "value": [{"Result": 721780827.52}]
}
```

### Failed Validation
```json
{
  "valid": false,
  "syntax_valid": true,
  "executes": false,
  "error": "Execution error: Column 'NonExistent' not found in table 'Sales'"
}
```
