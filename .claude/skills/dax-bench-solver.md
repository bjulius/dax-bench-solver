# DAX Bench Solver Skill

Iteratively solve DAX Bench problems using any LLM model via OpenRouter, tracking iterations to solution with full observability.

## Purpose

This skill demonstrates that **any decent LLM can reliably solve DAX problems through iteration**, not just first-try accuracy. The key insight: with a validated solution to iterate against, even smaller/cheaper models reach correct answers - they just take more loops.

## When to Invoke This Skill

Use this skill when the user wants to:
- "Solve a DAX Bench task"
- "Compare models on DAX"
- "Run the DAX benchmark"
- "Test model X against model Y"
- "Show iteration comparison"

## Prerequisites

1. **OpenRouter API Key**: Set as environment variable `OPENROUTER_DAXBENCH_API_KEY` (or `OPENROUTER_API_KEY`)
2. **Power BI Desktop**: Open with the target `.pbix` file
3. **Power BI MCP Server**: Connected to the model

---

# ⛔ MANDATORY INITIALIZATION CHECKLIST

## YOU MUST COMPLETE ALL STEPS BELOW BEFORE ANY BENCHMARK WORK. NO EXCEPTIONS.

Every time the DAX Bench Solver skill is initiated, you MUST:

1. ✅ Display this checklist to the user
2. ✅ Execute each step in order
3. ✅ Report status of each step before proceeding
4. ✅ STOP if any step fails

```
╔══════════════════════════════════════════════════════════════════════╗
║               DAX BENCH SOLVER - INITIALIZATION                       ║
╠══════════════════════════════════════════════════════════════════════╣
║  [ ] Step 1: Read Lessons Learned                                    ║
║  [ ] Step 2: Refresh OpenRouter Model Cache                          ║
║  [ ] Step 3: Offer DAX Function List Update                          ║
║  [ ] Step 4: Verify Power BI Connection                              ║
║  [ ] Step 5: Extract Live Schema from Power BI                       ║
║  [ ] Step 6: Load Task Definitions                                   ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## INIT STEP 1: Read Lessons Learned (MANDATORY)

**Action:** Read the lessons-learned file BEFORE any benchmark work.

```
Read: .claude/skills/dax-bench-solver/lessons-learned.md
```

**What to extract:**
- Common failure patterns and how to avoid them
- Effective feedback strategies that work
- Model-specific quirks discovered in previous runs
- Tasks that commonly need multiple iterations
- Run history with performance data

**Report to user:**
> "📚 Lessons Learned loaded. Last updated: {date}. Key patterns: {2-3 bullet points}"

---

## INIT STEP 2: Refresh OpenRouter Model Cache (MANDATORY)

**Action:** ALWAYS refresh the model cache. Do NOT skip this step.

```bash
python dax-bench/fetch_models.py refresh
```

**Then report statistics:**
```bash
python dax-bench/fetch_models.py stats
```

**Report to user:**
> "🔄 Model cache refreshed. {total} models available. {free} free models. Top providers: {list}"

**CRITICAL RULES:**
- NEVER hardcode or guess model identifiers
- ALWAYS read from cache file: `dax-bench/models_cache.json`
- Use EXACT `id` field from cache (e.g., `anthropic/claude-opus-4-5-20251101`)
- DO NOT use shortened names like "opus" or "claude-opus"

---

## INIT STEP 3: Offer DAX Function List Update (MANDATORY)

**Action:** Read the DAX function reference and offer to update it.

```
Read: dax-bench/dax_functions_reference.json
```

**Extract the `last_updated` field, then ASK THE USER using AskUserQuestion tool:**

> "The DAX function validation list was last updated on **{last_updated}**.
> Would you like me to check DAX.guide for new functions?"
>
> Options:
> - **Yes** - Fetch https://dax.guide/functions/ and compare
> - **No** - Proceed with current list

**If user says YES:**
1. Fetch `https://dax.guide/functions/`
2. Extract all function names from the page
3. Compare against current `valid_functions` list
4. Add any new functions found
5. Update `last_updated` to today's date
6. Report: "Added X new functions: {list}" or "No new functions found"

**If user says NO:**
- Proceed with workflow (but still report the last update date was noted)

---

