# DAX Bench Full Benchmark Report

## Run Information
| Field | Value |
|-------|-------|
| **Model** | google/gemini-2.5-flash |
| **Timestamp** | 2025-12-13T15:58:12Z |
| **Tasks Run** | 30 |
| **Max Iterations** | 10 |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | 21/30 (70.0%) |
| **First-Try Success** | 7/30 (23.3%) |
| **Total Iterations** | 128 |
| **Avg Iterations/Task** | 4.27 |
| **Total Input Tokens** | 117,468 |
| **Total Output Tokens** | 8,745 |
| **Total Tokens** | 126,213 |
| **Total Cost** | $0.0539 |
| **Cost per Task** | $0.001797 |
| **Total Time** | 127.9s (2.1m) |
| **Avg Time/Task** | 4.26s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
| Basic | 6/6 | 5/6 | 1.17 |
| Intermediate | 9/13 | 2/13 | 4.54 |
| Advanced | 6/11 | 0/11 | 5.64 |

---

## Per-Task Results

| Task | Complexity | Category | Solved | Iters | Cost |
|------|------------|----------|--------|-------|------|
| task-001 | basic | aggregation | ✅ | 1 | $0.0001 |
| task-002 | basic | aggregation | ✅ | 2 | $0.0001 |
| task-003 | basic | aggregation | ✅ | 1 | $0.0001 |
| task-004 | basic | aggregation | ✅ | 1 | $0.0001 |
| task-005 | basic | aggregation | ✅ | 1 | $0.0001 |
| task-025 | basic | calculation | ✅ | 1 | $0.0001 |
| task-006 | intermediate | time-intelligence | ✅ | 2 | $0.0002 |
| task-007 | intermediate | time-intelligence | ✅ | 2 | $0.0002 |
| task-008 | intermediate | filtering | ✅ | 2 | $0.0002 |
| task-011 | intermediate | table-manipulation | ✅ | 2 | $0.0003 |
| task-012 | intermediate | table-manipulation | ✅ | 3 | $0.0005 |
| task-015 | intermediate | context-transition | ❌ | 10 | $0.0048 |
| task-017 | intermediate | context-transition | ❌ | 10 | $0.0069 |
| task-019 | intermediate | filtering | ✅ | 3 | $0.0006 |
| task-022 | intermediate | iterator | ✅ | 1 | $0.0001 |
| task-023 | intermediate | table-manipulation | ❌ | 10 | $0.0075 |
| task-026 | intermediate | calculation | ❌ | 10 | $0.0063 |
| task-027 | intermediate | time-intelligence | ✅ | 3 | $0.0012 |
| task-029 | intermediate | time-intelligence | ✅ | 1 | $0.0001 |
| task-009 | advanced | calculation | ❌ | 10 | $0.0058 |
| task-010 | advanced | iterator | ✅ | 2 | $0.0004 |
| task-013 | advanced | table-manipulation | ✅ | 2 | $0.0008 |
| task-014 | advanced | table-manipulation | ❌ | 10 | $0.0025 |
| task-016 | advanced | context-transition | ✅ | 2 | $0.0004 |
| task-018 | advanced | context-transition | ❌ | 10 | $0.0041 |
| task-020 | advanced | filtering | ❌ | 10 | $0.0051 |
| task-021 | advanced | filtering | ❌ | 10 | $0.0043 |
| task-024 | advanced | iterator | ✅ | 2 | $0.0002 |
| task-028 | advanced | time-intelligence | ✅ | 2 | $0.0006 |
| task-030 | advanced | time-intelligence | ✅ | 2 | $0.0004 |

---

## Failed Tasks (if any)

- **task-015**: Product Percentage of Category Total (intermediate)
- **task-017**: Granularity-Aware Measure with VALUES (intermediate)
- **task-023**: Top 5 Products with TOPN (intermediate)
- **task-026**: Safe Ratio with Cascading Fallbacks (intermediate)
- **task-009**: Year-over-Year Growth Percentage (advanced)
- **task-014**: Year-Category Analysis Matrix (advanced)
- **task-018**: Running Count with EARLIER (advanced)
- **task-020**: Percentage of Total with ALLEXCEPT (advanced)
- **task-021**: Filter Intersection with KEEPFILTERS (advanced)
