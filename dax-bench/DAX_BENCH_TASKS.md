# DAX Bench Task Reference

*A comprehensive benchmark for evaluating LLM DAX generation capabilities*

**Author:** Maxim
**Version:** 2.0
**Total Tasks:** 30 (6 Basic, 13 Intermediate, 11 Advanced)

---

## Data Model Context (Contoso)

All tasks use the **Contoso Sales** data model:

| Table | Key Columns | Description |
|-------|-------------|-------------|
| **Sales** | Order Number, Net Price, Quantity, Unit Price, Unit Cost, ProductKey, Order Date | Transactional fact table |
| **Product** | ProductKey, Product Name, Category, Brand, Unit Price | Product dimension |
| **Customer** | CustomerKey, Name, City, Country | Customer dimension |
| **Date** | Date, Year, Month, Quarter | Date dimension (related to Sales[Order Date]) |
| **Budget** | Year, Budget Amount | Disconnected budget table (for TREATAS tasks) |

---

## Basic Tasks (6)

### Task 001: Total Sales Amount
**Category:** Aggregation

> Create a DAX measure called 'Total Sales' that calculates the sum of the 'Net Price' column from the 'Sales' table.

```dax
Total Sales = SUM(Sales[Net Price])
```

**Alternatives:**
- `SUMX(Sales, Sales[Net Price])`

---

### Task 002: Count of Customers
**Category:** Aggregation

> Create a DAX measure called 'Customer Count' that counts the total number of rows in the 'Customer' table.

```dax
Customer Count = COUNTROWS(Customer)
```

**Alternatives:**
- `COUNT(Customer[CustomerKey])`

---

### Task 003: Average Unit Price
**Category:** Aggregation

> Create a DAX measure called 'Avg Unit Price' that calculates the average of the 'Unit Price' column from the 'Sales' table.

```dax
Avg Unit Price = AVERAGE(Sales[Unit Price])
```

**Alternatives:**
- `AVERAGEX(Sales, Sales[Unit Price])`

---

### Task 004: Distinct Product Count
**Category:** Aggregation

> Create a DAX measure called 'Products Sold' that counts the distinct number of products (using ProductKey) from the 'Sales' table.

```dax
Products Sold = DISTINCTCOUNT(Sales[ProductKey])
```

**Alternatives:**
- `COUNTROWS(DISTINCT(Sales[ProductKey]))`

---

### Task 005: Total Order Quantity
**Category:** Aggregation

> Create a DAX measure called 'Total Quantity' that sums the 'Quantity' column from the 'Sales' table.

```dax
Total Quantity = SUM(Sales[Quantity])
```

---

### Task 025: Handle Missing Data with BLANK
**Category:** Calculation | Error Handling

> Create a measure called 'Safe Quantity' that returns the total Quantity from Sales. If there are no sales (result is BLANK), return 0 instead of BLANK.

```dax
Safe Quantity = IF(ISBLANK(SUM(Sales[Quantity])), 0, SUM(Sales[Quantity]))
```

**Alternatives:**
- `COALESCE(SUM(Sales[Quantity]), 0)` *(preferred)*
- `SUM(Sales[Quantity]) + 0`

**Hints:**
- COALESCE returns the first non-BLANK value
- Adding 0 to a BLANK converts it to 0

---

## Intermediate Tasks (13)

### Task 006: Year-to-Date Sales
**Category:** Time Intelligence

> Create a DAX measure called 'YTD Sales' that calculates the year-to-date total of Net Price from Sales, using the Date table's Date column.

```dax
YTD Sales = TOTALYTD(SUM(Sales[Net Price]), 'Date'[Date])
```

**Alternatives:**
- `CALCULATE(SUM(Sales[Net Price]), DATESYTD('Date'[Date]))`

---

### Task 007: Previous Year Sales
**Category:** Time Intelligence

> Create a DAX measure called 'PY Sales' that calculates the Net Price from the same period last year.

```dax
PY Sales = CALCULATE(SUM(Sales[Net Price]), SAMEPERIODLASTYEAR('Date'[Date]))
```

**Alternatives:**
- `CALCULATE(SUM(Sales[Net Price]), DATEADD('Date'[Date], -1, YEAR))`

---

### Task 008: Sales by Category Filter
**Category:** Filtering

> Create a DAX measure called 'Audio Sales' that calculates the total Net Price only for products in the 'Audio' category.

```dax
Audio Sales = CALCULATE(SUM(Sales[Net Price]), Product[Category] = "Audio")
```

**Alternatives:**
- `CALCULATE(SUM(Sales[Net Price]), FILTER(Product, Product[Category] = "Audio"))`