## INIT STEP 4: Verify Power BI Connection (MANDATORY)

**Action:** Check that Power BI MCP server is connected.

```
mcp__powerbi-desktop__manage_model_connection(operation: "get_current")
```

**Expected response:**
- `connected: true`
- `table_count: > 0`

**If NOT connected:**
- STOP the workflow
- Instruct user: "Please open Power BI Desktop with your target .pbix file and ensure the MCP server is running"

**Report to user:**
> "✅ Power BI connected. Model has {table_count} tables."

---

## INIT STEP 5: Extract Live Schema from Power BI (MANDATORY)

**Action:** Extract the ACTUAL schema from the connected Power BI model.

**5a. List all tables:**
```
mcp__powerbi-desktop__list_objects(type: "tables")
```

**5b. For each table, list columns:**
```
mcp__powerbi-desktop__list_objects(type: "columns", table: "{table_name}")
```

**5c. List relationships:**
```
mcp__powerbi-desktop__list_objects(type: "relationships")
```

**5d. List existing measures:**
```
mcp__powerbi-desktop__list_objects(type: "measures")
```

**Store this schema for injection into prompts. Format as:**
```
Schema Summary:
- Tables: {list of table names}
- Key columns per table: {table: [columns]}
- Relationships: {from -> to (type)}
- Existing measures: {count} in {table}
```

**Report to user:**
> "📊 Schema extracted: {N} tables, {M} relationships, {K} existing measures."

**CRITICAL:** This schema MUST be injected into the `dataModelContext` section of every prompt sent to the LLM. Do NOT use static schema from task files if live schema differs.

---

## INIT STEP 6: Load Task Definitions (MANDATORY)

**Action:** Load the task(s) to be solved based on user request.

**Task locations:**
```
dax-bench/tasks/
├── basic/         (task-001 to task-006)
├── intermediate/  (task-007 to task-020)
└── advanced/      (task-021 to task-030)
```

**Each task JSON contains:**
- `prompt.system`: System prompt for LLM
- `prompt.user`: The DAX question
- `prompt.dataModelContext`: Schema (**REPLACE with live schema from Step 5**)
- `expectedOutput.dax`: Correct DAX
- `expectedOutput.alternativeCorrect`: Other valid solutions
- `expectedOutput.expectedResult`: (some tasks) Actual values to validate

**Report to user:**
> "📝 Loaded {N} task(s): {task_ids}. Complexity: {level}."

---

## INITIALIZATION COMPLETE

Only after ALL 6 steps are completed successfully, display:

```
╔══════════════════════════════════════════════════════════════════════╗
║  ✅ INITIALIZATION COMPLETE                                          ║
╠══════════════════════════════════════════════════════════════════════╣
║  Lessons Learned: Loaded ({date})                                    ║
║  Model Cache: {total} models available                               ║
║  DAX Functions: {count} functions (updated: {date})                  ║
║  Power BI: Connected ({table_count} tables)                          ║
║  Schema: Extracted and ready for prompt injection                    ║
║  Tasks: {N} task(s) loaded                                           ║
╠══════════════════════════════════════════════════════════════════════╣
║  Ready to begin benchmark. Proceeding to solve loop...               ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

# ⚠️ LESSONS LEARNED: READ BEFORE, WRITE AFTER (ALL MODELS)

## The Lessons Learned Cycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LESSONS LEARNED LIFECYCLE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   BEFORE RUN (Init Step 1)           DURING RUN (Solve Loop)       │
│   ┌─────────────────────┐           ┌─────────────────────┐        │
│   │ READ lessons-       │           │ APPLY patterns to:  │        │
│   │ learned.md          │ ───────▶  │ - Craft prompts     │        │
│   │                     │           │ - Give feedback     │        │
│   │ Extract:            │           │ - Avoid known traps │        │
│   │ - Failure patterns  │           └─────────────────────┘        │
│   │ - What works        │                     │                    │
│   │ - Model quirks      │                     ▼                    │
│   └─────────────────────┘    AFTER **ALL MODELS** COMPLETE         │
│                              ┌─────────────────────┐               │
│                              │ WRITE new learnings │               │
│                  ◀────────── │ to lessons-         │               │
│                              │ learned.md          │               │
│                              └─────────────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⛔ CRITICAL: Fair Comparison Rule

**When comparing multiple models, DO NOT write lessons learned until ALL models have completed.**

```
WRONG (Unfair):
  Run Model A → Write lessons → Run Model B → Write lessons → Run Model C
  ❌ Model B benefits from Model A's learnings
  ❌ Model C benefits from both A and B's learnings

