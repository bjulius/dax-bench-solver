# DAX Bench Full Benchmark Report

## Run Information
| Field | Value |
|-------|-------|
| **Model** | openai/gpt-5.2 |
| **Timestamp** | 2025-12-13T14:20:55Z |
| **Tasks Run** | 30 |
| **Max Iterations** | 10 |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | 27/30 (90.0%) |
| **First-Try Success** | 3/30 (10.0%) |
| **Total Iterations** | 95 |
| **Avg Iterations/Task** | 3.17 |
| **Total Input Tokens** | 52,072 |
| **Total Output Tokens** | 15,013 |
| **Total Tokens** | 67,085 |
| **Total Cost** | $0.2852 |
| **Cost per Task** | $0.009506 |
| **Total Time** | 356.1s (5.9m) |
| **Avg Time/Task** | 11.87s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
| Basic | 6/6 | 3/6 | 1.50 |
| Intermediate | 11/13 | 0/13 | 3.62 |
| Advanced | 10/11 | 0/11 | 3.55 |

---

## Per-Task Results

| Task | Complexity | Category | Solved | Iters | Cost |
|------|------------|----------|--------|-------|------|
| task-001 | basic | aggregation | ✅ | 1 | $0.0004 |
| task-002 | basic | aggregation | ✅ | 2 | $0.0008 |
| task-003 | basic | aggregation | ✅ | 2 | $0.0011 |
| task-004 | basic | aggregation | ✅ | 2 | $0.0010 |
| task-005 | basic | aggregation | ✅ | 1 | $0.0004 |
| task-025 | basic | calculation | ✅ | 1 | $0.0005 |
| task-006 | intermediate | time-intelligence | ✅ | 2 | $0.0013 |
| task-007 | intermediate | time-intelligence | ✅ | 2 | $0.0014 |
| task-008 | intermediate | filtering | ✅ | 2 | $0.0015 |
| task-011 | intermediate | table-manipulation | ✅ | 3 | $0.0037 |
| task-012 | intermediate | table-manipulation | ✅ | 2 | $0.0018 |
| task-015 | intermediate | context-transition | ❌ | 10 | $0.0469 |
| task-017 | intermediate | context-transition | ✅ | 3 | $0.0076 |
| task-019 | intermediate | filtering | ✅ | 2 | $0.0019 |
| task-022 | intermediate | iterator | ✅ | 3 | $0.0061 |
| task-023 | intermediate | table-manipulation | ✅ | 3 | $0.0185 |
| task-026 | intermediate | calculation | ❌ | 10 | $0.0512 |
| task-027 | intermediate | time-intelligence | ✅ | 3 | $0.0133 |
| task-029 | intermediate | time-intelligence | ✅ | 2 | $0.0017 |
| task-009 | advanced | calculation | ❌ | 10 | $0.0385 |
| task-010 | advanced | iterator | ✅ | 3 | $0.0046 |
| task-013 | advanced | table-manipulation | ✅ | 2 | $0.0040 |
| task-014 | advanced | table-manipulation | ✅ | 4 | $0.0035 |
| task-016 | advanced | context-transition | ✅ | 3 | $0.0078 |
| task-018 | advanced | context-transition | ✅ | 4 | $0.0169 |
| task-020 | advanced | filtering | ✅ | 3 | $0.0060 |
| task-021 | advanced | filtering | ✅ | 4 | $0.0271 |
| task-024 | advanced | iterator | ✅ | 2 | $0.0062 |
| task-028 | advanced | time-intelligence | ✅ | 2 | $0.0068 |
| task-030 | advanced | time-intelligence | ✅ | 2 | $0.0027 |

---

## Failed Tasks (if any)

- **task-015**: Product Percentage of Category Total (intermediate)
- **task-026**: Safe Ratio with Cascading Fallbacks (intermediate)
- **task-009**: Year-over-Year Growth Percentage (advanced)
