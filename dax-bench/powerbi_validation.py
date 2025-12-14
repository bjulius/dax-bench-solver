"""
Power BI Validation - MCP Tool Wrapper
Provides validation functions for DAX expressions.

Usage:
    # When running via Claude Code with MCP tools available:
    from powerbi_validation import PowerBIValidator

    validator = PowerBIValidator(mcp_tools)
    result = validator.validate_measure("_Measures", "Test", "SUM(Sales[Amount])")
"""

from typing import Any, Optional, Dict, List, Callable


class PowerBIValidationError(Exception):
    """Raised when validation fails."""
    pass


class PowerBIConnectionError(Exception):
    """Raised when Power BI is not connected."""
    pass


class PowerBIValidator:
    """
    Wrapper for Power BI MCP tools.

    When running via Claude Code, the mcp_tools dict is populated
    with actual MCP function references:
    - create_measure: manage_measure(operation="create", ...)
    - update_measure: manage_measure(operation="update", ...)
    - delete_measure: manage_measure(operation="delete", ...)
    - run_dax: run_dax(query="...")
    - get_model_info: get_model_info(info_type="schema")
    - get_connection: manage_model_connection(operation="get_current")
    """

    def __init__(self, mcp_tools: Dict[str, Callable]):
        """
        Initialize with MCP tool references.

        Args:
            mcp_tools: Dict mapping tool names to callable functions
        """
        self.tools = mcp_tools
        self._connected = False
        self._model_info: Optional[Dict] = None

    def check_connection(self) -> Dict[str, Any]:
        """
        Check if Power BI is connected and accessible.

        Returns:
            Dict with connection info: {"connected": bool, "model_id": str, ...}

        Raises:
            PowerBIConnectionError: If not connected
        """
        if "get_connection" not in self.tools:
            raise PowerBIConnectionError("MCP tools not available - run via Claude Code")

        try:
            result = self.tools["get_connection"](operation="get_current")
            self._connected = result.get("connected", False)
            if not self._connected:
                raise PowerBIConnectionError("Power BI not connected")
            return result
        except Exception as e:
            raise PowerBIConnectionError(f"Connection check failed: {e}")

    def get_schema(self) -> Dict[str, Any]:
        """
        Get complete model schema for LLM context.

        Returns:
            Dict with model, tables, columns, relationships, measures
        """
        if "get_model_info" not in self.tools:
            raise PowerBIValidationError("get_model_info tool not available")

        if self._model_info is None:
            self._model_info = self.tools["get_model_info"](info_type="schema")

        return self._model_info

    def create_measure(self, table: str, name: str,
                       expression: str,
                       description: Optional[str] = None,
                       format_string: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a DAX measure in the model.

        Args:
            table: Target table name (usually "_Measures")
            name: Measure name
            expression: DAX expression (without measure name prefix)
            description: Optional description
            format_string: Optional format string (e.g., "#,##0.00")

        Returns:
            {"success": True} or {"success": False, "error": "..."}
        """
        if "create_measure" not in self.tools:
            raise PowerBIValidationError("create_measure tool not available")

        try:
            kwargs = {
                "operation": "create",
                "table": table,
                "name": name,
                "expression": expression
            }
            if description:
                kwargs["description"] = description
            if format_string:
                kwargs["formatString"] = format_string

            result = self.tools["create_measure"](**kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_dax(self, query: str) -> Dict[str, Any]:
        """
        Execute a DAX query and return results.

        Args:
            query: DAX query (e.g., "EVALUATE ROW(...)")

        Returns:
            {"data": [...], "error": None} or {"data": None, "error": "..."}
        """
        if "run_dax" not in self.tools:
            raise PowerBIValidationError("run_dax tool not available")

        try:
            result = self.tools["run_dax"](query=query)
            return {"data": result, "error": None}
        except Exception as e:
            return {"data": None, "error": str(e)}

    def validate_measure(self, table: str, name: str,
                         expression: str,
                         cleanup_on_failure: bool = True) -> Dict[str, Any]:
        """
        Validate a DAX expression by creating and executing it.

        This is the main validation method:
        1. Creates the measure (syntax check)
        2. Executes the measure (runtime check)
        3. Returns validation result

        Args:
            table: Target table for measure
            name: Measure name
            expression: DAX expression body
            cleanup_on_failure: Delete measure if validation fails

        Returns:
            Dict with validation result:
            - valid: bool - Overall validity
            - syntax_valid: bool - Syntax check passed
            - executes: bool - Execution succeeded
            - error: str or None - Error message if failed
            - value: Any - Result value if successful
        """
        result = {
            "valid": False,
            "syntax_valid": False,
            "executes": False,
            "error": None,
            "value": None,
            "measure_name": name
        }

        # Step 1: Create measure (syntax validation)
        create_result = self.create_measure(table, name, expression)
        if not create_result["success"]:
            result["error"] = f"Syntax error: {create_result['error']}"
            return result

        result["syntax_valid"] = True

        # Step 2: Execute measure (runtime validation)
        query = f'EVALUATE ROW("Result", [{name}])'
        exec_result = self.run_dax(query)

        if exec_result["error"]:
            result["error"] = f"Execution error: {exec_result['error']}"
            if cleanup_on_failure:
                self.delete_measure(table, name)
            return result

        result["executes"] = True
        result["valid"] = True
        result["value"] = exec_result["data"]

        return result

    def update_measure(self, table: str, name: str,
                       new_name: Optional[str] = None,
                       expression: Optional[str] = None,
                       description: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an existing measure.

        Args:
            table: Table containing the measure
            name: Current measure name
            new_name: New name (if renaming)
            expression: New expression (if updating)
            description: New description (if updating)

        Returns:
            Update result from MCP
        """
        if "update_measure" not in self.tools:
            raise PowerBIValidationError("update_measure tool not available")

        kwargs = {"operation": "update", "table": table, "name": name}
        if new_name:
            kwargs["newName"] = new_name
        if expression:
            kwargs["expression"] = expression
        if description:
            kwargs["description"] = description

        return self.tools["update_measure"](**kwargs)

    def delete_measure(self, table: str, name: str) -> bool:
        """
        Delete a measure from the model.

        Args:
            table: Table containing the measure
            name: Measure name

        Returns:
            True if deleted, False if failed
        """
        if "delete_measure" not in self.tools:
            return False

        try:
            self.tools["delete_measure"](
                operation="delete",
                table=table,
                name=name
            )
            return True
        except Exception:
            return False

    def list_measures(self, table: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all measures in the model.

        Args:
            table: Optional table filter

        Returns:
            List of measure definitions
        """
        if "list_objects" not in self.tools:
            raise PowerBIValidationError("list_objects tool not available")

        kwargs = {"type": "measures"}
        if table:
            kwargs["table"] = table

        return self.tools["list_objects"](**kwargs)


def create_validator_for_claude_code() -> PowerBIValidator:
    """
    Create a validator with placeholder tools for Claude Code.

    Claude Code will replace these with actual MCP function calls
    when running the benchmark.
    """
    def not_available(name: str):
        def _fn(*args, **kwargs):
            raise PowerBIValidationError(
                f"Tool '{name}' requires Claude Code with Power BI MCP"
            )
        return _fn

    placeholder_tools = {
        "create_measure": not_available("create_measure"),
        "update_measure": not_available("update_measure"),
        "delete_measure": not_available("delete_measure"),
        "run_dax": not_available("run_dax"),
        "get_model_info": not_available("get_model_info"),
        "get_connection": not_available("get_connection"),
        "list_objects": not_available("list_objects"),
    }

    return PowerBIValidator(placeholder_tools)


# CLI for testing
if __name__ == "__main__":
    import sys

    print("Power BI Validation Module")
    print("-" * 40)
    print("This module provides DAX validation via Power BI MCP.")
    print("")
    print("Usage:")
    print("  from powerbi_validation import PowerBIValidator")
    print("  validator = PowerBIValidator(mcp_tools)")
    print("  result = validator.validate_measure('_Measures', 'Test', 'SUM(...)')")
    print("")
    print("When running via Claude Code, MCP tools are automatically available.")
    print("For standalone testing, set up the MCP bridge configuration.")