CORRECT (Fair):
  Run Model A → Run Model B → Run Model C → Write ALL lessons
  ✅ All models start with same prior knowledge
  ✅ Fair comparison achieved
```

**Enforcement:**
- During a multi-model comparison run, accumulate learnings in memory
- Only write to lessons-learned.md after the LAST model completes
- Include learnings from ALL models in a single update

---

## BEFORE RUN: Apply Existing Lessons (Init Step 1)

When you read lessons-learned.md in Step 1, **actively use this knowledge**:

### During Prompt Construction
- Check "Common Failure Patterns" for the task category
- Include hints from "Validated Learnings" in the prompt
- Reference model-specific quirks if using a previously-tested model

### During Iteration Feedback
- Use "Effective Feedback Strategies" section
- Apply specific feedback phrases that worked before
- Avoid generic "try again" messages

---

## AFTER ALL MODELS COMPLETE: Write Lessons (MANDATORY)

**You MUST update the lessons-learned file after ALL models in the comparison set have completed.**

### What to Write

| Section | When to Update | What to Add |
|---------|----------------|-------------|
| **Last Updated** | Always | Today's date |
| **Model Performance Summary** | Always | New row for EACH model tested |
| **Run History** | Always | New run entry with all models |
| **Multi-Iteration Fixes** | If any task took >1 iteration | Error → Feedback → Lesson (per model) |
| **Validated Learnings** | If a new pattern emerged | Problem → Rule → Feedback |

### Multi-Iteration Documentation Format

For EVERY task that required more than 1 iteration, document:

```markdown
### Run {N}: {task_id} - {model_name} ({iterations} iterations)
- **Initial Error**: {What the model got wrong on first try}
- **Error Type**: {syntax|semantic|wrong_value|missing_function}
- **Feedback Given**: "{Exact feedback text that fixed it}"
- **Lesson for Future**: {Pattern to remember for similar tasks}
```

### Comparison Run Entry Format

```markdown
## Run {N}: {date} - Multi-Model Comparison

**Models Tested:** {model_1}, {model_2}, {model_3}
**Tasks:** {task_list or "all"}

### Results Summary
| Model | Solved | First-Try | Avg Iters | Cost |
|-------|--------|-----------|-----------|------|
| {model_1} | X/Y | X/Y | N.N | $X.XX |
| {model_2} | X/Y | X/Y | N.N | $X.XX |
| {model_3} | X/Y | X/Y | N.N | $X.XX |

### Multi-Iteration Fixes
{All multi-iteration entries for all models}

### New Patterns Discovered
{Any new learnings applicable to future runs}
```

### Write Location

```
Edit: .claude/skills/dax-bench-solver/lessons-learned.md
```

---

## File Locations

| File | Purpose | When to Access |
|------|---------|----------------|
| `.claude/skills/dax-bench-solver/lessons-learned.md` | Run history & patterns | Step 1 (read), Post-run (write) |
| `dax-bench/models_cache.json` | OpenRouter model IDs | Step 2 |
| `dax-bench/dax_functions_reference.json` | Valid DAX functions | Step 3 |
| `dax-bench/tasks/{level}/task-XXX.json` | Task definitions | Step 6 |
| `dax-bench/runs/` | Run logs | Created during solve loop |

---

# WORKFLOW (After Initialization)

## Step 1: Select Task(s)

Load task(s) from the `dax-bench/tasks/` directory:

```
dax-bench/tasks/
├── basic/         (6 tasks: 001-005, 025)
├── intermediate/  (13 tasks)
└── advanced/      (11 tasks)
```

Each task JSON contains:
- `prompt.system`: System prompt for LLM
- `prompt.user`: The DAX question
- `prompt.dataModelContext`: Schema information
- `expectedOutput.dax`: Correct DAX
- `expectedOutput.alternativeCorrect`: Other valid solutions
- `expectedOutput.expectedResult`: (some tasks) Actual values to validate

### Step 2: Discover & Select Model(s)

**Use `fetch_models.py` to discover available models:**

```bash
cd dax-bench