---

### Task 011: Sales Summary by Category
**Category:** Table Manipulation

> Create a calculated table called 'Category Summary' that shows each product category with its total Net Price. The table should have two columns: Category and Total Sales.

```dax
Category Summary =
ADDCOLUMNS(
    SUMMARIZE(Sales, Product[Category]),
    "Total Sales", CALCULATE(SUM(Sales[Net Price]))
)
```

**Alternatives:**
- `SUMMARIZECOLUMNS(Product[Category], "Total Sales", SUM(Sales[Net Price]))` *(preferred for performance)*

**Anti-pattern:** Don't nest aggregations inside SUMMARIZE directly

---

### Task 012: Product List with Renamed Columns
**Category:** Table Manipulation

> Create a calculated table called 'Product Catalog' that contains only the Product Name, Brand, and Category columns. Rename 'Product Name' to 'Name' and 'Category' to 'Product Category'.

```dax
Product Catalog =
SELECTCOLUMNS(
    Product,
    "Name", Product[Product Name],
    "Brand", Product[Brand],
    "Product Category", Product[Category]
)
```

---

### Task 015: Product Percentage of Category Total
**Category:** Context Transition | Calculated Column

> Create a calculated column in the Product table called 'Category Share %' that shows what percentage each product's total sales represents of its category's total sales.

```dax
Category Share % =
VAR ProductSales = CALCULATE(SUM(Sales[Net Price]))
VAR CategorySales = CALCULATE(SUM(Sales[Net Price]), ALLEXCEPT(Product, Product[Category]))
RETURN DIVIDE(ProductSales, CategorySales) * 100
```

**Key Concepts:**
- CALCULATE triggers context transition from row to filter context
- ALLEXCEPT keeps filters on specified columns while removing others

---

### Task 017: Granularity-Aware Measure with VALUES
**Category:** Context Transition

> Create a measure called 'Smart Sales' that returns the total Net Price when viewing at Year level, but returns the average Net Price per month when viewing at Month level.

```dax
Smart Sales =
IF(
    HASONEVALUE('Date'[Year]) && NOT(HASONEVALUE('Date'[Month])),
    SUM(Sales[Net Price]),
    IF(
        HASONEVALUE('Date'[Month]),
        AVERAGEX(VALUES('Date'[Month]), CALCULATE(SUM(Sales[Net Price]))),
        SUM(Sales[Net Price])
    )
)
```

**Key Concept:** HASONEVALUE returns TRUE when exactly one value is in filter context

---

### Task 019: Multiple Filter Conditions
**Category:** Filtering

> Create a measure called 'Premium Audio Sales' that calculates the total Net Price only for products in the 'Audio' category AND with a Unit Price greater than 100.

```dax
Premium Audio Sales =
CALCULATE(
    SUM(Sales[Net Price]),
    Product[Category] = "Audio",
    Product[Unit Price] > 100
)
```

**Note:** Multiple filter arguments in CALCULATE are combined with AND logic

---

### Task 022: Product Ranking with RANKX
**Category:** Iterator

> Create a measure called 'Sales Rank' that ranks each product by its total Net Price sales (highest = rank 1). Use dense ranking.

```dax
Sales Rank = RANKX(ALL(Product), SUM(Sales[Net Price]), , DESC, DENSE)
```

**Key Concepts:**
- ALL(Product) creates proper ranking context
- DENSE avoids gaps in rank numbers for ties
- DESC sorts highest first

---

### Task 023: Top 5 Products with TOPN
**Category:** Table Manipulation

> Create a measure called 'Top 5 Sales' that returns the total Net Price ONLY when the current product is among the top 5 by sales. For products outside top 5, return BLANK().

```dax
Top 5 Sales =
VAR Top5 = TOPN(5, ALL(Product[Product Name]), CALCULATE(SUM(Sales[Net Price])), DESC)
VAR CurrentProduct = SELECTEDVALUE(Product[Product Name])
RETURN IF(CurrentProduct IN Top5, SUM(Sales[Net Price]), BLANK())
```

**Alternative approach:** Use RANKX and check if rank <= 5

---

### Task 026: Safe Ratio with Cascading Fallbacks
**Category:** Calculation | Error Handling

> Create a measure called 'Profit Margin %' that calculates (Net Price - Unit Cost) / Net Price * 100. Handle zero/BLANK Net Price (return 0) and negative margins (return 0).

```dax
Profit Margin % =
VAR TotalRevenue = SUM(Sales[Net Price])
VAR TotalCost = SUM(Sales[Unit Cost])
VAR RawMargin = DIVIDE(TotalRevenue - TotalCost, TotalRevenue, 0) * 100
RETURN IF(RawMargin < 0, 0, RawMargin)
```

