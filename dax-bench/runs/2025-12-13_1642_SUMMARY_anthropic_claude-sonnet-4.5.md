# DAX Bench Full Benchmark Report

## Run Information
| Field | Value |
|-------|-------|
| **Model** | anthropic/claude-sonnet-4.5 |
| **Timestamp** | 2025-12-13T16:42:46Z |
| **Tasks Run** | 30 |
| **Max Iterations** | 10 |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | 28/30 (93.3%) |
| **First-Try Success** | 4/30 (13.3%) |
| **Total Iterations** | 82 |
| **Avg Iterations/Task** | 2.73 |
| **Total Input Tokens** | 54,343 |
| **Total Output Tokens** | 6,124 |
| **Total Tokens** | 60,467 |
| **Total Cost** | $0.2549 |
| **Cost per Task** | $0.008496 |
| **Total Time** | 183.1s (3.1m) |
| **Avg Time/Task** | 6.10s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
| Basic | 6/6 | 3/6 | 1.50 |
| Intermediate | 12/13 | 1/13 | 2.62 |
| Advanced | 10/11 | 0/11 | 3.55 |

---

## Per-Task Results

| Task | Complexity | Category | Solved | Iters | Cost |
|------|------------|----------|--------|-------|------|
| task-001 | basic | aggregation | ✅ | 1 | $0.0006 |
| task-002 | basic | aggregation | ✅ | 2 | $0.0012 |
| task-003 | basic | aggregation | ✅ | 1 | $0.0006 |
| task-004 | basic | aggregation | ✅ | 2 | $0.0015 |
| task-005 | basic | aggregation | ✅ | 1 | $0.0006 |
| task-025 | basic | calculation | ✅ | 2 | $0.0023 |
| task-006 | intermediate | time-intelligence | ✅ | 2 | $0.0026 |
| task-007 | intermediate | time-intelligence | ✅ | 2 | $0.0020 |
| task-008 | intermediate | filtering | ✅ | 1 | $0.0008 |
| task-011 | intermediate | table-manipulation | ✅ | 2 | $0.0023 |
| task-012 | intermediate | table-manipulation | ✅ | 2 | $0.0026 |
| task-015 | intermediate | context-transition | ✅ | 2 | $0.0043 |
| task-017 | intermediate | context-transition | ✅ | 2 | $0.0038 |
| task-019 | intermediate | filtering | ✅ | 2 | $0.0027 |
| task-022 | intermediate | iterator | ✅ | 2 | $0.0020 |
| task-023 | intermediate | table-manipulation | ✅ | 3 | $0.0116 |
| task-026 | intermediate | calculation | ❌ | 10 | $0.0620 |
| task-027 | intermediate | time-intelligence | ✅ | 2 | $0.0066 |
| task-029 | intermediate | time-intelligence | ✅ | 2 | $0.0024 |
| task-009 | advanced | calculation | ✅ | 9 | $0.0443 |
| task-010 | advanced | iterator | ✅ | 2 | $0.0030 |
| task-013 | advanced | table-manipulation | ✅ | 2 | $0.0058 |
| task-014 | advanced | table-manipulation | ✅ | 2 | $0.0023 |
| task-016 | advanced | context-transition | ✅ | 2 | $0.0039 |
| task-018 | advanced | context-transition | ✅ | 4 | $0.0057 |
| task-020 | advanced | filtering | ✅ | 2 | $0.0038 |
| task-021 | advanced | filtering | ✅ | 2 | $0.0036 |
| task-024 | advanced | iterator | ❌ | 10 | $0.0616 |
| task-028 | advanced | time-intelligence | ✅ | 2 | $0.0057 |
| task-030 | advanced | time-intelligence | ✅ | 2 | $0.0028 |

---

## Failed Tasks (if any)

- **task-026**: Safe Ratio with Cascading Fallbacks (intermediate)
- **task-024**: 90th Percentile Order Value (advanced)
