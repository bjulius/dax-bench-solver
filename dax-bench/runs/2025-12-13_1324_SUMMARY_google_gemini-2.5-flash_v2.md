# DAX Bench Full Benchmark Report (v2 - Enhanced Feedback)

## Run Information
| Field | Value |
|-------|-------|
| **Model** | google/gemini-2.5-flash |
| **Timestamp** | 2025-12-13T13:24:11Z |
| **Tasks Run** | 30 |
| **Max Iterations** | 10 |
| **Feedback Mode** | Enhanced (function hints, pattern analysis) |

---

## Summary Results

| Metric | Value |
|--------|-------|
| **Tasks Solved** | 15/30 (50.0%) |
| **First-Try Success** | 7/30 (23.3%) |
| **Total Iterations** | 176 |
| **Avg Iterations/Task** | 5.87 |
| **Total Input Tokens** | 136,053 |
| **Total Output Tokens** | 12,335 |
| **Total Tokens** | 148,388 |
| **Total Cost** | $0.0695 |
| **Cost per Task** | $0.002318 |
| **Total Time** | 189.4s (3.2m) |
| **Avg Time/Task** | 6.31s |

---

## Results by Complexity

| Complexity | Solved | First-Try | Avg Iters |
|------------|--------|-----------|-----------|
| Basic | 6/6 | 5/6 | 1.17 |
| Intermediate | 5/13 | 2/13 | 6.85 |
| Advanced | 4/11 | 0/11 | 7.27 |

---

## Results by Category

| Category | Solved | First-Try | Tasks |
|----------|--------|-----------|-------|
| aggregation | 5/5 | 4/5 | 5 |
| calculation | 1/3 | 1/3 | 3 |
| context-transition | 1/4 | 0/4 | 4 |
| filtering | 1/4 | 1/4 | 4 |
| iterator | 2/3 | 0/3 | 3 |
| table-manipulation | 1/5 | 0/5 | 5 |
| time-intelligence | 4/6 | 1/6 | 6 |

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
| task-008 | intermediate | filtering | ✅ | 1 | $0.0001 |
| task-011 | intermediate | table-manipulation | ❌ | 10 | $0.0031 |
| task-012 | intermediate | table-manipulation | ❌ | 10 | $0.0033 |
| task-015 | intermediate | context-transition | ❌ | 10 | $0.0038 |
| task-017 | intermediate | context-transition | ❌ | 10 | $0.0055 |
| task-019 | intermediate | filtering | ❌ | 10 | $0.0032 |
| task-022 | intermediate | iterator | ✅ | 3 | $0.0005 |
| task-023 | intermediate | table-manipulation | ❌ | 10 | $0.0064 |
| task-026 | intermediate | calculation | ❌ | 10 | $0.0054 |
| task-027 | intermediate | time-intelligence | ❌ | 10 | $0.0055 |
| task-029 | intermediate | time-intelligence | ✅ | 1 | $0.0001 |
| task-009 | advanced | calculation | ❌ | 10 | $0.0036 |
| task-010 | advanced | iterator | ❌ | 10 | $0.0039 |
| task-013 | advanced | table-manipulation | ❌ | 10 | $0.0070 |
| task-014 | advanced | table-manipulation | ✅ | 2 | $0.0003 |
| task-016 | advanced | context-transition | ✅ | 2 | $0.0004 |
| task-018 | advanced | context-transition | ❌ | 10 | $0.0037 |
| task-020 | advanced | filtering | ❌ | 10 | $0.0042 |
| task-021 | advanced | filtering | ❌ | 10 | $0.0035 |
| task-024 | advanced | iterator | ✅ | 2 | $0.0002 |
| task-028 | advanced | time-intelligence | ✅ | 4 | $0.0014 |
| task-030 | advanced | time-intelligence | ❌ | 10 | $0.0038 |

---

## Failed Tasks (if any)

### task-011: Sales Summary by Category
- **Complexity**: intermediate
- **Category**: table-manipulation
- **Iterations**: 10
- **Last Attempt**:
```dax
Category Summary = 
ADDCOLUMNS(
    SUMMARIZE(
        'Sales',
        'Product'[Category]
    ),
    "Total Sales", CALCULATE(SUM('Sales'[Net Price]))
)
```

### task-012: Product List with Renamed Columns
- **Complexity**: intermediate
- **Category**: table-manipulation
- **Iterations**: 10
- **Last Attempt**:
```dax
Product Catalog = 
SELECTCOLUMNS(
    Product,
    "Name", Product[Product Name],
    "Brand", Product[Brand],
    "Product Category", Product[Category]
)
```

### task-015: Product Percentage of Category Total
- **Complexity**: intermediate
- **Category**: context-transition
- **Iterations**: 10
- **Last Attempt**:
```dax
VAR CurrentProductSales = CALCULATE(SUM(Sales[Net Price]), ALLEXCEPT(Product, Product[ProductKey]))
VAR CategorySales = CALCULATE(SUM(Sales[Net Price]), ALL(Product[ProductKey]), Product[Category])
RETURN
    DIVIDE(CurrentProductSales, CategorySales)
```

### task-017: Granularity-Aware Measure with VALUES
- **Complexity**: intermediate
- **Category**: context-transition
- **Iterations**: 10
- **Last Attempt**:
```dax
Smart Sales =
IF (
    HASONEVALUE ( 'Date'[Year] ) && NOT ( HASONEVALUE ( 'Date'[Month] ) ),
    SUM ( Sales[Net Price] ),
    IF (
        HASONEVALUE ( 'Date'[Month] ),
        AVERAGEX ( VALUES ( 'Date'[Month] ), CALCULATE ( SUM ( Sales[Net Price] ) ) ),
        SUM ( Sales[Net Price] )
    )
)
```

