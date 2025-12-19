"""
Schema Extractor for Power BI Models
Generates LLM-friendly schema prompts from Power BI MCP data.

Usage:
    # From Python
    from schema_extractor import extract_schema, get_schema_prompt
    schema_prompt = get_schema_prompt(format="compact")

    # From CLI
    python schema_extractor.py schema.json [full|compact|minimal]
"""

import json
import sys
from typing import Literal, Optional

SchemaFormat = Literal["full", "compact", "minimal"]

# Table classification heuristics
FACT_TABLE_INDICATORS = ["Sales", "Orders", "Transactions", "Facts", "Fact"]
DATE_TABLE_INDICATORS = ["Date", "Calendar", "Time"]
MEASURE_TABLE_INDICATORS = ["_Measures", "Measures", "_Calc"]


def classify_table(table_name: str, columns: list, relationships: list) -> str:
    """Classify table as fact, dimension, date, or measures."""
    name_lower = table_name.lower()

    # Check for measure table (no real columns)
    real_columns = [c for c in columns if not c.get("isHidden") and not c["name"].startswith("RowNumber")]
    if len(real_columns) <= 1:
        return "measures"

    # Check for date table
    for indicator in DATE_TABLE_INDICATORS:
        if indicator.lower() in name_lower:
            return "date"

    # Check for fact table (has FK relationships to other tables)
    outgoing_rels = [r for r in relationships if r["fromTable"] == table_name]
    if len(outgoing_rels) >= 2:
        return "fact"

    # Check by name
    for indicator in FACT_TABLE_INDICATORS:
        if indicator.lower() in name_lower:
            return "fact"

    return "dimension"


def needs_quoting(name: str) -> bool:
    """Check if table name needs to be quoted in DAX."""
    reserved_words = ["Date", "Time", "Year", "Month", "Day", "Hour", "Minute", "Second"]
    return " " in name or name in reserved_words


def format_table_name(name: str) -> str:
    """Format table name with quotes if needed."""
    return f"'{name}'" if needs_quoting(name) else name


def format_compact(schema: dict) -> str:
    """Generate compact schema for LLM prompts (~500-800 tokens)."""
    lines = ["## Power BI Data Model", "", "### Tables", ""]

    tables = schema.get("tables", [])
    relationships = schema.get("relationships", [])

    # Classify and sort tables
    classified = []
    for table in tables:
        if table.get("isHidden"):
            continue
        table_type = classify_table(table["name"], table.get("columns", []), relationships)
        if table_type == "measures":
            continue  # Skip measure-only tables
        classified.append((table, table_type))

    # Sort: fact, dimension, date
    type_order = {"fact": 0, "dimension": 1, "date": 2}
    classified.sort(key=lambda x: type_order.get(x[1], 3))

    for table, table_type in classified:
        name = table["name"]
        display_name = format_table_name(name)

        # Get visible columns (excluding system columns)
        columns = [c for c in table.get("columns", [])
                   if not c.get("isHidden") and not c["name"].startswith("RowNumber")]

        col_names = []
        for col in columns:
            col_name = col["name"]
            if col.get("isKey"):
                col_name += " [PK]"
            col_names.append(col_name)

        lines.append(f"**{display_name}** ({table_type})")
        lines.append(f"Columns: {', '.join(col_names)}")
        lines.append("")

    # Relationships
    lines.append("### Relationships")
    for rel in relationships:
        if not rel.get("isActive", True):
            continue
        from_table = format_table_name(rel["fromTable"])
        to_table = format_table_name(rel["toTable"])
        lines.append(f"- {from_table}[{rel['fromColumn']}] -> {to_table}[{rel['toColumn']}]")

    # DAX Conventions
    lines.extend([
        "",
        "### DAX Conventions",
        "- Quote table names with spaces or reserved words: 'Date', 'Currency Exchange'",
        "- Use 'Date'[Date] for time intelligence functions (TOTALYTD, SAMEPERIODLASTYEAR, etc.)",
        "- Use DIVIDE() instead of / for safe division",
        "- Use VALUES() or DISTINCT() with quotes: VALUES('Date'[Year])",
    ])

    return "\n".join(lines)


def format_minimal(schema: dict) -> str:
    """Generate minimal schema (~200-400 tokens)."""
    tables = schema.get("tables", [])
    relationships = schema.get("relationships", [])

    lines = ["Tables:"]
    for table in tables:
        if table.get("isHidden"):
            continue
        columns = [c["name"] for c in table.get("columns", [])
                   if not c.get("isHidden") and not c["name"].startswith("RowNumber")]
        if not columns:
            continue
        # Limit to 8 most relevant columns
        lines.append(f"  {table['name']}: {', '.join(columns[:8])}")

    lines.append("")
    lines.append("Relationships:")
    for rel in relationships[:6]:  # Limit relationships
        if rel.get("isActive", True):
            lines.append(f"  {rel['fromTable']}->{rel['toTable']}")

    lines.append("")
    lines.append("Note: Quote 'Date' table in DAX. Use 'Date'[Date] for time intelligence.")

    return "\n".join(lines)


