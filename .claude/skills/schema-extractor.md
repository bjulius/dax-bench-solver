# Schema Extractor Skill

Extract Power BI model schema and format it for LLM prompts with configurable verbosity levels.

## Purpose

Generate well-formatted schema context that helps LLMs write syntactically correct DAX by understanding:
- Available tables and their columns (with data types)
- Relationships between tables
- Existing measures
- Important conventions (quoting rules, date table usage)

## When to Invoke This Skill

Use this skill when:
- Preparing prompts for DAX generation benchmarks
- Building system prompts that need model context
- User asks "what's the schema?" or "show me the data model"
- Before generating DAX that references model objects

## Prerequisites

- **Power BI Desktop**: Open with the target .pbix file
- **Power BI MCP Server**: Connected to the model

## Schema Formats

### Format: `full`
Complete schema with all details - best for comprehensive understanding.
~2000-3000 tokens depending on model size.

### Format: `compact` (Recommended for prompts)
Optimized for LLM prompts - includes essential columns, relationships, and conventions.
~500-800 tokens.

### Format: `minimal`
Just table and column names - for very token-constrained scenarios.
~200-400 tokens.

## Extraction Process

### Step 1: Get Raw Schema

Use Power BI MCP to fetch the complete schema:

```
mcp__powerbi-desktop__get_model_info({ info_type: "schema" })
```

This returns JSON with:
- `model`: metadata (name, compatibility level)
- `tables[]`: each table with columns and measures
- `relationships[]`: all relationships

### Step 2: Process Tables

For each table, extract:
- Table name
- Column names and data types
- Key columns (isKey: true)
- Hidden status (filter out hidden tables/columns for prompts)

Categorize tables:
- **Fact tables**: Tables with foreign keys to dimensions (e.g., Sales)
- **Dimension tables**: Tables with primary keys (e.g., Customer, Product)
- **Date tables**: Tables marked as date tables or with Date column as key
- **Measure tables**: Tables that only contain measures (e.g., _Measures)

### Step 3: Process Relationships

Extract relationship information:
- From table/column (typically fact table)
- To table/column (typically dimension)
- Cardinality (ManyToOne, OneToMany, etc.)
- Cross-filter direction
- Active status

### Step 4: Format Output

#### Compact Format Template (Recommended)

```markdown
## Power BI Data Model

### Tables

**Sales** (fact)
Columns: Order Number, Order Date, Delivery Date, CustomerKey, StoreKey, ProductKey, Quantity, Unit Price, Net Price, Unit Cost

**Customer** (dimension)
Columns: CustomerKey, Name, Gender, City, State, Country, Continent, Age

**Product** (dimension)
Columns: ProductKey, Product Name, Brand, Category, Subcategory, Unit Price, Unit Cost

**Store** (dimension)
Columns: StoreKey, Store Code, Name, Country, State, Square Meters, Status

**'Date'** (date dimension)
Columns: Date [PK], Year, Month, Month Name, Quarter, Week of Year, Fiscal Year

### Relationships
- Sales[CustomerKey] -> Customer[CustomerKey]
- Sales[ProductKey] -> Product[ProductKey]
- Sales[StoreKey] -> Store[StoreKey]
- Sales[Order Date] -> 'Date'[Date]

### DAX Conventions
- Quote table names with spaces or reserved words: 'Date', 'Currency Exchange'
- Date table key: 'Date'[Date] - use for time intelligence (SAMEPERIODLASTYEAR, DATESYTD, etc.)
- Use DIVIDE() instead of / for safe division
```

#### Full Format Template

Include everything from compact plus:
- All column data types
- Format strings
- All measures with expressions
- Hidden objects (marked)
- Relationship cardinality and cross-filter details

#### Minimal Format Template

```
Tables: Sales, Customer, Product, Store, Date
Sales: Order Number, Order Date, CustomerKey, StoreKey, ProductKey, Quantity, Net Price
Customer: CustomerKey, Name, City, State, Country
Product: ProductKey, Product Name, Brand, Category
Store: StoreKey, Name, Country, State
Date: Date, Year, Month, Quarter
Keys: Sales->Customer, Sales->Product, Sales->Store, Sales->Date
```

## Python Implementation

Save to `dax-bench/schema_extractor.py`:

