# DAX Bench Run Log

## Run Information
| Field | Value |
|-------|-------|
| **Task** | task-027 - Safe Year-over-Year with Missing Data |
| **Model** | mistralai/mistral-small-3.1-24b-instruct |
| **Timestamp** | 2025-12-13T16:43:00Z |
| **Result** | ✅ SOLVED in 2 iteration(s) |

## Task Details
- **Complexity**: intermediate
- **Category**: time-intelligence

---

## Iterations

### Iteration 1
**Token Usage**: 171 input, 115 output

**Model Response**:
```dax
Safe YoY Change =
VAR CurrentYearSales = SUM('Sales'[Net Price])
VAR PreviousYearSales = CALCULATE(
    SUM('Sales'[Net Price]),
    SAMEPERIODLASTYEAR('Date'[Date])
)
VAR Result =
    IF(
        ISBLANK(CurrentYearSales),
        0,
        IF(
            ISBLANK(PreviousYearSales),
            CurrentYearSales,
            DIVIDE(CurrentYearSales - PreviousYearSales, PreviousYearSales)
        )
    )
RETURN Result
```

**Validation**: ❌ FAILED (no_match)

---

### Iteration 2
**Token Usage**: 505 input, 79 output

**Model Response**:
```dax
Safe YoY Change =
VAR CurrentSales = SUM(Sales[Net Price])
VAR PriorSales = CALCULATE(SUM(Sales[Net Price]), SAMEPERIODLASTYEAR('Date'[Date]))
RETURN IF(ISBLANK(CurrentSales), 0, IF(ISBLANK(PriorSales), CurrentSales, CurrentSales - PriorSales))
```

**Validation**: ✅ PASSED (exact_match)

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Iterations** | 2 |
| **First Try Success** | ❌ No |
| **Input Tokens** | 676 |
| **Output Tokens** | 194 |
| **Total Cost** | $0.000042 |
| **Total Time** | 8.90s |

## Final DAX
```dax
Safe YoY Change =
VAR CurrentSales = SUM(Sales[Net Price])
VAR PriorSales = CALCULATE(SUM(Sales[Net Price]), SAMEPERIODLASTYEAR('Date'[Date]))
RETURN IF(ISBLANK(CurrentSales), 0, IF(ISBLANK(PriorSales), CurrentSales, CurrentSales - PriorSales))
```
