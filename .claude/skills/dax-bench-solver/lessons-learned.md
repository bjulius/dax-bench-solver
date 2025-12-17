# DAX Bench Solver - Lessons Learned

This file captures patterns and insights from benchmark runs to improve future DAX generation.

## Last Updated
2025-12-14

---

## Model Performance Summary

| Model | Solved | First-Try | Avg Iters | Notes |
|-------|--------|-----------|-----------|-------|
| anthropic/claude-opus-4-5-20251101 | 30/30 (100%) | 30/30 (100%) | 1.0 | Perfect first-try, MCP validated |
| mistralai/mistral-small-3.1-24b-instruct | 30/30 (100%) | 25/30 (83%) | 1.17 | 5 tasks needed 2 iterations |
| google/gemini-2.5-flash | 21/30 (70%) | 7/30 (23%) | N/A | v1 run, basic feedback |

---

## Common Failure Patterns

### Context Transition Tasks
**Tasks**: task-015, task-016, task-017, task-018
**Issue**: Models struggle with CALCULATE context transition and EARLIER function
**Lesson**: When prompting for context transition, explicitly mention:
- Whether row context needs to be converted to filter context
- When EARLIER is appropriate (calculated columns only)
- CALCULATE's role in context transition

### Advanced Filtering
**Tasks**: task-020, task-021
**Issue**: ALLEXCEPT and KEEPFILTERS misuse
**Lesson**:
- ALLEXCEPT removes all filters EXCEPT specified columns
- KEEPFILTERS adds filters instead of replacing them
- Models often confuse these with ALL and FILTER

### Complex Calculations
**Tasks**: task-009, task-026
**Issue**: YoY calculations and cascading fallbacks
**Lesson**:
- Always use DIVIDE() for division operations
- SAMEPERIODLASTYEAR requires proper date table relationship
- Cascading IF/COALESCE patterns need explicit structure

---

## Successful Patterns

### Basic Aggregations (100% success)
- SUM, AVERAGE, COUNT, DISTINCTCOUNT work reliably
- Models understand basic measure syntax well

### Time Intelligence (mostly successful)
- TOTALYTD, DATESYTD work well
- SAMEPERIODLASTYEAR needs explicit date column reference
- Rolling averages (DATESINPERIOD) work with proper hints

### Iterators (good success)
- SUMX, RANKX, TOPN understood well
- Need to specify iterator vs aggregator context

---

## Effective Feedback Strategies

### What Works
1. **Show the expected function**: "Expected solution uses CALCULATE with ALLEXCEPT"
2. **Point out missing functions**: "Your solution is missing DIVIDE for safe division"
3. **Provide task hints**: Include hints from task JSON when available
4. **Show expected vs actual**: When values differ, show both

### What Doesn't Work
1. **Just saying "wrong"**: Too vague, model repeats same mistake
2. **Showing full answer**: Model may just copy without understanding
3. **Generic "try again"**: No guidance for improvement

---

## DAX Function Reference for Prompts

### Must-Know Functions by Category

**Aggregation**: SUM, AVERAGE, COUNT, COUNTROWS, DISTINCTCOUNT, MIN, MAX
**Time Intelligence**: TOTALYTD, DATESYTD, SAMEPERIODLASTYEAR, DATEADD, DATESINPERIOD
**Filtering**: CALCULATE, FILTER, ALL, ALLEXCEPT, REMOVEFILTERS, KEEPFILTERS
**Iterators**: SUMX, AVERAGEX, MAXX, MINX, COUNTX, RANKX
**Table**: SUMMARIZE, ADDCOLUMNS, SELECTCOLUMNS, TOPN, VALUES, DISTINCT
**Context**: EARLIER, EARLIEST (calculated columns only), SELECTEDVALUE
**Logical**: IF, SWITCH, DIVIDE, COALESCE, ISBLANK, IFERROR
**Relationships**: TREATAS, USERELATIONSHIP, CROSSFILTER

---

## Prompt Engineering Tips

### For Basic Tasks
- Simple, direct prompts work fine
- Include table and column names

### For Intermediate Tasks
- Mention the primary DAX function expected
- Include data model context (relationships)
- Specify return type (number, percentage, text)

### For Advanced Tasks
- Break down the logic into steps
- Explicitly mention context transition if needed
- Provide example expected output if available
- Include hints about edge cases (nulls, zeros)

---

## Run History

### Run 5: 2025-12-14 (Claude Opus 4.5, MCP Live Validation)
- Model: anthropic/claude-opus-4-5-20251101
- Result: 30/30 (100%)
- First-try: 30/30 (100%)
- Avg Iterations: 1.0
- Notes: Perfect score, zero corrections needed. Used live MCP validation against Power BI.

### Run 4: 2025-12-14 (Mistral Small 3.1, MCP Live Validation)
- Model: mistralai/mistral-small-3.1-24b-instruct
- Result: 30/30 (100%)
- First-try: 25/30 (83.3%)
- Avg Iterations: 1.17
- Cost: ~$0.015
- Notes: 5 tasks required 2nd iteration

**Multi-Iteration Fixes (Mistral):**
| Task | Error | Fix |
|------|-------|-----|
| task-010 | Used TOTALMTD without date context | Changed to DATESYTD |
| task-019 | Used Sales[Unit Price] for filter | Changed to Product[Unit Price] |
| task-025 | Used COALESCE (flagged by validator) | Changed to IF(ISBLANK(...)) |
| task-026 | Missing SUM() aggregation | Added SUM() around column refs |
| task-030 | Wrong fiscal year end "7/01" | Changed to "6/30" (year END date) |

### Run 1: 2025-12-13 (v1, basic feedback)
- Model: google/gemini-2.5-flash
- Result: 21/30 (70%)
- First-try: 7/30 (23%)
- Cost: $0.0529
- Notes: Basic "pattern didn't match" feedback

---

## Validated Learnings (High Value)

### Table Qualifiers Matter (task-019)
**Problem**: Models confuse `Sales[Unit Price]` with `Product[Unit Price]`
**Rule**: When filtering on product attributes in CALCULATE, use the Product table
**Feedback that works**: "Unit Price filter should use Product[Unit Price], not Sales[Unit Price]"

### Fiscal Year End Date (task-030)
**Problem**: Models use fiscal year START date instead of END date
**Rule**: DATESYTD year_end_date parameter is the ENDING date (e.g., "6/30" for July-start fiscal year)
**Feedback that works**: "The year_end_date parameter is the END of fiscal year, not the start. Use '6/30' not '7/01'"

### COALESCE Validation Issue (task-025)
**Problem**: COALESCE is valid DAX (since 2020) but static validator may flag it
**Rule**: COALESCE is valid, but IF(ISBLANK(...)) is universally accepted
**Note**: Consider updating dax_functions_reference.json to include COALESCE

### Running Total Context (task-010)
**Problem**: TOTALMTD returns NULL without proper date context
**Rule**: Use DATESYTD for year-to-date running totals without explicit date filters
**Feedback that works**: "DATESYTD is more reliable for running totals than TOTALMTD in measure context"

---

## TODO: Future Improvements

- [x] Add actual Power BI execution validation (DONE - MCP integration)
- [x] Capture real error messages from DAX engine (DONE - via MCP)
- [x] Compare generated values to expected values (DONE - reference_values.json)
- [ ] Build category-specific prompt templates
- [ ] Add few-shot examples for difficult patterns
- [ ] Integrate lessons-learned reading into benchmark scripts
- [ ] Auto-update lessons-learned from multi-iteration runs