**Key Concept:** DIVIDE's third parameter handles division by zero

---

### Task 027: Safe Year-over-Year with Missing Data
**Category:** Time Intelligence | Error Handling

> Create a measure called 'Safe YoY Change' that calculates year-over-year change. If no previous year data exists, return current year sales. If both years have no data, return 0.

```dax
Safe YoY Change =
VAR CurrentSales = SUM(Sales[Net Price])
VAR PriorSales = CALCULATE(SUM(Sales[Net Price]), SAMEPERIODLASTYEAR('Date'[Date]))
RETURN IF(
    ISBLANK(CurrentSales), 0,
    IF(ISBLANK(PriorSales), CurrentSales, CurrentSales - PriorSales)
)
```

**Alternative:** Use `COALESCE` for cleaner handling

---

### Task 029: Same Month Previous Year Comparison
**Category:** Time Intelligence

> Create a measure called 'Prior Year Month Sales' that returns the total Net Price for the same month in the previous year.

```dax
Prior Year Month Sales =
CALCULATE(SUM(Sales[Net Price]), PARALLELPERIOD('Date'[Date], -12, MONTH))
```

**Alternatives:**
- `SAMEPERIODLASTYEAR('Date'[Date])` *(most readable)*
- `DATEADD('Date'[Date], -1, YEAR)`

---

## Advanced Tasks (11)

### Task 009: Year-over-Year Growth Percentage
**Category:** Calculation

> Create a measure called 'YoY Growth %' that calculates (Current - Previous) / Previous. Handle division by zero with BLANK().

```dax
YoY Growth % =
VAR CurrentSales = SUM(Sales[Net Price])
VAR PreviousSales = CALCULATE(SUM(Sales[Net Price]), SAMEPERIODLASTYEAR('Date'[Date]))
RETURN DIVIDE(CurrentSales - PreviousSales, PreviousSales)
```

---

### Task 010: Running Total with CALCULATE and FILTER
**Category:** Iterator

> Create a measure called 'Running Total' that calculates a cumulative running total of Net Price within each year (resets at year start).

```dax
Running Total =
CALCULATE(
    SUM(Sales[Net Price]),
    FILTER(
        ALL('Date'),
        'Date'[Year] = MAX('Date'[Year]) && 'Date'[Date] <= MAX('Date'[Date])
    )
)
```

**Simpler Alternative:**
```dax
Running Total = CALCULATE(SUM(Sales[Net Price]), DATESYTD('Date'[Date]))
```

---

### Task 013: Union of High-Value Transactions
**Category:** Table Manipulation

> Create a calculated table called 'Special Orders' that combines: (1) orders with Net Price > 1000, and (2) orders with Quantity > 10. Include Order Number, Net Price, Quantity.

```dax
Special Orders =
UNION(
    SELECTCOLUMNS(FILTER(Sales, Sales[Net Price] > 1000),
        "Order Number", Sales[Order Number],
        "Net Price", Sales[Net Price],
        "Quantity", Sales[Quantity]
    ),
    SELECTCOLUMNS(FILTER(Sales, Sales[Quantity] > 10),
        "Order Number", Sales[Order Number],
        "Net Price", Sales[Net Price],
        "Quantity", Sales[Quantity]
    )
)
```

**Note:** UNION requires matching columns; does NOT remove duplicates (use DISTINCT if needed)

---

### Task 014: Year-Category Analysis Matrix
**Category:** Table Manipulation

> Create a calculated table called 'Analysis Matrix' with all combinations of Year and Category (Cartesian product for gap analysis).

```dax
Analysis Matrix = CROSSJOIN(ALL('Date'[Year]), ALL(Product[Category]))
```

**Alternative:** `GENERATE(ALL('Date'[Year]), ALL(Product[Category]))`

---

### Task 016: Virtual Relationship with TREATAS
**Category:** Context Transition

> Create a measure called 'Budget vs Actual' comparing actual Net Price to Budget Amount for the same year. Budget table is disconnected.

```dax
Budget vs Actual =
VAR ActualSales = SUM(Sales[Net Price])
VAR BudgetAmount = CALCULATE(
    SUM(Budget[Budget Amount]),
    TREATAS(VALUES('Date'[Year]), Budget[Year])
)
RETURN ActualSales - BudgetAmount
```

**Key Concept:** TREATAS applies lineage from one column to another, creating a virtual relationship

---

### Task 018: Running Count with EARLIER
**Category:** Context Transition | Calculated Column