# Refresh model cache from OpenRouter API (caches for 24h)
python fetch_models.py refresh

# View stats on available models
python fetch_models.py stats

# Find best FREE models (ranked by capability)
python fetch_models.py free

# Find cheapest FLASH/efficient models
python fetch_models.py flash

# Find FRONTIER (top-tier) models
python fetch_models.py frontier

# Find best VALUE under a cost threshold
python fetch_models.py value --max-cost 0.5

# Find REASONING-specialized models (R1, o1, etc.)
python fetch_models.py reasoning

# Search by name
python fetch_models.py search --query "gemini"

# Find models by provider
python fetch_models.py provider --query "anthropic"

# Output as JSON for scripting
python fetch_models.py free --json
```

**Model Tiers:**

| Tier | Description | Examples |
|------|-------------|----------|
| **free** | $0 cost, rate-limited | gemini-2.0-flash-exp:free, llama-3.3-70b:free |
| **flash** | Fast, cheap, efficient | Gemini 2.5 Flash, Haiku, Ministral |
| **strong** | Good performance, moderate cost | Sonnet, DeepSeek V3, GPT-4o |
| **frontier** | Top accuracy, premium cost | Opus 4.5, GPT-5.2, Gemini 3 Pro |
| **reasoning** | Extended thinking (slower) | DeepSeek R1, o1, o3 |

**Quick Picks by Use Case:**

| Goal | Recommended Model(s) |
|------|---------------------|
| Best accuracy | `anthropic/claude-opus-4.5` |
| Best value | `anthropic/claude-3.5-haiku` |
| Best free | `meta-llama/llama-3.3-70b-instruct:free` |
| Cheapest | `mistralai/ministral-3b` ($0.04/1M) |
| Largest context | `google/gemini-2.5-flash` (1M tokens) |

For comparison runs, select two models (Model A vs Model B).

### Step 3: Solve Loop (Per Model, Per Task)

```
FOR each selected model:
  FOR each selected task:
    iteration = 0
    solved = false
    total_tokens = 0

    WHILE iteration < MAX_ITERATIONS (10) AND NOT solved:
      iteration++

      1. Call OpenRouter API with:
         - model: selected model ID
         - messages: [system prompt, user prompt + context]
         - If iteration > 1: append previous error/feedback

      2. Parse DAX from response

      3. Validate DAX:
         a. Syntax check (create measure in Power BI)
         b. If task has expectedResult: execute and compare values
         c. If no expectedResult: compare to expectedOutput.dax patterns

      4. If validation fails:
         - Log the error
         - Prepare feedback for next iteration
         - Continue loop

      5. If validation passes:
         - solved = true
         - Log success

    Record: {task, model, solved, iterations, tokens, cost, time}
```

### Step 4: Generate Observability Log

Create markdown log at `dax-bench/runs/{timestamp}_{model}_{task}.md`:

```markdown
# DAX Bench Run
- **Task**: task-009 (YoY Growth %)
- **Model**: claude-opus-4.5
- **Timestamp**: 2024-12-13T14:30:00Z
- **Result**: ✅ SOLVED in 2 iterations

## Iteration 1
**Prompt sent**: [truncated prompt]

**Model response**:
```dax
YoY Growth % = (SUM(Sales[Net Price]) - CALCULATE(SUM(Sales[Net Price]), SAMEPERIODLASTYEAR(Date[Date]))) / CALCULATE(SUM(Sales[Net Price]), SAMEPERIODLASTYEAR(Date[Date]))
```

**Validation**: ❌ FAILED
**Error**: Division by zero not handled - expected DIVIDE() function

**Feedback for next iteration**: "The measure fails when previous year has no data. Use DIVIDE() to handle division by zero safely."

---

## Iteration 2
**Model response**:
```dax
YoY Growth % =
VAR CurrentSales = SUM(Sales[Net Price])
VAR PreviousSales = CALCULATE(SUM(Sales[Net Price]), SAMEPERIODLASTYEAR(Date[Date]))
RETURN DIVIDE(CurrentSales - PreviousSales, PreviousSales)
```

