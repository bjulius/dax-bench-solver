# DAX Bench Full Benchmark Report

## Run Information
| Field | Value |
|-------|-------|
| **Model** | meta-llama/llama-3.3-70b-instruct:free |
| **Timestamp** | 2025-12-13T21:38:23Z |
| **Tasks Run** | 30 |
| **Max Iterations** | 10 |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | 22/30 (73.3%) |
| **First-Try Success** | 1/30 (3.3%) |
| **Total Iterations** | 139 |
| **Avg Iterations/Task** | 4.63 |
| **Total Input Tokens** | 28,125 |
| **Total Output Tokens** | 2,384 |
| **Total Tokens** | 30,509 |
| **Total Cost** | $0.0000 |
| **Cost per Task** | $0.000000 |
| **Total Time** | 195.8s (3.3m) |
| **Avg Time/Task** | 6.53s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
| Basic | 6/6 | 1/6 | 1.83 |
| Intermediate | 6/13 | 0/13 | 6.85 |
| Advanced | 10/11 | 0/11 | 3.55 |

---

## Per-Task Results

| Task | Complexity | Category | Solved | Iters | Cost |
|------|------------|----------|--------|-------|------|
| task-001 | basic | aggregation | ✅ | 2 | $0.0000 |
| task-002 | basic | aggregation | ✅ | 2 | $0.0000 |
| task-003 | basic | aggregation | ✅ | 2 | $0.0000 |
| task-004 | basic | aggregation | ✅ | 2 | $0.0000 |
| task-005 | basic | aggregation | ✅ | 2 | $0.0000 |
| task-025 | basic | calculation | ✅ | 1 | $0.0000 |
| task-006 | intermediate | time-intelligence | ✅ | 2 | $0.0000 |
| task-007 | intermediate | time-intelligence | ✅ | 2 | $0.0000 |
| task-008 | intermediate | filtering | ❌ | 10 | $0.0000 |
| task-011 | intermediate | table-manipulation | ❌ | 10 | $0.0000 |
| task-012 | intermediate | table-manipulation | ❌ | 10 | $0.0000 |
| task-015 | intermediate | context-transition | ✅ | 3 | $0.0000 |
| task-017 | intermediate | context-transition | ✅ | 2 | $0.0000 |
| task-019 | intermediate | filtering | ✅ | 2 | $0.0000 |
| task-022 | intermediate | iterator | ❌ | 10 | $0.0000 |
| task-023 | intermediate | table-manipulation | ❌ | 10 | $0.0000 |
| task-026 | intermediate | calculation | ❌ | 10 | $0.0000 |
| task-027 | intermediate | time-intelligence | ❌ | 10 | $0.0000 |
| task-029 | intermediate | time-intelligence | ✅ | 8 | $0.0000 |
| task-009 | advanced | calculation | ✅ | 3 | $0.0000 |
| task-010 | advanced | iterator | ✅ | 3 | $0.0000 |
| task-013 | advanced | table-manipulation | ✅ | 3 | $0.0000 |
| task-014 | advanced | table-manipulation | ✅ | 3 | $0.0000 |
| task-016 | advanced | context-transition | ✅ | 3 | $0.0000 |
| task-018 | advanced | context-transition | ❌ | 10 | $0.0000 |
| task-020 | advanced | filtering | ✅ | 4 | $0.0000 |
| task-021 | advanced | filtering | ✅ | 3 | $0.0000 |
| task-024 | advanced | iterator | ✅ | 2 | $0.0000 |
| task-028 | advanced | time-intelligence | ✅ | 3 | $0.0000 |
| task-030 | advanced | time-intelligence | ✅ | 2 | $0.0000 |

---

## Failed Tasks (if any)

- **task-008**: Sales by Category Filter (intermediate)
- **task-011**: Sales Summary by Category (intermediate)
- **task-012**: Product List with Renamed Columns (intermediate)
- **task-022**: Product Ranking with RANKX (intermediate)
- **task-023**: Top 5 Products with TOPN (intermediate)
- **task-026**: Safe Ratio with Cascading Fallbacks (intermediate)
- **task-027**: Safe Year-over-Year with Missing Data (intermediate)
- **task-018**: Running Count with EARLIER (advanced)
