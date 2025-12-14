# DAX Bench Full Benchmark Report

## Run Information
| Field | Value |
|-------|-------|
| **Model** | mistralai/mistral-small-3.1-24b-instruct |
| **Timestamp** | 2025-12-13T16:43:00Z |
| **Tasks Run** | 30 |
| **Max Iterations** | 10 |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | 26/30 (86.7%) |
| **First-Try Success** | 8/30 (26.7%) |
| **Total Iterations** | 95 |
| **Avg Iterations/Task** | 3.17 |
| **Total Input Tokens** | 62,389 |
| **Total Output Tokens** | 5,180 |
| **Total Tokens** | 67,569 |
| **Total Cost** | $0.0025 |
| **Cost per Task** | $0.000083 |
| **Total Time** | 471.3s (7.9m) |
| **Avg Time/Task** | 15.71s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
| Basic | 6/6 | 6/6 | 1.00 |
| Intermediate | 11/13 | 2/13 | 3.15 |
| Advanced | 9/11 | 0/11 | 4.36 |

---

## Per-Task Results

| Task | Complexity | Category | Solved | Iters | Cost |
|------|------------|----------|--------|-------|------|
| task-001 | basic | aggregation | ✅ | 1 | $0.0000 |
| task-002 | basic | aggregation | ✅ | 1 | $0.0000 |
| task-003 | basic | aggregation | ✅ | 1 | $0.0000 |
| task-004 | basic | aggregation | ✅ | 1 | $0.0000 |
| task-005 | basic | aggregation | ✅ | 1 | $0.0000 |
| task-025 | basic | calculation | ✅ | 1 | $0.0000 |
| task-006 | intermediate | time-intelligence | ✅ | 1 | $0.0000 |
| task-007 | intermediate | time-intelligence | ✅ | 1 | $0.0000 |
| task-008 | intermediate | filtering | ✅ | 2 | $0.0000 |
| task-011 | intermediate | table-manipulation | ✅ | 2 | $0.0000 |
| task-012 | intermediate | table-manipulation | ✅ | 2 | $0.0001 |
| task-015 | intermediate | context-transition | ❌ | 10 | $0.0004 |
| task-017 | intermediate | context-transition | ✅ | 2 | $0.0000 |
| task-019 | intermediate | filtering | ✅ | 2 | $0.0000 |
| task-022 | intermediate | iterator | ✅ | 2 | $0.0000 |
| task-023 | intermediate | table-manipulation | ✅ | 3 | $0.0001 |
| task-026 | intermediate | calculation | ❌ | 10 | $0.0005 |
| task-027 | intermediate | time-intelligence | ✅ | 2 | $0.0000 |
| task-029 | intermediate | time-intelligence | ✅ | 2 | $0.0000 |
| task-009 | advanced | calculation | ❌ | 10 | $0.0004 |
| task-010 | advanced | iterator | ✅ | 8 | $0.0002 |
| task-013 | advanced | table-manipulation | ✅ | 3 | $0.0001 |
| task-014 | advanced | table-manipulation | ✅ | 3 | $0.0000 |
| task-016 | advanced | context-transition | ✅ | 2 | $0.0000 |
| task-018 | advanced | context-transition | ✅ | 2 | $0.0000 |
| task-020 | advanced | filtering | ✅ | 4 | $0.0001 |
| task-021 | advanced | filtering | ✅ | 2 | $0.0000 |
| task-024 | advanced | iterator | ✅ | 2 | $0.0000 |
| task-028 | advanced | time-intelligence | ❌ | 10 | $0.0004 |
| task-030 | advanced | time-intelligence | ✅ | 2 | $0.0000 |

---

## Failed Tasks (if any)

- **task-015**: Product Percentage of Category Total (intermediate)
- **task-026**: Safe Ratio with Cascading Fallbacks (intermediate)
- **task-009**: Year-over-Year Growth Percentage (advanced)
- **task-028**: 3-Month Rolling Average (advanced)
