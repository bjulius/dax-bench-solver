# DAX Bench Full Benchmark Report

## Run Information
| Field | Value |
|-------|-------|
| **Model** | google/gemini-2.5-flash-lite |
| **Timestamp** | 2025-12-13T21:39:37Z |
| **Tasks Run** | 30 |
| **Max Iterations** | 10 |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | 16/30 (53.3%) |
| **First-Try Success** | 10/30 (33.3%) |
| **Total Iterations** | 164 |
| **Avg Iterations/Task** | 5.47 |
| **Total Input Tokens** | 177,821 |
| **Total Output Tokens** | 11,938 |
| **Total Tokens** | 189,759 |
| **Total Cost** | $0.0204 |
| **Cost per Task** | $0.000680 |
| **Total Time** | 176.4s (2.9m) |
| **Avg Time/Task** | 5.88s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
| Basic | 6/6 | 6/6 | 1.00 |
| Intermediate | 6/13 | 3/13 | 6.08 |
| Advanced | 4/11 | 1/11 | 7.18 |

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
| task-007 | intermediate | time-intelligence | ✅ | 2 | $0.0000 |
| task-008 | intermediate | filtering | ✅ | 1 | $0.0000 |
| task-011 | intermediate | table-manipulation | ❌ | 10 | $0.0009 |
| task-012 | intermediate | table-manipulation | ✅ | 2 | $0.0001 |
| task-015 | intermediate | context-transition | ❌ | 10 | $0.0012 |
| task-017 | intermediate | context-transition | ❌ | 10 | $0.0013 |
| task-019 | intermediate | filtering | ✅ | 2 | $0.0001 |
| task-022 | intermediate | iterator | ❌ | 10 | $0.0009 |
| task-023 | intermediate | table-manipulation | ❌ | 10 | $0.0020 |
| task-026 | intermediate | calculation | ❌ | 10 | $0.0018 |
| task-027 | intermediate | time-intelligence | ❌ | 10 | $0.0014 |
| task-029 | intermediate | time-intelligence | ✅ | 1 | $0.0000 |
| task-009 | advanced | calculation | ❌ | 10 | $0.0015 |
| task-010 | advanced | iterator | ❌ | 10 | $0.0013 |
| task-013 | advanced | table-manipulation | ❌ | 10 | $0.0020 |
| task-014 | advanced | table-manipulation | ✅ | 3 | $0.0001 |
| task-016 | advanced | context-transition | ❌ | 10 | $0.0016 |
| task-018 | advanced | context-transition | ✅ | 3 | $0.0001 |
| task-020 | advanced | filtering | ❌ | 10 | $0.0014 |
| task-021 | advanced | filtering | ✅ | 2 | $0.0001 |
| task-024 | advanced | iterator | ✅ | 1 | $0.0000 |
| task-028 | advanced | time-intelligence | ❌ | 10 | $0.0013 |
| task-030 | advanced | time-intelligence | ❌ | 10 | $0.0012 |

---

## Failed Tasks (if any)

- **task-011**: Sales Summary by Category (intermediate)
- **task-015**: Product Percentage of Category Total (intermediate)
- **task-017**: Granularity-Aware Measure with VALUES (intermediate)
- **task-022**: Product Ranking with RANKX (intermediate)
- **task-023**: Top 5 Products with TOPN (intermediate)
- **task-026**: Safe Ratio with Cascading Fallbacks (intermediate)
- **task-027**: Safe Year-over-Year with Missing Data (intermediate)
- **task-009**: Year-over-Year Growth Percentage (advanced)
- **task-010**: Running Total with CALCULATE and FILTER (advanced)
- **task-013**: Union of High-Value Transactions (advanced)
- **task-016**: Virtual Relationship with TREATAS (advanced)
- **task-020**: Percentage of Total with ALLEXCEPT (advanced)
- **task-028**: 3-Month Rolling Average (advanced)
- **task-030**: Fiscal Year-to-Date (July Start) (advanced)