def format_full(schema: dict) -> str:
    """Generate full schema with all details (~2000-3000 tokens)."""
    lines = ["# Power BI Data Model Schema", ""]

    # Model info
    model = schema.get("model", {})
    if model:
        lines.extend([
            "## Model Information",
            f"- Name: {model.get('name', 'N/A')}",
            f"- Compatibility Level: {model.get('compatibilityLevel', 'N/A')}",
            ""
        ])

    lines.append("## Tables")

    for table in schema.get("tables", []):
        hidden_marker = " [HIDDEN]" if table.get("isHidden") else ""
        lines.append(f"\n### {table['name']}{hidden_marker}")

        if table.get("description"):
            lines.append(f"*{table['description']}*")

        lines.append("\n| Column | Type | Key | Format |")
        lines.append("|--------|------|-----|--------|")

        for col in table.get("columns", []):
            if col["name"].startswith("RowNumber"):
                continue
            key = "PK" if col.get("isKey") else ""
            fmt = col.get("formatString", "")[:20] if col.get("formatString") else ""
            hidden = " (hidden)" if col.get("isHidden") else ""
            lines.append(f"| {col['name']}{hidden} | {col['dataType']} | {key} | {fmt} |")

        # Measures
        measures = table.get("measures", [])
        if measures:
            lines.append("\n**Measures:**")
            for m in measures[:10]:  # Limit to 10 measures per table
                expr_preview = m.get("expression", "")[:60].replace("\n", " ")
                lines.append(f"- `{m['name']}` = {expr_preview}...")

    # Relationships
    lines.extend(["", "## Relationships", ""])
    lines.append("| From | To | Cardinality | Direction | Active |")
    lines.append("|------|----|-------------|-----------|--------|")

    for rel in schema.get("relationships", []):
        from_ref = f"{rel['fromTable']}[{rel['fromColumn']}]"
        to_ref = f"{rel['toTable']}[{rel['toColumn']}]"
        cardinality = rel.get("cardinality", "N/A")
        direction = rel.get("crossFilterDirection", "N/A")
        active = "Yes" if rel.get("isActive", True) else "No"
        lines.append(f"| {from_ref} | {to_ref} | {cardinality} | {direction} | {active} |")

    # DAX Conventions
    lines.extend([
        "",
        "## DAX Conventions",
        "",
        "### Quoting Rules",
        "- Table names with spaces require quotes: `'Currency Exchange'[Rate]`",
        "- Reserved words require quotes: `'Date'[Date]`, `'Year'[Value]`",
        "- Column names with spaces use brackets: `Sales[Net Price]`",
        "",
        "### Time Intelligence",
        "- Date table key column: `'Date'[Date]`",
        "- YTD: `TOTALYTD(expr, 'Date'[Date])`",
        "- Same period last year: `CALCULATE(expr, SAMEPERIODLASTYEAR('Date'[Date]))`",
        "- Date range: `DATESINPERIOD('Date'[Date], MAX('Date'[Date]), -3, MONTH)`",
        "",
        "### Best Practices",
        "- Use `DIVIDE(a, b)` instead of `a / b`",
        "- Use `VALUES('Table'[Column])` with quotes for table functions",
        "- Prefix variables with underscore or use descriptive names",
    ])

    return "\n".join(lines)


def extract_schema(schema_json: dict, format: SchemaFormat = "compact") -> str:
    """
    Extract and format schema for LLM prompts.

    Args:
        schema_json: Raw schema from Power BI MCP get_model_info
        format: Output format - "full", "compact", or "minimal"

    Returns:
        Formatted schema string
    """
    if format == "full":
        return format_full(schema_json)
    elif format == "minimal":
        return format_minimal(schema_json)
    else:
        return format_compact(schema_json)


def get_schema_prompt(format: SchemaFormat = "compact", schema_file: Optional[str] = None) -> str:
    """
    Get schema prompt, optionally loading from file.

    If schema_file is provided, loads from that file.
    Otherwise, this function should be called with schema data from MCP.

    Args:
        format: Output format
        schema_file: Optional path to schema JSON file

    Returns:
        Formatted schema string
    """
    if schema_file:
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
        return extract_schema(schema, format)
    else:
        raise ValueError("schema_file required when not using MCP directly")


def save_schema(schema_json: dict, output_path: str, format: SchemaFormat = "compact"):
    """Save formatted schema to file."""
    formatted = extract_schema(schema_json, format)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(formatted)
    return output_path


# CLI
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Schema Extractor - Generate LLM-friendly Power BI schema prompts")
        print("")
        print("Usage:")
        print("  python schema_extractor.py <schema.json> [format]")
        print("")
        print("Formats:")
        print("  compact  - Optimized for LLM prompts (default, ~500-800 tokens)")
        print("  minimal  - Just table/column names (~200-400 tokens)")
        print("  full     - Complete schema with all details (~2000-3000 tokens)")
        print("")
        print("Example:")
        print("  python schema_extractor.py model_schema.json compact > prompt_context.md")
        sys.exit(1)

    schema_file = sys.argv[1]
    fmt = sys.argv[2] if len(sys.argv) > 2 else "compact"

    if fmt not in ["full", "compact", "minimal"]:
        print(f"Error: Unknown format '{fmt}'. Use: full, compact, or minimal")
        sys.exit(1)

    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
        print(extract_schema(schema, fmt))
    except FileNotFoundError:
        print(f"Error: File not found: {schema_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {schema_file}: {e}")
        sys.exit(1)
