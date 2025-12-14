# DAX Bench Model Comparison Report

## Run Information
| Field | Value |
|-------|-------|
| **Date** | {date} |
| **Model A** | {model_a_name} ({model_a_tier}) |
| **Model B** | {model_b_name} ({model_b_tier}) |
| **Tasks Run** | {task_count} tasks |
| **Max Iterations** | {max_iterations} |

---

## Executive Summary

{summary_paragraph}

---

## Head-to-Head Comparison

| Metric | {model_a_name} | {model_b_name} | Winner |
|--------|----------------|----------------|--------|
| **Tasks Solved** | {a_solved}/{task_count} ({a_solved_pct}%) | {b_solved}/{task_count} ({b_solved_pct}%) | {solved_winner} |
| **First-Try Success** | {a_first_try}/{task_count} ({a_first_pct}%) | {b_first_try}/{task_count} ({b_first_pct}%) | {first_try_winner} |
| **Total Iterations** | {a_total_iters} | {b_total_iters} | {iter_winner} |
| **Avg Iterations/Task** | {a_avg_iters} | {b_avg_iters} | {avg_iter_winner} |
| **Total Input Tokens** | {a_input_tokens:,} | {b_input_tokens:,} | {input_winner} |
| **Total Output Tokens** | {a_output_tokens:,} | {b_output_tokens:,} | {output_winner} |
| **Total Cost** | ${a_total_cost} | ${b_total_cost} | {cost_winner} |
| **Total Time** | {a_total_time} | {b_total_time} | {time_winner} |
| **Cost per Solve** | ${a_cost_per_solve} | ${b_cost_per_solve} | {cost_solve_winner} |
| **Time per Solve** | {a_time_per_solve} | {b_time_per_solve} | {time_solve_winner} |

---

## Key Insights

### Reliability
{reliability_insight}

### Efficiency
{efficiency_insight}

### Cost-Effectiveness
{cost_insight}

### Recommendation
{recommendation}

---

## Per-Task Breakdown

| Task | Complexity | Category | {model_a_name} | {model_b_name} |
|------|------------|----------|----------------|----------------|
| task-001 | basic | aggregation | ✅ 1 iter | ✅ 1 iter |
| task-002 | basic | aggregation | ✅ 1 iter | ✅ 1 iter |
| task-003 | basic | aggregation | ✅ 1 iter | ✅ 2 iters |
| ... | ... | ... | ... | ... |

### Tasks Where Models Differed

{diff_analysis}

---

## Detailed Run Logs

Individual run logs for each task:

### Model A: {model_a_name}
{model_a_log_links}

### Model B: {model_b_name}
{model_b_log_links}

---

## Methodology

- **Validation**: DAX measures validated against expected outputs from DAX Bench
- **Iteration Feedback**: On failure, specific error messages fed back to model
- **Timeout**: {timeout_ms}ms per API call
- **Temperature**: 0.2 (low for consistency)
- **Max Iterations**: {max_iterations} before marking as unsolved

---

## Raw Data

<details>
<summary>Click to expand JSON results</summary>

```json
{raw_json_results}
```

</details>
