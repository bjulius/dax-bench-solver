# DAX Bench Full Benchmark Report

## Run Information
| Field | Value |
|-------|-------|
| **Model** | anthropic/claude-sonnet-4.5 |
| **Timestamp** | 2025-12-13T21:26:26Z |
| **Tasks Run** | 30 |
| **Max Iterations** | 10 |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | 29/30 (96.7%) |
| **First-Try Success** | 5/30 (16.7%) |
| **Total Iterations** | 65 |
| **Avg Iterations/Task** | 2.17 |
| **Total Input Tokens** | 27,355 |
| **Total Output Tokens** | 4,588 |
| **Total Tokens** | 31,943 |
| **Total Cost** | $0.1509 |
| **Cost per Task** | $0.005030 |
| **Total Time** | 144.9s (2.4m) |
| **Avg Time/Task** | 4.83s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
| Basic | 6/6 | 4/6 | 1.33 |
| Intermediate | 13/13 | 1/13 | 2.00 |
| Advanced | 10/11 | 0/11 | 2.82 |

---

## Per-Task Results

| Task | Complexity | Category | Solved | Iters | Cost |
|------|------------|----------|--------|-------|------|
| task-001 | basic | aggregation | ✅ | 1 | $0.0006 |
| task-002 | basic | aggregation | ✅ | 2 | $0.0012 |
| task-003 | basic | aggregation | ✅ | 1 | $0.0006 |
| task-004 | basic | aggregation | ✅ | 1 | $0.0006 |
| task-005 | basic | aggregation | ✅ | 1 | $0.0006 |
| task-025 | basic | calculation | ✅ | 2 | $0.0023 |
| task-006 | intermediate | time-intelligence | ✅ | 2 | $0.0022 |
| task-007 | intermediate | time-intelligence | ✅ | 2 | $0.0020 |
| task-008 | intermediate | filtering | ✅ | 1 | $0.0008 |
| task-011 | intermediate | table-manipulation | ✅ | 2 | $0.0023 |
| task-012 | intermediate | table-manipulation | ✅ | 2 | $0.0026 |
| task-015 | intermediate | context-transition | ✅ | 2 | $0.0043 |
| task-017 | intermediate | context-transition | ✅ | 2 | $0.0034 |
| task-019 | intermediate | filtering | ✅ | 2 | $0.0027 |
| task-022 | intermediate | iterator | ✅ | 2 | $0.0020 |
| task-023 | intermediate | table-manipulation | ✅ | 3 | $0.0105 |
| task-026 | intermediate | calculation | ✅ | 2 | $0.0056 |
| task-027 | intermediate | time-intelligence | ✅ | 2 | $0.0066 |
| task-029 | intermediate | time-intelligence | ✅ | 2 | $0.0024 |
| task-009 | advanced | calculation | ✅ | 2 | $0.0045 |
| task-010 | advanced | iterator | ✅ | 2 | $0.0030 |
| task-013 | advanced | table-manipulation | ✅ | 2 | $0.0058 |
| task-014 | advanced | table-manipulation | ✅ | 2 | $0.0023 |
| task-016 | advanced | context-transition | ✅ | 2 | $0.0039 |
| task-018 | advanced | context-transition | ✅ | 3 | $0.0058 |
| task-020 | advanced | filtering | ✅ | 2 | $0.0038 |
| task-021 | advanced | filtering | ✅ | 2 | $0.0030 |
| task-024 | advanced | iterator | ❌ | 10 | $0.0568 |
| task-028 | advanced | time-intelligence | ✅ | 2 | $0.0061 |
| task-030 | advanced | time-intelligence | ✅ | 2 | $0.0028 |

---

## Failed Tasks (if any)

- **task-024**: 90th Percentile Order Value (advanced)
