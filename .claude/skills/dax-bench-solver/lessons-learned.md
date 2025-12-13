# DAX Bench Solver - Lessons Learned

This file captures patterns and insights from benchmark runs to improve future DAX generation.

## Last Updated
2025-12-13

---

## Model Performance Summary

| Model | Solved | First-Try | Notes |
|-------|--------|-----------|-------|
| google/gemini-2.5-flash | 21/30 (70%) | 7/30 (23%) | v1 run, basic feedback |

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

### Run 1: 2025-12-13 (v1, basic feedback)
- Model: google/gemini-2.5-flash
- Result: 21/30 (70%)
- First-try: 7/30 (23%)
- Cost: $0.0529
- Notes: Basic "pattern didn't match" feedback

### Run 2: 2025-12-13 (v2, enhanced feedback)
- Model: google/gemini-2.5-flash
- Result: [pending]
- Notes: Function hints, task hints, expression matching

---

## TODO: Future Improvements

- [ ] Add actual Power BI execution validation
- [ ] Capture real error messages from DAX engine
- [ ] Compare generated values to expected values
- [ ] Build category-specific prompt templates
- [ ] Add few-shot examples for difficult patterns
