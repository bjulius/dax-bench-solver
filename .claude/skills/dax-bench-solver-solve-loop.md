# MANDATORY AGENTIC SOLVE LOOP

**This file documents the REQUIRED iteration loop for DAX Bench Solver.**

## The Agentic Loop - MUST FOLLOW EVERY STEP

```
FOR each selected model:
  FOR each selected task:
    iteration = 0
    solved = false
    feedback_history = []

    WHILE iteration < MAX_ITERATIONS (10) AND NOT solved:
      iteration++

      ╔═══════════════════════════════════════════════════════════════╗
      ║ STEP 3.1: GENERATE DAX                                        ║
      ╚═══════════════════════════════════════════════════════════════╝
      Call OpenRouter API with:
        - model: exact ID from models_cache.json
        - messages: [system prompt, user prompt + LIVE schema]
        - If iteration > 1: append ALL previous feedback_history

      Parse DAX from response (extract from ```dax blocks)

      ╔═══════════════════════════════════════════════════════════════╗
      ║ STEP 3.2: FUNCTION VALIDATION (MANDATORY)                     ║
      ╚═══════════════════════════════════════════════════════════════╝
      Check against dax_functions_reference.json:
        - Extract all function names from generated DAX
        - Compare against valid_functions list
        - Flag invalid: Excel (SUMIF), SQL (DENSE_RANK), invented

      IF invalid functions found:
        feedback = "Invalid function(s): {list}. Use {alternatives}."
        feedback_history.append(feedback)
        CONTINUE → next iteration

      ╔═══════════════════════════════════════════════════════════════╗
      ║ STEP 3.3: SYNTAX VALIDATION (MANDATORY)                       ║
      ╚═══════════════════════════════════════════════════════════════╝
      Create measure in Power BI:
        mcp__powerbi-desktop__manage_measure(
          operation: "create", table: "_Measures",
          name: "{task_id}_iter{iteration}", expression: "{dax}"
        )

      IF creation fails:
        feedback = "Syntax error: {error_message}"
        feedback_history.append(feedback)
        CONTINUE → next iteration

      ╔═══════════════════════════════════════════════════════════════╗
      ║ STEP 3.4: VALUE VALIDATION (MANDATORY)                        ║
      ╚═══════════════════════════════════════════════════════════════╝
      Execute and compare:
        result = run_dax('EVALUATE ROW("Result", [measure])')
        Compare to expected_value with tolerance

      IF value mismatch:
        feedback = "Wrong result. Expected: {expected}, Got: {actual}."
        feedback_history.append(feedback)
        CONTINUE → next iteration

      ╔═══════════════════════════════════════════════════════════════╗
      ║ STEP 3.5: SUCCESS                                             ║
      ╚═══════════════════════════════════════════════════════════════╝
      solved = true

    END WHILE

    Record: {task, model, solved, iterations_needed}
```

## ⛔ CRITICAL RULES

1. **ALWAYS function validate** - Don't let invalid functions reach Power BI
2. **ALWAYS syntax validate** - Create measure to test compilation
3. **ALWAYS value validate** - Execute and compare to expected
4. **ALWAYS provide feedback** - Every failure gets specific feedback
5. **ALWAYS allow 10 iterations** - Models can learn and improve
6. **NEVER skip iterations** - Single-shot is NOT valid

**Success metric: "Solved within 10 iterations"**