> Create a calculated column called 'Category Rank by Price' that ranks each product within its category by Unit Price (highest = rank 1).

```dax
Category Rank by Price =
COUNTROWS(
    FILTER(
        Product,
        Product[Category] = EARLIER(Product[Category]) &&
        Product[Unit Price] > EARLIER(Product[Unit Price])
    )
) + 1
```

**Alternative (preferred for performance):**
```dax
Category Rank by Price =
RANKX(
    FILTER(ALL(Product), Product[Category] = EARLIER(Product[Category])),
    Product[Unit Price], , DESC, DENSE
)
```

**Key Concept:** EARLIER references the outer row context in nested iteration

---

### Task 020: Percentage of Total with ALLEXCEPT
**Category:** Filtering

> Create a measure called 'Category % of Year' showing each category's sales as percentage of total year sales (decimal format).

```dax
Category % of Year =
VAR CategorySales = SUM(Sales[Net Price])
VAR YearTotal = CALCULATE(
    SUM(Sales[Net Price]),
    ALLEXCEPT('Date', 'Date'[Year]),
    ALL(Product)
)
RETURN DIVIDE(CategorySales, YearTotal)
```

**Key Concept:** ALLEXCEPT removes all filters EXCEPT on specified columns

---

### Task 021: Filter Intersection with KEEPFILTERS
**Category:** Filtering

> Create a measure called 'Selected Category Audio Only' that shows Audio sales ONLY if Audio is already selected. If Computers is selected, return BLANK (no intersection).

```dax
Selected Category Audio Only =
CALCULATE(SUM(Sales[Net Price]), KEEPFILTERS(Product[Category] = "Audio"))
```

**Key Concept:** Without KEEPFILTERS, CALCULATE replaces filters. With KEEPFILTERS, filters intersect.

---

### Task 024: 90th Percentile Order Value
**Category:** Iterator | Statistics

> Create a measure called 'P90 Order Value' calculating the 90th percentile of Net Price.

```dax
P90 Order Value = PERCENTILEX.INC(Sales, Sales[Net Price], 0.9)
```

**Notes:**
- INC = inclusive (includes boundary), EXC = exclusive
- 0.9 = 90th percentile

---

### Task 028: 3-Month Rolling Average
**Category:** Time Intelligence

> Create a measure called 'Rolling 3M Avg Sales' calculating the average monthly sales over current month plus two preceding months.

```dax
Rolling 3M Avg Sales =
DIVIDE(
    CALCULATE(
        SUM(Sales[Net Price]),
        DATESINPERIOD('Date'[Date], MAX('Date'[Date]), -3, MONTH)
    ),
    3
)
```

**Alternative using AVERAGEX:**
```dax
Rolling 3M Avg Sales =
AVERAGEX(
    DATESINPERIOD('Date'[Date], MAX('Date'[Date]), -3, MONTH),
    CALCULATE(SUM(Sales[Net Price]))
)
```

---

### Task 030: Fiscal Year-to-Date (July Start)
**Category:** Time Intelligence

> Create a measure called 'Fiscal YTD Sales' using a fiscal year starting July 1st (ending June 30th).

```dax
Fiscal YTD Sales = CALCULATE(SUM(Sales[Net Price]), DATESYTD('Date'[Date], "6/30"))
```

**Alternatives:**
- `TOTALYTD(SUM(Sales[Net Price]), 'Date'[Date], "6/30")`

**Note:** The year_end_date parameter specifies June 30 for a July-start fiscal year

---

## Summary Statistics

| Complexity | Count | Key Patterns |
|------------|-------|--------------|
| Basic | 6 | SUM, COUNT, AVERAGE, DISTINCTCOUNT, ISBLANK |
| Intermediate | 13 | CALCULATE, TOTALYTD, SAMEPERIODLASTYEAR, SUMMARIZE, SELECTCOLUMNS, RANKX, TOPN |
| Advanced | 11 | FILTER, ALLEXCEPT, KEEPFILTERS, TREATAS, EARLIER, CROSSJOIN, UNION, DATESINPERIOD, PERCENTILEX |

## Common Anti-Patterns to Detect

1. **Excel functions**: SUMIF, SUMPRODUCT, VLOOKUP
2. **SQL functions**: DENSE_RANK, ROW_NUMBER, ORDER BY
3. **Missing table qualifiers**: `[Net Price]` instead of `Sales[Net Price]`
4. **Division without DIVIDE**: Risk of division by zero errors
5. **Nested SUMMARIZE aggregations**: Use ADDCOLUMNS pattern instead
6. **EARLIER in measures**: Requires row context (calculated columns only)