**Validation**: ✅ PASSED
- Syntax: Valid
- Output match: Matches alternative pattern #2
- Execution: Returns expected values

---

## Summary
| Metric | Value |
|--------|-------|
| Iterations | 2 |
| Input Tokens | 1,245 |
| Output Tokens | 312 |
| Total Cost | $0.047 |
| Time | 4.2s |
```

### Step 5: Generate Comparison Report

For dual-model runs, create `dax-bench/runs/{timestamp}_comparison.md`:

```markdown
# Model Comparison Report
**Date**: 2024-12-13
**Models**: Claude Opus 4.5 vs DeepSeek V3.2
**Tasks**: All 30 tasks

## Summary

| Metric | Claude Opus 4.5 | DeepSeek V3.2 | Winner |
|--------|-----------------|---------------|--------|
| Tasks Solved | 30/30 (100%) | 30/30 (100%) | TIE |
| First-Try Success | 24/30 (80%) | 18/30 (60%) | Opus |
| Total Iterations | 42 | 67 | Opus |
| Avg Iterations | 1.4 | 2.2 | Opus |
| Total Input Tokens | 89,000 | 134,000 | Opus |
| Total Output Tokens | 36,000 | 52,000 | Opus |
| Total Cost | $2.45 | $0.18 | DeepSeek |
| Total Time | 4m 32s | 6m 18s | Opus |
| Cost per Solve | $0.082 | $0.006 | DeepSeek |

## Key Insight
Both models solve all 30 tasks successfully. Claude Opus 4.5 is **faster**
```

### Step 6: Update Lessons Learned (REQUIRED)

**After completing any benchmark run, you MUST update the lessons-learned file:**

```
Edit: .claude/skills/dax-bench-solver/lessons-learned.md
```

**Required updates:**

1. **Update "Last Updated" date** to today

2. **Add row to Model Performance Summary table:**
   ```markdown
   | {model_id} | {solved}/{total} ({%}) | {first_try}/{total} ({%}) | {avg_iters} | {notes} |
   ```

3. **For each task that required >1 iteration, add to Run History:**
   ```markdown
   **Multi-Iteration Fixes ({Model}):**
   | Task | Error | Fix |
   |------|-------|-----|
   | task-XXX | {what went wrong} | {what fixed it} |
   ```

4. **If a new pattern emerges, add to "Validated Learnings":**
   ```markdown
   ### {Pattern Name} (task-XXX)
   **Problem**: {what models get wrong}
   **Rule**: {the correct approach}
   **Feedback that works**: "{exact feedback text that fixed it}"
   ```

**This step is NOT optional.** Future runs depend on accumulated learnings.

---

## Appendix: DAX.guide Function Scraping

When user requests DAX function list update, follow this process:

### Step 1: Fetch the page
```
WebFetch(url: "https://dax.guide/functions/", prompt: "Extract all DAX function names from this page. Return them as a JSON array of uppercase strings.")
```

### Step 2: Parse and compare
```python
# Pseudocode for comparison
new_functions = set(fetched_functions)
existing_functions = set(dax_functions_reference["valid_functions"])
added = new_functions - existing_functions
removed = existing_functions - new_functions  # Usually empty, but flag if functions deprecated
```

### Step 3: Update the file
If new functions found:
```json
{
  "source": "https://dax.guide/functions/",
  "last_updated": "{today's date}",
  "last_check_note": "Added: {list of new functions}",
  "valid_functions": [... updated list ...]
}
```

### Step 4: Report to user
```
✅ DAX function list updated:
- Previous count: {old_count}
- New count: {new_count}
- Added functions: {list or "none"}
- Removed functions: {list or "none"}
- Last updated: {today}
```

### Known DAX.guide Structure
The functions page lists functions in alphabetical sections. Each function is a link.
Look for patterns like:
- Function names in `<a>` tags with href to `/functions/{name}/`
- All caps or title case function names
- Exclude navigation elements, headers

## Per-Task Breakdown

| Task | Complexity | Opus Iters | DeepSeek Iters |
|------|------------|------------|----------------|
| task-001 | basic | 1 | 1 |
| task-002 | basic | 1 | 1 |
| ... | ... | ... | ... |
| task-030 | advanced | 2 | 4 |
```

