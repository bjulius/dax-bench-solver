# DAX Bench Full Benchmark Report

## Run Information
| Field | Value |
|-------|-------|
| **Model** | anthropic/claude-opus-4.5 |
| **Timestamp** | 2025-12-13T14:07:42Z |
| **Tasks Run** | 30 |
| **Max Iterations** | 10 |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | 29/30 (96.7%) |
| **First-Try Success** | 8/30 (26.7%) |
| **Total Iterations** | 76 |
| **Avg Iterations/Task** | 2.53 |
| **Total Input Tokens** | 45,388 |
| **Total Output Tokens** | 5,378 |
| **Total Tokens** | 50,766 |
| **Total Cost** | $0.3614 |
| **Cost per Task** | $0.012046 |
| **Total Time** | 242.1s (4.0m) |
| **Avg Time/Task** | 8.07s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
| Basic | 6/6 | 3/6 | 1.50 |
| Intermediate | 12/13 | 4/13 | 2.92 |
| Advanced | 11/11 | 1/11 | 2.64 |

---

## Per-Task Results

| Task | Complexity | Category | Solved | Iters | Cost |
|------|------------|----------|--------|-------|------|
| task-001 | basic | aggregation | ✅ | 1 | $0.0010 |
| task-002 | basic | aggregation | ✅ | 2 | $0.0021 |
| task-003 | basic | aggregation | ✅ | 1 | $0.0011 |
| task-004 | basic | aggregation | ✅ | 2 | $0.0025 |
| task-005 | basic | aggregation | ✅ | 1 | $0.0010 |
| task-025 | basic | calculation | ✅ | 2 | $0.0040 |
| task-006 | intermediate | time-intelligence | ✅ | 1 | $0.0014 |
| task-007 | intermediate | time-intelligence | ✅ | 1 | $0.0013 |
| task-008 | intermediate | filtering | ✅ | 1 | $0.0013 |
| task-011 | intermediate | table-manipulation | ✅ | 3 | $0.0069 |
| task-012 | intermediate | table-manipulation | ✅ | 2 | $0.0043 |
| task-015 | intermediate | context-transition | ❌ | 10 | $0.0849 |
| task-017 | intermediate | context-transition | ✅ | 2 | $0.0066 |
| task-019 | intermediate | filtering | ✅ | 2 | $0.0040 |
| task-022 | intermediate | iterator | ✅ | 2 | $0.0039 |
| task-023 | intermediate | table-manipulation | ✅ | 3 | $0.0185 |
| task-026 | intermediate | calculation | ✅ | 8 | $0.0728 |
| task-027 | intermediate | time-intelligence | ✅ | 2 | $0.0107 |
| task-029 | intermediate | time-intelligence | ✅ | 1 | $0.0015 |
| task-009 | advanced | calculation | ✅ | 8 | $0.0632 |
| task-010 | advanced | iterator | ✅ | 3 | $0.0100 |
| task-013 | advanced | table-manipulation | ✅ | 2 | $0.0093 |
| task-014 | advanced | table-manipulation | ✅ | 2 | $0.0034 |
| task-016 | advanced | context-transition | ✅ | 2 | $0.0067 |
| task-018 | advanced | context-transition | ✅ | 2 | $0.0049 |
| task-020 | advanced | filtering | ✅ | 3 | $0.0130 |
| task-021 | advanced | filtering | ✅ | 2 | $0.0048 |
| task-024 | advanced | iterator | ✅ | 1 | $0.0014 |
| task-028 | advanced | time-intelligence | ✅ | 2 | $0.0103 |
| task-030 | advanced | time-intelligence | ✅ | 2 | $0.0047 |

---

## Failed Tasks (if any)

- **task-015**: Product Percentage of Category Total (intermediate)