```python
"""
Schema Extractor for Power BI Models
Generates LLM-friendly schema prompts from Power BI MCP data
"""

import json
from typing import Literal

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


def format_compact(schema: dict) -> str:
    """Generate compact schema for LLM prompts (~500-800 tokens)."""
    lines = ["## Power BI Data Model", "", "### Tables", ""]

    tables = schema.get("tables", [])
    relationships = schema.get("relationships", [])

    # Sort tables by type: fact first, then dimensions, then date
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
        # Quote if needed
        display_name = f"'{name}'" if " " in name or name in ["Date"] else name

        # Get visible columns
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
        from_table = f"'{rel['fromTable']}'" if " " in rel["fromTable"] else rel["fromTable"]
        to_table = f"'{rel['toTable']}'" if " " in rel["toTable"] else rel["toTable"]
        lines.append(f"- {from_table}[{rel['fromColumn']}] -> {to_table}[{rel['toColumn']}]")

    # Conventions
    lines.extend([
        "",
        "### DAX Conventions",
        "- Quote table names with spaces or reserved words: 'Date', 'Currency Exchange'",
        "- Use 'Date'[Date] for time intelligence functions (TOTALYTD, SAMEPERIODLASTYEAR, etc.)",
        "- Use DIVIDE() instead of / for safe division",
        "- Use VALUES() or DISTINCT() for table expressions in CROSSJOIN",
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
        lines.append(f"  {table['name']}: {', '.join(columns[:8])}")  # Limit columns

    lines.append("Relationships:")
    for rel in relationships[:6]:  # Limit relationships
        if rel.get("isActive", True):
            lines.append(f"  {rel['fromTable']}->{rel['toTable']}")

    return "\n".join(lines)


def format_full(schema: dict) -> str:
    """Generate full schema with all details (~2000-3000 tokens)."""
    lines = ["# Power BI Data Model Schema", ""]

    # Model info
    model = schema.get("model", {})
    if model:
        lines.extend([
            "## Model Information",
            f"- Compatibility Level: {model.get('compatibilityLevel', 'N/A')}",
            ""
        ])

    lines.append("## Tables")

    for table in schema.get("tables", []):
        hidden_marker = " [HIDDEN]" if table.get("isHidden") else ""
        lines.append(f"\n### {table['name']}{hidden_marker}")

        if table.get("description"):
            lines.append(f"*{table['description']}*")

        lines.append("\n| Column | Type | Key | Hidden |")
        lines.append("|--------|------|-----|--------|")

        for col in table.get("columns", []):
            if col["name"].startswith("RowNumber"):
                continue
            key = "PK" if col.get("isKey") else ""
            hidden = "Yes" if col.get("isHidden") else ""
            lines.append(f"| {col['name']} | {col['dataType']} | {key} | {hidden} |")

        # Measures
        measures = table.get("measures", [])
        if measures:
            lines.append("\n**Measures:**")
            for m in measures[:10]:  # Limit to 10 measures per table
                expr_preview = m.get("expression", "")[:50]
                lines.append(f"- `{m['name']}` = {expr_preview}...")

    # Relationships
    lines.extend(["", "## Relationships", ""])
    lines.append("| From | To | Cardinality | Active |")
    lines.append("|------|----|-----------:|--------|")

    for rel in schema.get("relationships", []):
        from_ref = f"{rel['fromTable']}[{rel['fromColumn']}]"
        to_ref = f"{rel['toTable']}[{rel['toColumn']}]"
        cardinality = rel.get("cardinality", "N/A")
        active = "Yes" if rel.get("isActive", True) else "No"
        lines.append(f"| {from_ref} | {to_ref} | {cardinality} | {active} |")

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


# CLI usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python schema_extractor.py <schema.json> [format]")
        print("Formats: full, compact (default), minimal")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        schema = json.load(f)

    fmt = sys.argv[2] if len(sys.argv) > 2 else "compact"
    print(extract_schema(schema, fmt))
```

## Integration with Other Skills

### Called by: dax-bench-solver
```python
# In benchmark runner
from schema_extractor import extract_schema

# Get schema via MCP
schema = mcp__powerbi-desktop__get_model_info(info_type="schema")

# Format for prompt
schema_context = extract_schema(schema, format="compact")

# Include in system prompt
system_prompt = f"""You are a DAX expert.

{schema_context}

Generate only the DAX measure definition, no explanations."""
```

### Called by: bigfoot-dax-validator
```python
# Validate references exist in schema
schema = mcp__powerbi-desktop__get_model_info(info_type="schema")
# Check if Table[Column] exists...
```

## Example Outputs

### Compact (Default)
```
## Power BI Data Model

### Tables

**Sales** (fact)
Columns: Order Number, Order Date, CustomerKey, ProductKey, Quantity, Net Price, Unit Cost

**Customer** (dimension)
Columns: CustomerKey, Name, Gender, City, State, Country, Age

**Product** (dimension)
Columns: ProductKey, Product Name, Brand, Category, Unit Price

**'Date'** (date)
Columns: Date [PK], Year, Month, Month Name, Quarter, Week of Year

### Relationships
- Sales[CustomerKey] -> Customer[CustomerKey]
- Sales[ProductKey] -> Product[ProductKey]
- Sales[Order Date] -> 'Date'[Date]

### DAX Conventions
- Quote table names with spaces or reserved words: 'Date', 'Currency Exchange'
- Use 'Date'[Date] for time intelligence functions
- Use DIVIDE() instead of / for safe division
```

### Minimal
```
Tables:
  Sales: Order Number, Order Date, CustomerKey, ProductKey, Quantity, Net Price
  Customer: CustomerKey, Name, City, State, Country
  Product: ProductKey, Product Name, Brand, Category
  Date: Date, Year, Month, Quarter
Relationships:
  Sales->Customer
  Sales->Product
  Sales->Date
```