## OpenRouter API Integration

### API Call Structure

```javascript
POST https://openrouter.ai/api/v1/chat/completions
Headers:
  Authorization: Bearer {OPENROUTER_API_KEY}
  Content-Type: application/json
  HTTP-Referer: https://github.com/bigfootdax  // Optional
  X-Title: DAX Bench Solver  // Optional

Body:
{
  "model": "anthropic/claude-opus-4-5-20251101",
  "messages": [
    {"role": "system", "content": "{task.prompt.system}"},
    {"role": "user", "content": "{task.prompt.user}\n\nContext:\n{task.prompt.dataModelContext}"}
  ],
  "temperature": 0.2,
  "max_tokens": 2000
}
```

### Parsing Response

Extract DAX from response - models may include markdown formatting:
1. Look for code block: ```dax ... ``` or ``` ... ```
2. If no code block, look for pattern: `MeasureName = ...`
3. Strip any explanatory text before/after

## Validation Method: Power BI Execution (Required)

**Pattern matching has been removed.** All validation must go through Power BI execution.
This ensures functionally equivalent DAX (e.g., `LASTDATE` vs `MAX`) is correctly validated.

### Validation Workflow

For each generated DAX response:

**Step 1: Parse the measure**
```python
from benchmark_mcp import parse_measure_definition
measure_name, expression = parse_measure_definition(generated_dax)
```

**Step 2: Create the measure in Power BI**
```
manage_measure(
    operation: "create",
    table: "_Measures",
    name: "{task_id}_{measure_name}",
    expression: "{expression}"
)
```
- If creation fails → Syntax error → Generate feedback → Next iteration
- If creation succeeds → Syntax is valid → Continue

**Step 3: Execute the measure**
```
run_dax('EVALUATE ROW("Result", [{measure_name}])')
```
- If execution fails → Execution error → Generate feedback → Next iteration
- If execution succeeds → Measure works → Mark as SOLVED

**Step 4: Keep the measure**
Measures are kept in `_Measures` table for reference. No cleanup needed.

### Task Selection (v4)

Run specific tasks using the benchmark_mcp module or CLI:

```bash
# Specific tasks
python run_benchmark_v4.py model --tasks 1,2,3
python run_benchmark_v4.py model --tasks task-001,task-028
python run_benchmark_v4.py model --tasks 1-10

# By complexity
python run_benchmark_v4.py model --complexity basic
python run_benchmark_v4.py model --complexity advanced

# Combine filters
python run_benchmark_v4.py model --tasks 1-30 --complexity advanced

# Dry run (show what would run)
python run_benchmark_v4.py model --tasks 1-5 --dry-run
```

### Using benchmark_mcp.py from Claude Code

```python
# Load task
from benchmark_mcp import load_task, get_model_response, parse_measure_definition, generate_feedback, record_result

task = load_task("task-001")

# Get model's response
response = get_model_response(task, "google/gemini-2.5-pro")
dax = response["dax"]
measure_name, expression = parse_measure_definition(dax)

# Validate using MCP tools (Claude Code runs these)
# 1. Create measure
result = manage_measure(operation="create", table="_Measures", name=f"{task['id']}_{measure_name}", expression=expression)

# 2. If failed, generate feedback and retry
if not result["success"]:
    feedback = generate_feedback("syntax", result["error"], task, iteration=1)
    response = get_model_response(task, model, previous_attempts=[{"dax": dax, "feedback": feedback}])
    # ... continue iteration

# 3. If succeeded, execute to verify
exec_result = run_dax(f'EVALUATE ROW("Test", [{measure_name}])')

# 4. Record result
record_result(task, model, solved=True, iterations=[...], final_dax=dax)
```

## DAX Function Validation Rules

### CRITICAL: Only Use Valid DAX Functions

