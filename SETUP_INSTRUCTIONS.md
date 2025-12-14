# BigfootDAX Power BI Setup Instructions

## Quick Start Guide

### Step 1: Open Power BI Desktop
Launch Power BI Desktop (not the web version)

### Step 2: Import the Main Data File
1. Click **Home > Get Data > Text/CSV**
2. Navigate to: `C:\Users\brjul\OneDrive\Documents\Projects\BigfootDAX\`
3. Select: `bfro_reports_geocoded.csv`
4. Click **Load**

### Step 3: Rename the Table
1. In the Data pane, right-click the imported table
2. Rename it to: `bfro_reports`
   (This name is required for the DAX measures to work!)

### Step 4: Create the Date Table
1. Go to **Modeling > New Table**
2. Open `DateTable_DAX.txt` in this folder
3. Copy the DAX formula and paste it
4. Press Enter to create the table

### Step 5: Mark as Date Table
1. Select the DateTable
2. Go to **Table tools > Mark as date table**
3. Choose the "Date" column

### Step 6: Create Relationship
1. Go to **Model view** (left sidebar)
2. Drag `DateTable[Date]` to `bfro_reports[date]`
3. Verify it's a one-to-many relationship

### Step 7: Save Your File
Save as: `BigfootDAX.pbix` in this project folder

---

## Adding DAX Measures

### Option A: Use Power BI MCP Server (Recommended)
With your .pbix file open, ask Claude:
- "List my Power BI models"
- "Connect to model 1"
- "Create a measure called 'Total Sightings' with formula COUNTROWS(bfro_reports)"

### Option B: Manual Copy/Paste
Open `BigfootDAXMeasures_CopyPaste.txt` and copy measures one by one.

### Option C: Tabular Editor Script
If you have Tabular Editor installed, use `BigfootDAXMeasures.cs` to bulk import all measures.

---

## Data Overview

### bfro_reports table columns:
| Column | Description |
|--------|-------------|
| observed | Detailed sighting description |
| location_details | Specific location info |
| county | County name |
| state | State name |
| title | Report title |
| latitude | GPS latitude |
| longitude | GPS longitude |
| date | Sighting date |
| number | Report number |
| classification | Class A, B, or C |
| temperature_high | High temperature |
| moon_phase | Moon phase (0-1) |
| humidity | Humidity percentage |
| ... | Weather and other fields |

### DateTable columns (auto-generated):
- Date, Year, Month, MonthName, Quarter
- Day, DayOfWeek, DayName, WeekNum
- YearMonth, Decade, Season

---

## Included DAX Measures (20 total)

### Advanced Patterns:
1. **Longest Sighting Streak** - Consecutive days detection
2. **Missing Report Numbers Count** - Gap detection
3. **Cumulative Unique Counties** - Running distinct count
4. **Temperature (Last Known)** - Previous non-blank value
5. **Nth Highest State Sightings** - Ranking queries
6. **States for 80% of Sightings** - Pareto analysis
7. **Sightings YoY Change** - Period comparison
8. **Cumulative Sightings (Reset)** - Running totals with reset
9. **Date of 100th Sighting** - Threshold detection
10. **Median Annual Sightings** - Median per group

### Basic Measures:
- Total Sightings
- Unique States / Counties
- Class A Sightings & %
- Full Moon Sightings %
- And more...

---

## Troubleshooting

**Measures show errors?**
- Ensure table is named exactly `bfro_reports`
- Verify DateTable relationship exists
- Check that date column has no blanks

**MCP Server not connecting?**
- Ensure Power BI Desktop is open with a file loaded
- Restart Claude Code after adding MCP server
