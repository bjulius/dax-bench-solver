
## Power BI Data Model Schema

### Tables and Columns

**Customer** (dimension)
- CustomerKey (Int64), Gender (String), Name (String), City (String)
- State Code (String), State (String), Country (String), Continent (String)
- Birthday (DateTime), Age (Int64)

**Product** (dimension)
- ProductKey (Int64), Product Code (String), Product Name (String)
- Manufacturer (String), Brand (String), Color (String)
- Unit Cost (Decimal), Unit Price (Decimal)
- Subcategory (String), Category (String)

**Sales** (fact table)
- Order Number (Int64), Line Number (Int64)
- Order Date (DateTime), Delivery Date (DateTime)
- CustomerKey (Int64), StoreKey (Int64), ProductKey (Int64)
- Quantity (Int64), Unit Price (Decimal), Net Price (Decimal), Unit Cost (Decimal)
- Currency Code (String), Exchange Rate (Double)

**Store** (dimension)
- StoreKey (Int64), Store Code (Int64)
- Country (String), State (String), Name (String)
- Square Meters (Int64), Open Date (DateTime), Close Date (DateTime), Status (String)

**'Date'** (date dimension - use quotes around table name)
- Date (DateTime) [PRIMARY KEY - use for time intelligence]
- Year (Int64), Month (Int64), Day (Int64)
- Day Name (String), Month Name (String)
- Quarter (Int64), Week of Year (Int64)
- Fiscal Year (Int64), Fiscal Quarter (Int64), Fiscal Month (Int64)

### Relationships
- Sales[CustomerKey] -> Customer[CustomerKey]
- Sales[ProductKey] -> Product[ProductKey]
- Sales[StoreKey] -> Store[StoreKey]
- Sales[Order Date] -> 'Date'[Date]

### Important Notes
- Table names with special characters should be quoted: 'Date', 'Currency Exchange'
- The Date table is marked as a date table (Date[Date] is the key)
- Use 'Date'[Date] for time intelligence functions (SAMEPERIODLASTYEAR, DATESYTD, etc.)
