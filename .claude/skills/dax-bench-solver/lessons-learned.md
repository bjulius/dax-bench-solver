# DAX Bench Solver - Lessons Learned

This file captures patterns and insights from benchmark runs to improve future DAX generation.

## Last Updated
2025-12-17

---

## Model Performance Summary

| Model | Benchmark | Solved | First-Try | Avg Iters | Notes |
|-------|-----------|--------|-----------|-----------|-------|
| anthropic/claude-opus-4-5-20251101 | DAX-30 | 30/30 (100%) | 30/30 (100%) | 1.0 | Perfect first-try, MCP validated |
| mistralai/mistral-small-3.1-24b-instruct | DAX-30 | 30/30 (100%) | 25/30 (83%) | 1.17 | 5 tasks needed 2 iterations |
| google/gemini-2.5-flash | DAX-30 | 21/30 (70%) | 7/30 (23%) | N/A | v1 run, basic feedback |
| deepseek/deepseek-chat-v3.1 | BigfootDAX | 7/10 (70%) | 7/10 | 1.0 | Single-shot mode |
| anthropic/claude-haiku-4.5 | BigfootDAX | 6/10 (60%) | 6/10 | 1.0 | Single-shot; overcomplicates patterns |
| anthropic/claude-opus-4.5 | BigfootDAX | 7/10 (70%) | 7/10 | 1.0 | Single-shot mode |
| **deepseek/deepseek-chat-v3.1** | **BigfootDAX+** | **Partial** | **1/1** | 1.0 | **Iteration mode w/ improved prompts** |
| **anthropic/claude-opus-4.5** | **BigfootDAX+** | **Partial** | **1/2** | 1.5 | **Iteration mode w/ improved prompts** |

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

---

## Run 6: 2025-12-17 - BigfootDAX Multi-Model Comparison (Single-Shot)

**Models Tested:** DeepSeek V3.1, Claude Haiku 4.5, Claude Opus 4.5
**Tasks:** BigfootDAX benchmark (bigfoot-001 to bigfoot-010)
**Dataset:** bfro_reports (4,586 Bigfoot sighting reports)
**Mode:** Single-shot (no iteration)

### Results Summary

| Model | Correct | Score | Cost | Notes |
|-------|---------|-------|------|-------|
| deepseek/deepseek-chat-v3.1 | 7/10 | 70% | $0.0016 | Failed: 001, 003, 006 |
| anthropic/claude-haiku-4.5 | 6/10 | 60% | $0.014 | Failed: 001, 003, 005, 006 |
| anthropic/claude-opus-4.5 | 7/10 | 70% | $0.047 | Failed: 001, 003, 006 |

---

## Run 7: 2025-12-17 - Iteration Benchmark with Improved Prompts

**Models Tested:** DeepSeek V3.1, Claude Haiku 4.5, Claude Opus 4.5
**Focus Tasks:** bigfoot-001 (Longest Streak), bigfoot-003 (Cumulative Counties)
**Mode:** Agentic solve loop with Power BI validation and feedback

### Key Improvement: Live Schema Injection

The single-shot run used "DateTable" in prompts, but the actual Power BI model has "Dates". This was corrected in Run 7.

### Results Summary

| Model | bigfoot-001 (Streak) | bigfoot-003 (Counties) | Notes |
|-------|---------------------|------------------------|-------|
| DeepSeek V3.1 | ✅ Solved iter 1 | Not tested | Used DATEDIFF approach |
| Claude Haiku 4.5 | ❌ Failed 3+ iters | Not tested | Overcomplicates patterns |
| Claude Opus 4.5 | ✅ Solved iter 1 | 🔶 904/905 (iter 3) | Follows patterns well |

### Critical Finding: Prompt Quality > Model Size

With improved prompts (correct schema + trap warnings), **both DeepSeek ($0.0002) and Opus ($0.009) solved the hardest task (bigfoot-001) on iteration 1**. The single-shot run had all models fail this task.

The key improvements were:
1. **Correct table name**: "Dates" instead of "DateTable"
2. **Warning about common trap**: "Do NOT use COUNTROWS inside SUMMARIZE - it counts ALL rows!"
3. **Suggested alternative**: "Use DATEDIFF(MIN, MAX) + 1 for streak length"

### Task-Level Results

