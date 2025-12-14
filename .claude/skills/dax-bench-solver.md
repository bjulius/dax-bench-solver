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

1. **OpenRouter API Key**: Set as environment variable `OPENROUTER_API_KEY`
2. **Power BI Desktop**: Open with `Contoso.pbix` from `dax-bench/` folder
3. **Power BI MCP Server**: Connected to the Contoso model

## File Locations

- **Tasks**: `dax-bench/tasks/{basic,intermediate,advanced}/task-XXX.json`
- **Model Config**: `.claude/skills/dax-bench-solver/models.json`
- **Run Logs**: `dax-bench/runs/` (created per run)
- **Contoso Model**: `dax-bench/Contoso.pbix`

## Workflow

### Step 1: Select Task(s)

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
and requires **fewer iterations**, but DeepSeek V3.2 is **13x cheaper**.

For production use where cost matters: DeepSeek
For time-critical or complex tasks: Opus

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

## Validation Methods

### Method 1: Pattern Matching (All Tasks)

Compare generated DAX against:
- `expectedOutput.dax` (primary)
- `expectedOutput.alternativeCorrect` (alternatives)

Normalize before comparison:
- Remove extra whitespace
- Standardize quotes (`'Table'` vs `Table`)
- Ignore case for keywords

### Method 2: Execution Validation (Tasks with expectedResult)

For tasks that include `expectedOutput.expectedResult`:

1. Create measure in Power BI via MCP:
```
manage_measure(operation: "create", table: "_Measures", name: "Test_Measure", expression: "{generated_dax}")
```

2. Execute test query:
```
run_dax("EVALUATE SUMMARIZECOLUMNS(...)")
```

3. Compare results to `expectedResult.rows`

4. Clean up:
```
manage_measure(operation: "delete", table: "_Measures", name: "Test_Measure")
```

### Method 3: Syntax-Only Validation

If execution not possible, at minimum:
1. Attempt to create measure
2. If creation fails, capture error message
3. Use error for iteration feedback

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
