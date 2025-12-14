# DAX Bench Full Benchmark Report

## Run Information
| Field | Value |
|-------|-------|
| **Model** | google/gemini-3-pro-preview |
| **Timestamp** | 2025-12-13T15:07:58Z |
| **Tasks Run** | 30 |
| **Max Iterations** | 10 |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | 26/30 (86.7%) |
| **First-Try Success** | 3/30 (10.0%) |
| **Total Iterations** | 104 |
| **Avg Iterations/Task** | 3.47 |
| **Total Input Tokens** | 42,788 |
| **Total Output Tokens** | 79,884 |
| **Total Tokens** | 122,672 |
| **Total Cost** | $1.0442 |
| **Cost per Task** | $0.034806 |
| **Total Time** | 1093.8s (18.2m) |
| **Avg Time/Task** | 36.46s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
| Basic | 6/6 | 1/6 | 1.83 |
| Intermediate | 11/13 | 1/13 | 3.92 |
| Advanced | 9/11 | 1/11 | 3.82 |

---

## Per-Task Results

| Task | Complexity | Category | Solved | Iters | Cost |
|------|------------|----------|--------|-------|------|
| task-001 | basic | aggregation | ✅ | 2 | $0.0072 |
| task-002 | basic | aggregation | ✅ | 2 | $0.0065 |
| task-003 | basic | aggregation | ✅ | 2 | $0.0063 |
| task-004 | basic | aggregation | ✅ | 2 | $0.0061 |
| task-005 | basic | aggregation | ✅ | 2 | $0.0060 |
| task-025 | basic | calculation | ✅ | 1 | $0.0094 |
| task-006 | intermediate | time-intelligence | ✅ | 2 | $0.0114 |
| task-007 | intermediate | time-intelligence | ✅ | 2 | $0.0100 |
| task-008 | intermediate | filtering | ✅ | 2 | $0.0129 |
| task-011 | intermediate | table-manipulation | ✅ | 3 | $0.0325 |
| task-012 | intermediate | table-manipulation | ✅ | 2 | $0.0125 |
| task-015 | intermediate | context-transition | ❌ | 10 | $0.1245 |
| task-017 | intermediate | context-transition | ✅ | 4 | $0.0482 |
| task-019 | intermediate | filtering | ✅ | 1 | $0.0103 |
| task-022 | intermediate | iterator | ✅ | 3 | $0.0275 |
| task-023 | intermediate | table-manipulation | ✅ | 7 | $0.0900 |
| task-026 | intermediate | calculation | ❌ | 10 | $0.1217 |
| task-027 | intermediate | time-intelligence | ✅ | 2 | $0.0235 |
| task-029 | intermediate | time-intelligence | ✅ | 3 | $0.0270 |
| task-009 | advanced | calculation | ❌ | 10 | $0.1239 |
| task-010 | advanced | iterator | ✅ | 3 | $0.0294 |
| task-013 | advanced | table-manipulation | ✅ | 2 | $0.0217 |
| task-014 | advanced | table-manipulation | ✅ | 3 | $0.0183 |
| task-016 | advanced | context-transition | ✅ | 1 | $0.0089 |
| task-018 | advanced | context-transition | ✅ | 3 | $0.0299 |
| task-020 | advanced | filtering | ❌ | 10 | $0.1274 |
| task-021 | advanced | filtering | ✅ | 2 | $0.0119 |
| task-024 | advanced | iterator | ✅ | 2 | $0.0208 |
| task-028 | advanced | time-intelligence | ✅ | 2 | $0.0204 |
| task-030 | advanced | time-intelligence | ✅ | 4 | $0.0381 |

---

## Failed Tasks (if any)

- **task-015**: Product Percentage of Category Total (intermediate)
- **task-026**: Safe Ratio with Cascading Fallbacks (intermediate)
- **task-009**: Year-over-Year Growth Percentage (advanced)
- **task-020**: Percentage of Total with ALLEXCEPT (advanced)
