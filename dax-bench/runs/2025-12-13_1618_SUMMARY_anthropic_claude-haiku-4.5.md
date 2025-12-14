# DAX Bench Full Benchmark Report

## Run Information
| Field | Value |
|-------|-------|
| **Model** | anthropic/claude-haiku-4.5 |
| **Timestamp** | 2025-12-13T16:18:50Z |
| **Tasks Run** | 30 |
| **Max Iterations** | 10 |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | 28/30 (93.3%) |
| **First-Try Success** | 6/30 (20.0%) |
| **Total Iterations** | 82 |
| **Avg Iterations/Task** | 2.73 |
| **Total Input Tokens** | 49,414 |
| **Total Output Tokens** | 5,568 |
| **Total Tokens** | 54,982 |
| **Total Cost** | $0.0773 |
| **Cost per Task** | $0.002575 |
| **Total Time** | 156.0s (2.6m) |
| **Avg Time/Task** | 5.20s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
| Basic | 6/6 | 4/6 | 1.33 |
| Intermediate | 12/13 | 2/13 | 2.85 |
| Advanced | 10/11 | 0/11 | 3.36 |

---

## Per-Task Results

| Task | Complexity | Category | Solved | Iters | Cost |
|------|------------|----------|--------|-------|------|
| task-001 | basic | aggregation | ✅ | 1 | $0.0002 |
| task-002 | basic | aggregation | ✅ | 2 | $0.0004 |
| task-003 | basic | aggregation | ✅ | 1 | $0.0002 |
| task-004 | basic | aggregation | ✅ | 1 | $0.0002 |
| task-005 | basic | aggregation | ✅ | 1 | $0.0002 |
| task-025 | basic | calculation | ✅ | 2 | $0.0006 |
| task-006 | intermediate | time-intelligence | ✅ | 1 | $0.0003 |
| task-007 | intermediate | time-intelligence | ✅ | 2 | $0.0007 |
| task-008 | intermediate | filtering | ✅ | 2 | $0.0006 |
| task-011 | intermediate | table-manipulation | ✅ | 2 | $0.0008 |
| task-012 | intermediate | table-manipulation | ✅ | 1 | $0.0003 |
| task-015 | intermediate | context-transition | ✅ | 2 | $0.0015 |
| task-017 | intermediate | context-transition | ✅ | 2 | $0.0015 |
| task-019 | intermediate | filtering | ✅ | 3 | $0.0014 |
| task-022 | intermediate | iterator | ✅ | 3 | $0.0016 |
| task-023 | intermediate | table-manipulation | ✅ | 4 | $0.0055 |
| task-026 | intermediate | calculation | ❌ | 10 | $0.0200 |
| task-027 | intermediate | time-intelligence | ✅ | 3 | $0.0037 |
| task-029 | intermediate | time-intelligence | ✅ | 2 | $0.0008 |
| task-009 | advanced | calculation | ❌ | 10 | $0.0178 |
| task-010 | advanced | iterator | ✅ | 2 | $0.0013 |
| task-013 | advanced | table-manipulation | ✅ | 2 | $0.0012 |
| task-014 | advanced | table-manipulation | ✅ | 4 | $0.0018 |
| task-016 | advanced | context-transition | ✅ | 3 | $0.0026 |
| task-018 | advanced | context-transition | ✅ | 3 | $0.0019 |
| task-020 | advanced | filtering | ✅ | 3 | $0.0022 |
| task-021 | advanced | filtering | ✅ | 2 | $0.0011 |
| task-024 | advanced | iterator | ✅ | 2 | $0.0006 |
| task-028 | advanced | time-intelligence | ✅ | 3 | $0.0037 |
| task-030 | advanced | time-intelligence | ✅ | 3 | $0.0027 |

---

## Failed Tasks (if any)

- **task-026**: Safe Ratio with Cascading Fallbacks (intermediate)
- **task-009**: Year-over-Year Growth Percentage (advanced)
