# DAX Bench Full Benchmark Report

## Run Information
| Field | Value |
|-------|-------|
| **Model** | qwen/qwen3-235b-a22b:free |
| **Timestamp** | 2025-12-13T16:42:19Z |
| **Tasks Run** | 30 |
| **Max Iterations** | 10 |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | 4/30 (13.3%) |
| **First-Try Success** | 2/30 (6.7%) |
| **Total Iterations** | 278 |
| **Avg Iterations/Task** | 9.27 |
| **Total Input Tokens** | 5,325 |
| **Total Output Tokens** | 8,642 |
| **Total Tokens** | 13,967 |
| **Total Cost** | $0.0000 |
| **Cost per Task** | $0.000000 |
| **Total Time** | 501.2s (8.4m) |
| **Avg Time/Task** | 16.71s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
| Basic | 2/6 | 1/6 | 8.17 |
| Intermediate | 2/13 | 1/13 | 9.15 |
| Advanced | 0/11 | 0/11 | 10.00 |

---

## Per-Task Results

| Task | Complexity | Category | Solved | Iters | Cost |
|------|------------|----------|--------|-------|------|
| task-001 | basic | aggregation | ✅ | 1 | $0.0000 |
| task-002 | basic | aggregation | ❌ | 10 | $0.0000 |
| task-003 | basic | aggregation | ❌ | 10 | $0.0000 |
| task-004 | basic | aggregation | ❌ | 10 | $0.0000 |
| task-005 | basic | aggregation | ✅ | 8 | $0.0000 |
| task-025 | basic | calculation | ❌ | 10 | $0.0000 |
| task-006 | intermediate | time-intelligence | ❌ | 10 | $0.0000 |
| task-007 | intermediate | time-intelligence | ❌ | 10 | $0.0000 |
| task-008 | intermediate | filtering | ❌ | 10 | $0.0000 |
| task-011 | intermediate | table-manipulation | ✅ | 8 | $0.0000 |
| task-012 | intermediate | table-manipulation | ✅ | 1 | $0.0000 |
| task-015 | intermediate | context-transition | ❌ | 10 | $0.0000 |
| task-017 | intermediate | context-transition | ❌ | 10 | $0.0000 |
| task-019 | intermediate | filtering | ❌ | 10 | $0.0000 |
| task-022 | intermediate | iterator | ❌ | 10 | $0.0000 |
| task-023 | intermediate | table-manipulation | ❌ | 10 | $0.0000 |
| task-026 | intermediate | calculation | ❌ | 10 | $0.0000 |
| task-027 | intermediate | time-intelligence | ❌ | 10 | $0.0000 |
| task-029 | intermediate | time-intelligence | ❌ | 10 | $0.0000 |
| task-009 | advanced | calculation | ❌ | 10 | $0.0000 |
| task-010 | advanced | iterator | ❌ | 10 | $0.0000 |
| task-013 | advanced | table-manipulation | ❌ | 10 | $0.0000 |
| task-014 | advanced | table-manipulation | ❌ | 10 | $0.0000 |
| task-016 | advanced | context-transition | ❌ | 10 | $0.0000 |
| task-018 | advanced | context-transition | ❌ | 10 | $0.0000 |
| task-020 | advanced | filtering | ❌ | 10 | $0.0000 |
| task-021 | advanced | filtering | ❌ | 10 | $0.0000 |
| task-024 | advanced | iterator | ❌ | 10 | $0.0000 |
| task-028 | advanced | time-intelligence | ❌ | 10 | $0.0000 |
| task-030 | advanced | time-intelligence | ❌ | 10 | $0.0000 |

---

## Failed Tasks (if any)

- **task-002**: Count of Customers (basic)
- **task-003**: Average Unit Price (basic)
- **task-004**: Distinct Product Count (basic)
- **task-025**: Handle Missing Data with BLANK (basic)
- **task-006**: Year-to-Date Sales (intermediate)
- **task-007**: Previous Year Sales (intermediate)
- **task-008**: Sales by Category Filter (intermediate)
- **task-015**: Product Percentage of Category Total (intermediate)
- **task-017**: Granularity-Aware Measure with VALUES (intermediate)
- **task-019**: Multiple Filter Conditions (intermediate)
- **task-022**: Product Ranking with RANKX (intermediate)
- **task-023**: Top 5 Products with TOPN (intermediate)
- **task-026**: Safe Ratio with Cascading Fallbacks (intermediate)
- **task-027**: Safe Year-over-Year with Missing Data (intermediate)
- **task-029**: Same Month Previous Year Comparison (intermediate)
- **task-009**: Year-over-Year Growth Percentage (advanced)
- **task-010**: Running Total with CALCULATE and FILTER (advanced)
- **task-013**: Union of High-Value Transactions (advanced)
- **task-014**: Year-Category Analysis Matrix (advanced)
- **task-016**: Virtual Relationship with TREATAS (advanced)
- **task-018**: Running Count with EARLIER (advanced)
- **task-020**: Percentage of Total with ALLEXCEPT (advanced)
- **task-021**: Filter Intersection with KEEPFILTERS (advanced)
- **task-024**: 90th Percentile Order Value (advanced)
- **task-028**: 3-Month Rolling Average (advanced)
- **task-030**: Fiscal Year-to-Date (July Start) (advanced)
