# DAX Bench Full Benchmark Report

## Run Information
| Field | Value |
|-------|-------|
| **Model** | anthropic/claude-3.5-haiku |
| **Timestamp** | 2025-12-13T16:14:20Z |
| **Tasks Run** | 30 |
| **Max Iterations** | 10 |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | 27/30 (90.0%) |
| **First-Try Success** | 7/30 (23.3%) |
| **Total Iterations** | 91 |
| **Avg Iterations/Task** | 3.03 |
| **Total Input Tokens** | 66,577 |
| **Total Output Tokens** | 6,057 |
| **Total Tokens** | 72,634 |
| **Total Cost** | $0.0775 |
| **Cost per Task** | $0.002583 |
| **Total Time** | 204.6s (3.4m) |
| **Avg Time/Task** | 6.82s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
| Basic | 6/6 | 5/6 | 1.17 |
| Intermediate | 11/13 | 2/13 | 3.15 |
| Advanced | 10/11 | 0/11 | 3.91 |

---

## Per-Task Results

| Task | Complexity | Category | Solved | Iters | Cost |
|------|------------|----------|--------|-------|------|
| task-001 | basic | aggregation | ✅ | 1 | $0.0002 |
| task-002 | basic | aggregation | ✅ | 1 | $0.0001 |
| task-003 | basic | aggregation | ✅ | 1 | $0.0002 |
| task-004 | basic | aggregation | ✅ | 1 | $0.0002 |
| task-005 | basic | aggregation | ✅ | 1 | $0.0002 |
| task-025 | basic | calculation | ✅ | 2 | $0.0006 |
| task-006 | intermediate | time-intelligence | ✅ | 1 | $0.0002 |
| task-007 | intermediate | time-intelligence | ✅ | 1 | $0.0002 |
| task-008 | intermediate | filtering | ✅ | 2 | $0.0005 |
| task-011 | intermediate | table-manipulation | ✅ | 2 | $0.0007 |
| task-012 | intermediate | table-manipulation | ✅ | 2 | $0.0007 |
| task-015 | intermediate | context-transition | ❌ | 10 | $0.0126 |
| task-017 | intermediate | context-transition | ✅ | 2 | $0.0011 |
| task-019 | intermediate | filtering | ✅ | 2 | $0.0007 |
| task-022 | intermediate | iterator | ✅ | 2 | $0.0006 |
| task-023 | intermediate | table-manipulation | ✅ | 3 | $0.0024 |
| task-026 | intermediate | calculation | ❌ | 10 | $0.0156 |
| task-027 | intermediate | time-intelligence | ✅ | 2 | $0.0018 |
| task-029 | intermediate | time-intelligence | ✅ | 2 | $0.0007 |
| task-009 | advanced | calculation | ❌ | 10 | $0.0140 |
| task-010 | advanced | iterator | ✅ | 3 | $0.0015 |
| task-013 | advanced | table-manipulation | ✅ | 3 | $0.0020 |
| task-014 | advanced | table-manipulation | ✅ | 2 | $0.0006 |
| task-016 | advanced | context-transition | ✅ | 4 | $0.0027 |
| task-018 | advanced | context-transition | ✅ | 2 | $0.0007 |
| task-020 | advanced | filtering | ✅ | 9 | $0.0125 |
| task-021 | advanced | filtering | ✅ | 3 | $0.0011 |
| task-024 | advanced | iterator | ✅ | 2 | $0.0005 |
| task-028 | advanced | time-intelligence | ✅ | 2 | $0.0013 |
| task-030 | advanced | time-intelligence | ✅ | 3 | $0.0014 |

---

## Failed Tasks (if any)

- **task-015**: Product Percentage of Category Total (intermediate)
- **task-026**: Safe Ratio with Cascading Fallbacks (intermediate)
- **task-009**: Year-over-Year Growth Percentage (advanced)
