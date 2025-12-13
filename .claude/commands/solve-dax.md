# DAX Bench Solver Command

Solve DAX Bench tasks with iterative validation using OpenRouter models.

## Arguments
- `$ARGUMENTS` - Can be:
  - Task ID: `task-001` or `001`
  - Complexity level: `basic`, `intermediate`, `advanced`, `all`
  - Model comparison: `compare opus deepseek`

## Instructions

You are running the DAX Bench Solver. Use the skill defined in `.claude/skills/dax-bench-solver.md`.

### Parse Arguments: $ARGUMENTS

1. If arguments contain a task ID (e.g., `task-001` or just `001`):
   - Load that specific task from `dax-bench/tasks/`

2. If arguments contain a complexity level (`basic`, `intermediate`, `advanced`, `all`):
   - Load all tasks of that level

3. If arguments contain `compare {model1} {model2}`:
   - Run comparison mode with both models

4. If arguments contain a model name (opus, gpt, gemini, deepseek, etc.):
   - Use that model (map to full ID from models.json)

5. If no arguments, ask user what they want to run.

### Default Behavior

If only a task is specified without a model:
- Ask user which model(s) to use
- Show available models with their tiers and DAX Bench scores

### Execution Flow

1. **Verify Prerequisites**:
   - Check if OPENROUTER_API_KEY is available
   - Verify Power BI MCP connection
   - Confirm Contoso.pbix is the active model

2. **Load Task(s)**:
   - Read task JSON(s)
   - Display task title and complexity

3. **Run Solver Loop**:
   - For each model, for each task
   - Track iterations, tokens, time
   - Log each attempt to markdown

4. **Report Results**:
   - Show summary table
   - Link to detailed logs
   - If comparison: show winner analysis

### Example Invocations

```
/solve-dax task-001
/solve-dax basic
/solve-dax task-009 opus
/solve-dax compare opus deepseek task-009
/solve-dax all compare opus gemini
```