| Task | Expected | DeepSeek | Haiku | Opus |
|------|----------|----------|-------|------|
| bigfoot-001: Longest Streak | 9 | 2802 ❌ | Error ❌ | 2802 ❌ |
| bigfoot-002: Missing Reports | 53593 | 53593 ✅ | 53593 ✅ | 53593 ✅ |
| bigfoot-003: Cumulative Counties | 905 | 1004 ❌ | 1004 ❌ | 1004 ❌ |
| bigfoot-004: 3rd State Count | 283 | 283 ✅ | 283 ✅ | 283 ✅ |
| bigfoot-005: 3rd State Name | Florida | Florida ✅ | California ❌ | Florida ✅ |
| bigfoot-006: Pareto 80% | 22 | 1 ❌ | 1 ❌ | 21 ❌ |
| bigfoot-007: YoY Change 2010 | -23 | -23 ✅ | -23 ✅ | -23 ✅ |
| bigfoot-008: Avg Temperature | 68.82 | 68.82 ✅ | 68.82 ✅ | 68.82 ✅ |
| bigfoot-009: Total Sightings | 4586 | 4586 ✅ | 4586 ✅ | 4586 ✅ |
| bigfoot-010: Top State Count | 535 | 535 ✅ | 535 ✅ | 535 ✅ |

### New Failure Patterns Discovered

#### Islands and Gaps Pattern (bigfoot-001)
**Problem**: ALL models returned 2802 instead of 9 for longest consecutive streak
**Root Cause**: COUNTROWS inside SUMMARIZE counts ALL rows in the table, not per-group
**Bad Pattern**:
```dax
VAR StreakLengths = SUMMARIZE(DateGroups, [Group], "Count", COUNTROWS(DateGroups))
-- COUNTROWS(DateGroups) returns total rows (2802), not rows per group!
```
**Correct Pattern**: Use GROUPBY with COUNTX(CURRENTGROUP()) or filter-based counting
**Feedback that works**: "COUNTROWS inside SUMMARIZE counts all table rows, not per-group. Use GROUPBY with COUNTX(CURRENTGROUP()) instead."

#### Cumulative with Date Relationship (bigfoot-003)
**Problem**: ALL models returned 1004 instead of 905
**Root Cause**: The expected 905 counts only rows with valid dates (participating in relationship)
**Lesson**: When task mentions "up to selected date", clarify if nulls should be excluded
**Feedback that works**: "The cumulative count should only include rows that have valid dates participating in the date table relationship."

#### Pareto Cumulative Logic (bigfoot-006)
**Problem**: DeepSeek/Haiku returned 1, Opus returned 21 (off by 1)
**Root Cause**: Complex cumulative percentage logic with EARLIER is error-prone
**Lesson**: Pareto analysis requires careful cumulative sum with proper row context handling
**Feedback that works**: "Check that cumulative percentage includes the current state and uses >= comparison correctly."

#### TOPN + MINX for Nth Item (bigfoot-005 - Haiku only)
**Problem**: Haiku used TOPN(3) then MINX, returning alphabetically first ("California") not 3rd ranked ("Florida")
**Bad Pattern**:
```dax
VAR SortedStates = TOPN(3, RankedStates, [@Count], DESC)
RETURN MINX(SortedStates, bfro_reports[state])  -- Returns alphabetically first!
```
**Correct Pattern**: Use RANKX and FILTER for Nth item
**Feedback that works**: "MINX returns the minimum value, not the Nth item. Use FILTER with RANKX = N instead."

### Schema Mismatch Issue

**Critical Learning**: The benchmark prompts referenced `DateTable` but the actual Power BI model had `Dates`. This caused all YoY queries to fail initially until corrected.

**Lesson**: Always extract LIVE schema from Power BI (Step 5 of initialization) and inject it into prompts. Never rely on static schema definitions that may be outdated.

### Haiku Overcomplication Pattern (Run 7)

**Problem**: Even when given explicit working patterns, Claude Haiku 4.5 tends to overcomplicate solutions rather than follow the provided example.

**Example**: Given this working pattern:
```dax
VAR RankedDates = ADDCOLUMNS(SightingsByDate, "Rank", RANKX(...))
VAR GroupedGaps = SUMMARIZE(DateGaps, [GapGroup], "StreakLength", DATEDIFF(MIN(...), MAX(...), DAY) + 1)
```

Haiku generated complex alternatives with SUMPRODUCT, nested FILTER, and invalid RANK syntax instead of adapting the simple pattern.

**Lesson**: When using Haiku for complex DAX patterns, provide even more explicit guidance or consider using DeepSeek V3 (cheaper, follows patterns better) or Opus (more expensive, but reliable).

### DATEDIFF vs COUNTROWS for Streak Length (Run 7)

**Problem**: COUNTROWS inside SUMMARIZE counts ALL table rows, not per-group rows.

**Working Solution**: Use `DATEDIFF(MIN(date), MAX(date), DAY) + 1` to calculate streak length based on date range, which avoids the per-group counting issue.

**Alternative Working Solution**: Use `GROUPBY` with `COUNTX(CURRENTGROUP())` for true per-group counting.

