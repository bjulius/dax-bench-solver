# Bigfoot DAX Validator Skill

## Purpose
Validate DAX measures for syntax correctness, best practices, performance patterns, and model reference integrity.

## When to Use
Invoke this skill when:
- Creating new DAX measures
- Reviewing existing measures for quality
- Debugging DAX errors
- Optimizing measure performance
- User asks to "validate DAX" or "check my measures"

## Validation Categories

### 1. Reference Validation
Check that all referenced objects exist in the model:
- Table names: `'TableName'` or `TableName` must exist
- Column references: `TableName[ColumnName]` must exist
- Measure references: `[MeasureName]` must exist in model

### 2. Syntax Validation
Check for common syntax issues:
- Balanced parentheses and brackets
- Proper quoting of table names with spaces
- Valid operator usage
- Correct function argument counts

### 3. Best Practice Validation
Check for DAX anti-patterns:

#### High Severity
- **Naked CALCULATE**: `CALCULATE(expression)` without filters - usually indicates a bug
- **Scalar in FILTER**: Using scalar comparisons instead of table functions
- **FILTER on large tables**: `FILTER(ALL(LargeTable), ...)` instead of column filters
- **Circular dependency**: Measure references itself directly or indirectly

#### Medium Severity
- **Missing DIVIDE**: Using `/` operator without handling divide-by-zero
- **ALL vs REMOVEFILTERS**: Using `ALL()` when `REMOVEFILTERS()` is more appropriate
- **Hardcoded values**: Magic numbers that should be parameters
- **EARLIER misuse**: Using EARLIER when not in row context

#### Low Severity (Suggestions)
- **Format strings**: Measures without format strings
- **Descriptions**: Measures without descriptions
- **Display folders**: Measures not organized in folders
- **Long expressions**: Measures over 50 lines without comments

### 4. Performance Validation
Check for known performance issues:

#### Critical Performance
- **Row-by-row operations**: SUMX/MAXX over large unfiltered tables
- **CallbackDataID**: Patterns that cause storage engine cache misses
- **Nested iterators**: SUMX inside SUMX without good reason
- **DISTINCT in iterators**: Creating large intermediate tables

#### Warning Performance
- **Multiple CALCULATE**: Same filter applied multiple times
- **Redundant ALL**: ALL() on tables already removed from filter context
- **Unnecessary variables**: VAR that's only used once in simple expression

## Validation Process

When validating DAX:

1. **Parse the expression** - Extract table refs, column refs, measure refs, functions
2. **Check model references** - Use Power BI MCP to verify objects exist
3. **Pattern matching** - Check against anti-pattern rules
4. **Report findings** - Categorize by severity with fix suggestions

## Output Format

```
## DAX Validation Report: [Measure Name]

### Summary
- Errors: X
- Warnings: Y
- Suggestions: Z

### Errors (Must Fix)
1. **[Error Type]**: Description
   - Line: X
   - Fix: Suggestion

### Warnings (Should Fix)
1. **[Warning Type]**: Description
   - Impact: Explanation
   - Fix: Suggestion

### Suggestions (Consider)
1. **[Suggestion Type]**: Description
   - Benefit: Explanation
```

## DAX Anti-Pattern Reference

### Pattern: Naked CALCULATE
```dax
// BAD - What does this do?
Measure = CALCULATE(SUM(Sales[Amount]))

// GOOD - Explicit intent
Measure = CALCULATE(SUM(Sales[Amount]), REMOVEFILTERS())
```

### Pattern: Scalar in FILTER
```dax
// BAD - Row-by-row evaluation
CALCULATE(
    [Sales],
    FILTER(ALL(Date), Date[Year] = 2024)
)

// GOOD - Optimized filter
CALCULATE(
    [Sales],
    Date[Year] = 2024
)
```

### Pattern: Missing DIVIDE
```dax
// BAD - Crashes on zero
Ratio = [Numerator] / [Denominator]

// GOOD - Safe division
Ratio = DIVIDE([Numerator], [Denominator])
```

### Pattern: EARLIER Misuse
```dax
// BAD - Not in row context
Measure = CALCULATE(SUM(Sales[Amount]), EARLIER(Sales[Product]))

// EARLIER is for calculated columns with nested row contexts, not measures
```

### Pattern: Nested Iterators
```dax
// BAD - O(n*m) complexity
Measure =
SUMX(
    Products,
    SUMX(Customers, [Sales])  // Inner iterator for each product
)

// GOOD - Consider SUMMARIZE or restructuring
```

## Integration with Power BI MCP

Use these MCP tools during validation:
- `list_objects(type: "tables")` - Get all table names
- `list_objects(type: "columns", table: "X")` - Get columns for validation
- `list_objects(type: "measures")` - Get existing measures
- `search_model(query: "X", mode: "name")` - Find specific objects
- `run_dax(query: "EVALUATE ROW(...)")` - Test measure execution

## Example Validation Session

```
User: Validate this measure:
Sales YTD = CALCULATE(SUM(Sales[Amount]), DATESYTD(Date[Date]))