Before generating DAX, validate against the official function list from [DAX.guide](https://dax.guide/functions/).

**Common Invalid Functions (DO NOT USE):**

| Invalid Function | Language | Use Instead |
|-----------------|----------|-------------|
| `SUMIF` | Excel | `CALCULATE(SUM(col), filter)` |
| `SUMIFS` | Excel | `CALCULATE(SUM(col), filter1, filter2)` |
| `COUNTIF` | Excel | `CALCULATE(COUNTROWS(table), filter)` |
| `SUMPRODUCT` | Excel | `SUMX(table, expr1 * expr2)` |
| `VLOOKUP` | Excel | `LOOKUPVALUE(result, search_col, value)` |
| `DENSE_RANK` | SQL | `RANKX(table, expr, , DESC, DENSE)` |
| `ROW_NUMBER` | SQL | `RANKX(table, expr, , , SKIP)` |
| `SAMEPERIODLASTDAY` | **Invented** | `DATEADD('Date'[Date], -1, DAY)` |

### EARLIER is Deprecated - Use VAR Pattern

The `EARLIER()` function is **not recommended** per DAX.guide. Always use VAR to capture values before nested row context.

**BAD (deprecated):**
```dax
Category Rank =
RANKX(
    FILTER(Product, Product[Category] = EARLIER(Product[Category])),
    Product[Unit Price],
    , DESC, DENSE
)
```

**GOOD (modern pattern):**
```dax
Category Rank =
VAR CurrentCategory = Product[Category]
VAR CurrentPrice = Product[Unit Price]
RETURN
RANKX(
    FILTER(ALL(Product), Product[Category] = CurrentCategory),
    Product[Unit Price],
    , DESC, DENSE
)
```

### Creating Tables: Use Table Variables, Not New Tables

If you need to create intermediate tables for calculations, use **table variables** within the measure, not references to tables that don't exist in the model.

**BAD (references non-existent table):**
```dax
Top 5 Sales =
VAR IsInTop5 = CurrentProduct IN TopProducts  // TopProducts doesn't exist!
RETURN ...
```

**GOOD (create table as variable):**
```dax
Top 5 Sales =
VAR CurrentProduct = SELECTEDVALUE(Product[ProductKey])
VAR TopProducts =
    TOPN(
        5,
        ADDCOLUMNS(
            ALL(Product[ProductKey]),
            "@Sales", CALCULATE(SUM(Sales[Net Price]))
        ),
        [@Sales], DESC
    )
VAR IsInTop5 = CurrentProduct IN SELECTCOLUMNS(TopProducts, "Key", Product[ProductKey])
RETURN
    IF(IsInTop5, SUM(Sales[Net Price]), BLANK())
```

### Pre-Flight Validation

Before submitting DAX, the validator (`dax_function_validator.py`) checks:

1. **Function existence**: All functions must be in the official DAX.guide list
2. **Deprecated functions**: Warns about `EARLIER`/`EARLIEST` usage
3. **Excel/SQL functions**: Catches common mistakes from other languages
4. **Table references**: Ensures referenced tables exist in the model schema

Run validation:
```bash
cd dax-bench
python dax_function_validator.py
```

---

## Error Feedback Templates

When iteration fails, provide specific feedback:

### Syntax Error
```
Your DAX has a syntax error: {error_message}
Please fix the syntax and try again. Common issues:
- Missing parentheses
- Incorrect function name
- Invalid column reference
```

### Wrong Output
```
Your DAX executes but returns incorrect values.
Expected: {expected_value}
Got: {actual_value}
Please review your logic, especially: {hint_based_on_diff}
```

### Reference Error
```
Your DAX references a column or table that doesn't exist: {missing_ref}
Available tables: {table_list}
Available columns in {likely_table}: {column_list}
```

## Cost Calculation

```
cost = (input_tokens / 1_000_000 * model.inputCostPer1M) +
       (output_tokens / 1_000_000 * model.outputCostPer1M)
```

## Example Usage

### Single Model, Single Task
User: "Solve task-009 with Claude Opus"
→ Run solver for task-009 with claude-opus-4-5
→ Generate log file
→ Report: "Solved in 2 iterations, cost $0.047"

### Model Comparison, All Tasks
User: "Compare Opus vs DeepSeek on all tasks"
→ Run solver for all 30 tasks with both models
→ Generate individual logs + comparison report
→ Show summary table

### Quick Benchmark
User: "Run basic tasks with the top 3 models"
→ Run 6 basic tasks with Opus, GPT-5.2, Gemini 3
→ Generate comparison showing first-try rates
