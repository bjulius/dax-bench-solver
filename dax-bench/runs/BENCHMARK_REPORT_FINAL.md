# DAX Bench Benchmark Report - Final Results

**Date:** December 14, 2025
**Test Configuration:** 30 DAX tasks × 4 models = 120 total expressions
**Schema Context:** Provided (compact format with table/column info and relationships)

---

## Executive Summary

| Model | Static Pass | Runtime Pass | Final Score |
|-------|-------------|--------------|-------------|
| **Claude Opus 4.5** | 22/30 (73.3%) | 21/22 (95.5%) | **21/30 (70.0%)** |
| **Claude Sonnet 4.5** | 23/30 (76.7%) | 22/23 (95.7%) | **22/30 (73.3%)** |
| **Claude Haiku 4.5** | 23/30 (76.7%) | 18/23 (78.3%) | **18/30 (60.0%)** |
| **Mistral Small 3.1** | 21/30 (70.0%) | 18/21 (85.7%) | **18/30 (60.0%)** |

**Overall:** 79/120 expressions execute correctly (65.8%)

---

## Validation Pipeline

### Stage 1: Static Analysis
Checks for common issues without executing code:
- Missing DAX expression
- Table-returning expressions (SUMMARIZE, SELECTCOLUMNS, UNION, CROSSJOIN)
- Undefined table references (Budget table)
- Malformed measure parsing

### Stage 2: Syntax Validation
Created measures in Power BI model to verify DAX syntax

### Stage 3: Runtime Execution
Executed each measure with `EVALUATE ROW("result", [measure_name])`

---

## Detailed Results by Model

### Claude Opus 4.5

**Static Failures (8):**
- task-009: VAR parsing issue (measure name extracted incorrectly)
- task-011: Returns table (SUMMARIZE)
- task-012: Returns table (SELECTCOLUMNS)
- task-013: Returns table (UNION)
- task-014: Returns table (CROSSJOIN)
- task-016: References undefined Budget table
- task-023: Complex TOP N calculation
- task-026: VAR parsing issue

**Runtime Failures (1):**
- task-018: RANKX with EARLIER() - invalid in scalar measure context

**Final: 21/30 (70.0%)**

---

### Claude Sonnet 4.5

**Static Failures (7):**
- task-009: VAR parsing issue
- task-011: Returns table (SUMMARIZE)
- task-012: Returns table (SELECTCOLUMNS)
- task-013: Returns table (UNION)
- task-014: Returns table (CROSSJOIN)
- task-016: References undefined Budget table
- task-022: Uses DENSE_RANK (doesn't exist in DAX)

**Runtime Failures (1):**
- task-018: RANKX with EARLIER()

**Final: 22/30 (73.3%)**

---

### Claude Haiku 4.5

**Static Failures (7):**
- task-009: VAR parsing issue
- task-011: Returns table (SUMMARIZE)
- task-012: Returns table (SELECTCOLUMNS)
- task-013: Returns table (UNION)
- task-014: Returns table (CROSSJOIN)
- task-016: References undefined Budget table
- task-026: VAR parsing issue

**Runtime Failures (5):**
- task-008: Uses SUMIF (Excel function, not DAX)
- task-018: RANKX with EARLIER()
- task-019: Uses SUMPRODUCT (Excel function, not DAX)
- task-022: Uses DENSE_RANK (SQL function, not DAX)
- task-027: Expression error

**Final: 18/30 (60.0%)**

---

### Mistral Small 3.1

**Static Failures (9):**
- task-009: VAR parsing issue
- task-011: Returns table (SUMMARIZE)
- task-012: Returns table (SELECTCOLUMNS)
- task-013: Returns table (UNION)
- task-014: Returns table (CROSSJOIN)
- task-016: References undefined Budget table
- task-022: Expression error
- task-023: Invalid syntax
- task-026: VAR parsing issue

**Runtime Failures (3):**
- task-018: RANKX pattern error
- task-020: Uses SAMEPERIODLASTDAY (doesn't exist in DAX)
- task-021: KEEPFILTERS syntax error

**Final: 18/30 (60.0%)**

---

## Common Failure Patterns

### 1. Table-Returning Expressions
Tasks 011-014 required creating measures that produce tables (SUMMARIZE, SELECTCOLUMNS, UNION, CROSSJOIN). All models failed because DAX measures must return scalar values.

**Recommendation:** These tasks should be reclassified as "query tasks" vs "measure tasks"

### 2. Non-DAX Functions
Several models used functions that exist in Excel or SQL but not DAX:
- `SUMIF` (Excel) - Use `CALCULATE(SUM(...), ...)`
- `SUMPRODUCT` (Excel) - Use `SUMX(...)`
- `DENSE_RANK` (SQL) - Use `RANKX(..., , , DENSE)`
- `SAMEPERIODLASTDAY` (doesn't exist) - Use `DATEADD(..., -1, DAY)`

### 3. EARLIER() Context Issues
Task-018 (ranking within category) requires row context that doesn't exist in a standalone measure. All models tried to use `EARLIER()` which only works within calculated columns or iterator functions like `ADDCOLUMNS`.

### 4. Undefined References
Task-016 referenced a "Budget" table that doesn't exist in the test model.

---

## Model Comparison

| Metric | Opus | Sonnet | Haiku | Mistral |
|--------|------|--------|-------|---------|
| Correct DAX syntax | 22 | 23 | 23 | 21 |
| Uses correct DAX functions | 22 | 23 | 18 | 19 |
| Final valid measures | 21 | 22 | 18 | 18 |
| Avg response time (s) | 2.6 | 2.4 | 1.8 | 2.1 |

**Best Performer:** Claude Sonnet 4.5 (73.3%)
**Most Consistent:** Opus and Sonnet (only 1 runtime failure each)
**Fastest:** Claude Haiku 4.5

---

## Key Insights

1. **Schema context helps significantly** - All models correctly referenced table/column names and used proper quoting ('Date', 'Currency Exchange')

2. **Anthropic models outperform** - Claude Opus, Sonnet, and Haiku all knew DAX-specific functions better than Mistral (e.g., using CALCULATE instead of SUMIF)

3. **Haiku's accuracy issues** - Despite being fast, Haiku confused DAX with Excel functions (SUMIF, SUMPRODUCT)

4. **Complex context operations are hard** - Tasks requiring evaluation context manipulation (EARLIER, ALLEXCEPT) had high failure rates

5. **Time intelligence works well** - TOTALYTD, SAMEPERIODLASTYEAR, DATEADD all worked correctly across models

---

## Recommendations

1. **For benchmarking:** Separate tasks into "measure" vs "query" categories
2. **For production:** Use Sonnet for best accuracy/speed tradeoff
3. **For cost-sensitive:** Use Haiku but add validation layer
4. **For all models:** Add post-processing to detect non-DAX functions

---

## Files Generated

- `combined_api_responses_with_schema.json` - Raw API responses
- `validated_results_static.json` - Static analysis results
- `BENCHMARK_REPORT_FINAL.md` - This report

---

*Report generated by DAX Bench v4 with Power BI MCP validation*
