# DAX Bench Report (v3 - Dual Tier Feedback)

## Configuration
| Setting | Value |
|---------|-------|
| **Model** | google/gemini-2.5-flash |
| **Timestamp** | 2025-12-13T13:31:57Z |
| **Tier 1** | 5 iterations (basic feedback) |
| **Tier 2** | 5 iterations (enhanced feedback) |
| **Max Total** | 10 iterations |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | 11/30 (36.7%) |
| **First-Try Success** | 7/30 (23.3%) |
| **Solved in Tier 1** | 9/30 (30.0%) |
| **Solved in Tier 2** | 2/30 (6.7%) |
| **Total Iterations** | 215 |
| **Avg Iterations** | 7.17 |
| **Total Cost** | $0.0753 |
| **Total Time** | 228.7s (3.8m) |

---

## Tier Analysis

The dual-tier approach uses:
- **Tier 1**: Simple "try again" feedback - lets model explore freely
- **Tier 2**: Function hints and tips - helps when stuck

| Tier | Solved | % of Total Solves |
|------|--------|-------------------|
| First Try | 7 | 64% |
| Tier 1 (2-5) | 2 | 18% |
| Tier 2 (6-10) | 2 | 18% |

---

## Results by Complexity

| Complexity | Solved | Tier 1 | Tier 2 | Failed |
|------------|--------|--------|--------|--------|
| Basic | 6/6 | 6 | 0 | 0 |
| Intermediate | 5/13 | 3 | 2 | 8 |
| Advanced | 0/11 | 0 | 0 | 11 |

---

## Per-Task Results

| Task | Complexity | Solved | Tier | Iters | Cost |
|------|------------|--------|------|-------|------|
| task-001 | basic | ✅ | 1 | 1 | $0.0001 |
| task-002 | basic | ✅ | 1 | 2 | $0.0001 |
| task-003 | basic | ✅ | 1 | 1 | $0.0001 |
| task-004 | basic | ✅ | 1 | 1 | $0.0001 |
| task-005 | basic | ✅ | 1 | 1 | $0.0001 |
| task-025 | basic | ✅ | 1 | 1 | $0.0001 |
| task-006 | intermediate | ✅ | 2 | 7 | $0.0010 |
| task-007 | intermediate | ✅ | 2 | 7 | $0.0008 |
| task-008 | intermediate | ✅ | 1 | 2 | $0.0002 |
| task-011 | intermediate | ❌ | None | 10 | $0.0024 |
| task-012 | intermediate | ❌ | None | 10 | $0.0026 |
| task-015 | intermediate | ❌ | None | 10 | $0.0035 |
| task-017 | intermediate | ❌ | None | 10 | $0.0044 |
| task-019 | intermediate | ❌ | None | 10 | $0.0030 |
| task-022 | intermediate | ✅ | 1 | 1 | $0.0001 |
| task-023 | intermediate | ❌ | None | 10 | $0.0055 |
| task-026 | intermediate | ❌ | None | 10 | $0.0053 |
| task-027 | intermediate | ❌ | None | 10 | $0.0059 |
| task-029 | intermediate | ✅ | 1 | 1 | $0.0001 |
| task-009 | advanced | ❌ | None | 10 | $0.0042 |
| task-010 | advanced | ❌ | None | 10 | $0.0034 |
| task-013 | advanced | ❌ | None | 10 | $0.0061 |
| task-014 | advanced | ❌ | None | 10 | $0.0031 |
| task-016 | advanced | ❌ | None | 10 | $0.0030 |
| task-018 | advanced | ❌ | None | 10 | $0.0030 |
| task-020 | advanced | ❌ | None | 10 | $0.0036 |
| task-021 | advanced | ❌ | None | 10 | $0.0040 |
| task-024 | advanced | ❌ | None | 10 | $0.0021 |
| task-028 | advanced | ❌ | None | 10 | $0.0048 |
| task-030 | advanced | ❌ | None | 10 | $0.0031 |

---

## Failed Tasks

- **task-011**: Sales Summary by Category (table-manipulation)
- **task-012**: Product List with Renamed Columns (table-manipulation)
- **task-015**: Product Percentage of Category Total (context-transition)
- **task-017**: Granularity-Aware Measure with VALUES (context-transition)
- **task-019**: Multiple Filter Conditions (filtering)
- **task-023**: Top 5 Products with TOPN (table-manipulation)
- **task-026**: Safe Ratio with Cascading Fallbacks (calculation)
- **task-027**: Safe Year-over-Year with Missing Data (time-intelligence)
- **task-009**: Year-over-Year Growth Percentage (calculation)
- **task-010**: Running Total with CALCULATE and FILTER (iterator)
- **task-013**: Union of High-Value Transactions (table-manipulation)
- **task-014**: Year-Category Analysis Matrix (table-manipulation)
- **task-016**: Virtual Relationship with TREATAS (context-transition)
- **task-018**: Running Count with EARLIER (context-transition)
- **task-020**: Percentage of Total with ALLEXCEPT (filtering)
- **task-021**: Filter Intersection with KEEPFILTERS (filtering)
- **task-024**: 90th Percentile Order Value (iterator)
- **task-028**: 3-Month Rolling Average (time-intelligence)
- **task-030**: Fiscal Year-to-Date (July Start) (time-intelligence)