### task-019: Multiple Filter Conditions
- **Complexity**: intermediate
- **Category**: filtering
- **Iterations**: 10
- **Last Attempt**:
```dax
Premium Audio Sales =
CALCULATE (
    SUM ( Sales[Net Price] ),
    Product[Category] = "Audio",
    Product[Unit Price] > 100
)
```

### task-023: Top 5 Products with TOPN
- **Complexity**: intermediate
- **Category**: table-manipulation
- **Iterations**: 10
- **Last Attempt**:
```dax
Top 5 Sales = 
IF(
    ISINSCOPE(Product[Product Name]),
    VAR CurrentProduct = SELECTEDVALUE(Product[Product Name])
    VAR Top5Products = 
        TOPN(
            5,
            ALL(Product),
            SUM(Sales[Net Price]),
            DESC
        )
    RETURN
        IF(
            CurrentProduct IN SELECTCOLUMNS(Top5Products, "Name", Product[Product Name]),
            SUM(Sales[Net Price]),
            BLANK()
        ),
    SUM(Sales[Net Price])
)
```

### task-026: Safe Ratio with Cascading Fallbacks
- **Complexity**: intermediate
- **Category**: calculation
- **Iterations**: 10
- **Last Attempt**:
```dax
VAR _netPrice = SUM(Sales[Net Price])
VAR _unitCost = SUM(Sales[Unit Cost])
VAR _profitMargin = 
    IF(
        _netPrice = 0 || ISBLANK(_netPrice),
        0,
        DIVIDE(
            _netPrice - _unitCost,
            _netPrice
        )
    )
RETURN
    IF(
        _profitMargin < 0,
        0,
        _profitMargin
    ) * 100
```

### task-027: Safe Year-over-Year with Missing Data
- **Complexity**: intermediate
- **Category**: time-intelligence
- **Iterations**: 10
- **Last Attempt**:
```dax
Safe YoY Change = 
VAR CurrentSales = SUM(Sales[Net Price])
VAR PriorSales = CALCULATE(SUM(Sales[Net Price]), SAMEPERIODLASTYEAR('Date'[Date]))
RETURN
    IF(
        ISBLANK(CurrentSales),
        0,
        IF(
            ISBLANK(PriorSales),
            CurrentSales,
            CurrentSales - PriorSales
        )
    )
```

### task-009: Year-over-Year Growth Percentage
- **Complexity**: advanced
- **Category**: calculation
- **Iterations**: 10
- **Last Attempt**:
```dax
VAR CurrentYearSales = SUM(Sales[Net Price])
VAR PreviousYearSales = CALCULATE(SUM(Sales[Net Price]), SAMEPERIODLASTYEAR(Date[Date]))
RETURN
    DIVIDE(CurrentYearSales - PreviousYearSales, PreviousYearSales, BLANK())
```

### task-010: Running Total with CALCULATE and FILTER
- **Complexity**: advanced
- **Category**: iterator
- **Iterations**: 10
- **Last Attempt**:
```dax
Running Total =
CALCULATE (
    SUM ( Sales[Net Price] ),
    FILTER (
        ALL ( 'Date' ),
        'Date'[Year] = MAX ( 'Date'[Year] )
            && 'Date'[Date] <= MAX ( 'Date'[Date] )
    )
)
```

### task-013: Union of High-Value Transactions
- **Complexity**: advanced
- **Category**: table-manipulation
- **Iterations**: 10
- **Last Attempt**:
```dax
Special Orders =
UNION(
    SELECTCOLUMNS(
        FILTER(
            Sales,
            Sales[Net Price] > 1000
        ),
        "Order Number", Sales[Order Number],
        "Net Price", Sales[Net Price],
        "Quantity", Sales[Quantity]
    ),
    SELECTCOLUMNS(
        FILTER(
            Sales,
            Sales[Quantity] > 10
        ),
        "Order Number", Sales[Order Number],
        "Net Price", Sales[Net Price],
        "Quantity", Sales[Quantity]
    )
)
```

### task-018: Running Count with EARLIER
- **Complexity**: advanced
- **Category**: context-transition
- **Iterations**: 10
- **Last Attempt**:
```dax
Category Rank by Price =
COUNTROWS(
    FILTER(
        Product,
        Product[Category] = EARLIER(Product[Category]) && Product[Unit Price] > EARLIER(Product[Unit Price])
    )
) + 1
```

### task-020: Percentage of Total with ALLEXCEPT
- **Complexity**: advanced
- **Category**: filtering
- **Iterations**: 10
- **Last Attempt**:
```dax
of Year = 
VAR _CategorySales = SUM(Sales[Net Price])
VAR _YearSales = 
    CALCULATE(
        SUM(Sales[Net Price]),
        ALL(Product),
        ALLEXCEPT('Date', 'Date'[Year])
    )
RETURN
    DIVIDE(_CategorySales, _YearSales)
```

### task-021: Filter Intersection with KEEPFILTERS
- **Complexity**: advanced
- **Category**: filtering
- **Iterations**: 10
- **Last Attempt**:
```dax
Selected Category Audio Only = 
CALCULATE(
    SUM(Sales[Net Price]),
    KEEPFILTERS(Product[Category] = "Audio")
)
```

### task-030: Fiscal Year-to-Date (July Start)
- **Complexity**: advanced
- **Category**: time-intelligence
- **Iterations**: 10
- **Last Attempt**:
```dax
Fiscal YTD Sales = 
CALCULATE(
    SUM(Sales[Net Price]),
    DATESYTD(
        'Date'[Date], 
        "6/30"
    )
)
```

