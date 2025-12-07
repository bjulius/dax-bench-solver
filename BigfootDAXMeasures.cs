// ============================================================================
// BIGFOOT DAX MEASURES - Tabular Editor Import Script
// ============================================================================
//
// HOW TO USE:
// 1. Open your Power BI model in Tabular Editor (free: https://tabulareditor.com)
// 2. Go to Advanced Scripting tab (C# Scripts)
// 3. Paste this entire script
// 4. Press F5 or click Run
// 5. All measures will be created in a "Bigfoot Measures" folder
//
// PREREQUISITES:
// - Table named "bfro_reports" with your Bigfoot sighting data
// - Table named "DateTable" with the date dimension
// - Relationship: DateTable[Date] -> bfro_reports[date]
//
// ============================================================================

// Create a display folder for organization
var folderName = "Bigfoot Measures";

// Helper: Get or create the measures table
var measuresTableName = "_Measures";
Table measuresTable;

if (!Model.Tables.Contains(measuresTableName)) {
    measuresTable = Model.AddCalculatedTable(measuresTableName, "ROW(\"Dummy\", 1)");
    measuresTable.Description = "Container table for measures. The dummy column can be hidden.";
    measuresTable.Columns["Dummy"].IsHidden = true;
} else {
    measuresTable = Model.Tables[measuresTableName];
}

// ============================================================================
// MEASURE 1: CONSECUTIVE STREAK - Days with Sightings
// ============================================================================
// "What's the longest streak of consecutive days with at least one sighting?"
//
// WHY IT'S HARD: DAX has no "previous row" concept. We must:
// 1. Create islands of consecutive dates using ranking gaps
// 2. Group sightings into these islands
// 3. Find the maximum island size
// ============================================================================

var m1 = measuresTable.AddMeasure(
    "Longest Sighting Streak (Days)",
    @"
// Longest consecutive days with at least one Bigfoot sighting
VAR SightingDates =
    SUMMARIZE(
        bfro_reports,
        bfro_reports[date]
    )

VAR DatesWithRank =
    ADDCOLUMNS(
        SightingDates,
        ""DateRank"", RANKX(SightingDates, bfro_reports[date], , ASC, DENSE)
    )

VAR DatesWithIsland =
    ADDCOLUMNS(
        DatesWithRank,
        ""IslandID"",
        bfro_reports[date] - [DateRank]  // Consecutive dates will have same IslandID
    )

VAR IslandSizes =
    GROUPBY(
        DatesWithIsland,
        [IslandID],
        ""StreakLength"", COUNTX(CURRENTGROUP(), 1)
    )

RETURN
    MAXX(IslandSizes, [StreakLength])
"
);
m1.DisplayFolder = folderName;
m1.Description = "Finds the longest streak of consecutive calendar days that had at least one Bigfoot sighting. Uses the 'islands and gaps' pattern with ranking differences.";


// ============================================================================
// MEASURE 2: GAP DETECTION - Missing Report Numbers
// ============================================================================
// "Are there any missing report numbers in the current selection?"
//
// WHY IT'S HARD: DAX cannot generate a sequence of "expected" values.
// We use GENERATESERIES to create the expected range, then count mismatches.
// ============================================================================

var m2 = measuresTable.AddMeasure(
    "Missing Report Numbers Count",
    @"
// Count of missing report numbers in the current filter context
VAR MinReport = MIN(bfro_reports[number])
VAR MaxReport = MAX(bfro_reports[number])

VAR ExpectedNumbers =
    GENERATESERIES(MinReport, MaxReport, 1)

VAR ActualNumbers =
    DISTINCT(bfro_reports[number])

VAR MissingCount =
    COUNTROWS(ExpectedNumbers) - COUNTROWS(ActualNumbers)

RETURN
    IF(
        ISBLANK(MinReport) || ISBLANK(MaxReport),
        BLANK(),
        MissingCount
    )
"
);
m2.DisplayFolder = folderName;
m2.Description = "Counts how many report numbers are missing between the minimum and maximum report number in the current filter context.";


// ============================================================================
// MEASURE 3: RUNNING DISTINCT COUNT - Cumulative Unique Counties
// ============================================================================
// "How many unique counties have reported sightings up to this date?"
//
// WHY IT'S HARD: DISTINCTCOUNT only counts in current context.
// We need nested CALCULATE with an expanding date filter.
// ============================================================================

var m3 = measuresTable.AddMeasure(
    "Cumulative Unique Counties",
    @"
// Running distinct count of counties with sightings up to the current date
VAR CurrentDate = MAX(DateTable[Date])

RETURN
    CALCULATE(
        DISTINCTCOUNT(bfro_reports[county]),
        FILTER(
            ALL(DateTable),
            DateTable[Date] <= CurrentDate
        ),
        REMOVEFILTERS(bfro_reports[county])
    )
"
);
m3.DisplayFolder = folderName;
m3.Description = "Shows the cumulative count of unique counties that have had at least one Bigfoot sighting up to the selected date. Requires expanding filter context.";


// ============================================================================
// MEASURE 4: PREVIOUS NON-BLANK - Last Known Temperature
// ============================================================================
// "If temperature is missing, show the last recorded temperature."
//
// WHY IT'S HARD: DAX doesn't 'look backwards' naturally. We must:
// 1. Find all dates with non-blank values
// 2. Get the maximum date <= current date
// 3. Retrieve that date's value
// ============================================================================

var m4 = measuresTable.AddMeasure(
    "Temperature (Last Known)",
    @"
// Shows current temperature_high, or last known value if blank
VAR CurrentDate = MAX(DateTable[Date])
VAR CurrentTemp = AVERAGE(bfro_reports[temperature_high])

VAR LastKnownDate =
    CALCULATE(
        MAX(bfro_reports[date]),
        FILTER(
            ALL(bfro_reports),
            bfro_reports[date] <= CurrentDate &&
            NOT(ISBLANK(bfro_reports[temperature_high]))
        )
    )

VAR LastKnownTemp =
    CALCULATE(
        AVERAGE(bfro_reports[temperature_high]),
        REMOVEFILTERS(DateTable),
        bfro_reports[date] = LastKnownDate
    )

RETURN
    IF(
        NOT(ISBLANK(CurrentTemp)),
        CurrentTemp,
        LastKnownTemp
    )
"
);
m4.DisplayFolder = folderName;
m4.Description = "Returns the average high temperature for sightings on the current date. If no temperature data exists, returns the last known temperature from a previous date.";


// ============================================================================
// MEASURE 5: NTH HIGHEST - State with Nth Most Sightings
// ============================================================================
// "Which state has the 3rd most sightings?"
//
// WHY IT'S HARD: Can't simply index into a sorted list.
// Must use TOPN + MIN or ranking with specific position retrieval.
// ============================================================================

var m5 = measuresTable.AddMeasure(
    "Nth Highest State Sightings",
    @"
// Returns the sighting count for the Nth ranked state
// Change the RankPosition variable to get different ranks
VAR RankPosition = 3  // Change this to 1, 2, 3, etc.

VAR StateRankings =
    ADDCOLUMNS(
        SUMMARIZE(
            ALL(bfro_reports),
            bfro_reports[state]
        ),
        ""SightingCount"", CALCULATE(COUNTROWS(bfro_reports))
    )

VAR RankedStates =
    ADDCOLUMNS(
        StateRankings,
        ""StateRank"", RANKX(StateRankings, [SightingCount], , DESC, DENSE)
    )

VAR NthValue =
    MAXX(
        FILTER(RankedStates, [StateRank] = RankPosition),
        [SightingCount]
    )

RETURN
    NthValue
"
);
m5.DisplayFolder = folderName;
m5.Description = "Returns the sighting count for the Nth ranked state. Modify the RankPosition variable to change which rank to display.";

var m5b = measuresTable.AddMeasure(
    "Nth Highest State Name",
    @"
// Returns the NAME of the Nth ranked state
// Change the RankPosition variable to get different ranks
VAR RankPosition = 3  // Change this to 1, 2, 3, etc.

VAR StateRankings =
    ADDCOLUMNS(
        SUMMARIZE(
            ALL(bfro_reports),
            bfro_reports[state]
        ),
        ""SightingCount"", CALCULATE(COUNTROWS(bfro_reports))
    )

VAR RankedStates =
    ADDCOLUMNS(
        StateRankings,
        ""StateRank"", RANKX(StateRankings, [SightingCount], , DESC, DENSE)
    )

VAR NthState =
    MAXX(
        FILTER(RankedStates, [StateRank] = RankPosition),
        bfro_reports[state]
    )

RETURN
    NthState
"
);
m5b.DisplayFolder = folderName;
m5b.Description = "Returns the name of the Nth ranked state by sighting count. Companion to 'Nth Highest State Sightings'.";


// ============================================================================
// MEASURE 6: PARETO 80% - States Making Up 80% of Sightings
// ============================================================================
// "How many states account for 80% of all sightings?"
//
// WHY IT'S HARD: Must calculate running percentage and find the cutoff.
// Requires nested iteration with cumulative calculations.
// ============================================================================

var m6 = measuresTable.AddMeasure(
    "States for 80% of Sightings",
    @"
// Count of states needed to reach 80% of total sightings
VAR TotalSightings = COUNTROWS(ALL(bfro_reports))

VAR StateRankings =
    ADDCOLUMNS(
        SUMMARIZE(
            ALL(bfro_reports),
            bfro_reports[state]
        ),
        ""SightingCount"", CALCULATE(COUNTROWS(bfro_reports)),
        ""Pct"", DIVIDE(CALCULATE(COUNTROWS(bfro_reports)), TotalSightings)
    )

VAR RankedStates =
    ADDCOLUMNS(
        StateRankings,
        ""StateRank"", RANKX(StateRankings, [SightingCount], , DESC, DENSE)
    )

VAR StatesWithCumulative =
    ADDCOLUMNS(
        RankedStates,
        ""CumulativePct"",
        SUMX(
            FILTER(RankedStates, [SightingCount] >= EARLIER([SightingCount])),
            [Pct]
        )
    )

VAR StatesNeeded =
    MINX(
        FILTER(StatesWithCumulative, [CumulativePct] >= 0.80),
        [StateRank]
    )

RETURN
    StatesNeeded
"
);
m6.DisplayFolder = folderName;
m6.Description = "Calculates how many states (ranked by sighting count) are needed to account for 80% of all Bigfoot sightings. Classic Pareto analysis.";


// ============================================================================
// MEASURE 7: PREVIOUS PERIOD COMPARISON - Year over Year Change
// ============================================================================
// "Did sightings increase or decrease compared to last year?"
//
// WHY IT'S HARD: No 'previous row' in DAX. Must use DATEADD or
// explicit year arithmetic to reference prior period.
// ============================================================================

var m7 = measuresTable.AddMeasure(
    "Sightings YoY Change",
    @"
// Year-over-Year change in sighting count
VAR CurrentYear = SELECTEDVALUE(DateTable[Year])
VAR CurrentCount = COUNTROWS(bfro_reports)

VAR PreviousCount =
    CALCULATE(
        COUNTROWS(bfro_reports),
        REMOVEFILTERS(DateTable),
        DateTable[Year] = CurrentYear - 1
    )

RETURN
    IF(
        ISBLANK(CurrentYear) || ISBLANK(PreviousCount),
        BLANK(),
        CurrentCount - PreviousCount
    )
"
);
m7.DisplayFolder = folderName;
m7.Description = "Calculates the difference in sighting count between the current year and the previous year.";

var m7b = measuresTable.AddMeasure(
    "Sightings YoY % Change",
    @"
// Year-over-Year percentage change in sighting count
VAR CurrentYear = SELECTEDVALUE(DateTable[Year])
VAR CurrentCount = COUNTROWS(bfro_reports)

VAR PreviousCount =
    CALCULATE(
        COUNTROWS(bfro_reports),
        REMOVEFILTERS(DateTable),
        DateTable[Year] = CurrentYear - 1
    )

RETURN
    IF(
        ISBLANK(CurrentYear) || ISBLANK(PreviousCount) || PreviousCount = 0,
        BLANK(),
        DIVIDE(CurrentCount - PreviousCount, PreviousCount)
    )
"
);
m7b.DisplayFolder = folderName;
m7b.FormatString = "0.0%";
m7b.Description = "Calculates the percentage change in sighting count compared to the previous year.";

var m7c = measuresTable.AddMeasure(
    "Sightings YoY Trend",
    @"
// Returns Up, Down, or Flat based on YoY comparison
VAR CurrentYear = SELECTEDVALUE(DateTable[Year])
VAR CurrentCount = COUNTROWS(bfro_reports)

VAR PreviousCount =
    CALCULATE(
        COUNTROWS(bfro_reports),
        REMOVEFILTERS(DateTable),
        DateTable[Year] = CurrentYear - 1
    )

VAR Change = CurrentCount - PreviousCount

RETURN
    IF(
        ISBLANK(CurrentYear) || ISBLANK(PreviousCount),
        BLANK(),
        SWITCH(
            TRUE(),
            Change > 0, "↑ Up",
            Change < 0, "↓ Down",
            "→ Flat"
        )
    )
"
);
m7c.DisplayFolder = folderName;
m7c.Description = "Returns a text indicator (Up/Down/Flat) comparing current year to previous year sightings.";


// ============================================================================
// MEASURE 8: RESET RUNNING TOTAL - Cumulative by Decade
// ============================================================================
// "Show cumulative sightings within each decade, resetting at decade boundary."
//
// WHY IT'S HARD: DAX has no persistent 'state'. Must filter to
// current decade AND dates up to current date in same calculation.
// ============================================================================

var m8 = measuresTable.AddMeasure(
    "Cumulative Sightings (Reset by Decade)",
    @"
// Running total of sightings within the current decade, resets each new decade
VAR CurrentDate = MAX(DateTable[Date])
VAR CurrentDecade = MAX(DateTable[Decade])

RETURN
    CALCULATE(
        COUNTROWS(bfro_reports),
        FILTER(
            ALL(DateTable),
            DateTable[Decade] = CurrentDecade &&
            DateTable[Date] <= CurrentDate
        )
    )
"
);
m8.DisplayFolder = folderName;
m8.Description = "Shows a running total of sightings that resets at the start of each decade (1970, 1980, 1990, etc.).";

var m8b = measuresTable.AddMeasure(
    "Cumulative Sightings (Reset by Year)",
    @"
// Running total of sightings within the current year, resets each January
VAR CurrentDate = MAX(DateTable[Date])
VAR CurrentYear = MAX(DateTable[Year])

RETURN
    CALCULATE(
        COUNTROWS(bfro_reports),
        FILTER(
            ALL(DateTable),
            DateTable[Year] = CurrentYear &&
            DateTable[Date] <= CurrentDate
        )
    )
"
);
m8b.DisplayFolder = folderName;
m8b.Description = "Shows a running total of sightings that resets at the start of each calendar year.";


// ============================================================================
// MEASURE 9: FIRST DATE MEETING CONDITION - When Did State Hit 100 Sightings?
// ============================================================================
// "On what date did Washington state reach 100 cumulative sightings?"
//
// WHY IT'S HARD: Must calculate running total for EVERY date,
// then find the MINIMUM date where that total >= threshold.
// ============================================================================

var m9 = measuresTable.AddMeasure(
    "Date of 100th Sighting",
    @"
// Returns the date when cumulative sightings first reached 100
// Works within current filter context (e.g., filtered to a specific state)
VAR Threshold = 100

VAR DatesWithCumulative =
    ADDCOLUMNS(
        VALUES(DateTable[Date]),
        ""CumulativeCount"",
        VAR ThisDate = [Date]
        RETURN
            CALCULATE(
                COUNTROWS(bfro_reports),
                DateTable[Date] <= ThisDate,
                REMOVEFILTERS(DateTable[Date])
            )
    )

VAR FirstDateOverThreshold =
    MINX(
        FILTER(DatesWithCumulative, [CumulativeCount] >= Threshold),
        [Date]
    )

RETURN
    FirstDateOverThreshold
"
);
m9.DisplayFolder = folderName;
m9.FormatString = "yyyy-mm-dd";
m9.Description = "Returns the first date when cumulative sightings reached 100. Use with a state filter to see when each state hit the milestone.";

var m9b = measuresTable.AddMeasure(
    "Days to 100th Sighting",
    @"
// Returns how many days from first sighting to 100th sighting
VAR Threshold = 100

VAR DatesWithCumulative =
    ADDCOLUMNS(
        VALUES(DateTable[Date]),
        ""CumulativeCount"",
        VAR ThisDate = [Date]
        RETURN
            CALCULATE(
                COUNTROWS(bfro_reports),
                DateTable[Date] <= ThisDate,
                REMOVEFILTERS(DateTable[Date])
            )
    )

VAR FirstDate = MINX(bfro_reports, bfro_reports[date])

VAR FirstDateOverThreshold =
    MINX(
        FILTER(DatesWithCumulative, [CumulativeCount] >= Threshold),
        [Date]
    )

RETURN
    IF(
        ISBLANK(FirstDateOverThreshold),
        BLANK(),
        DATEDIFF(FirstDate, FirstDateOverThreshold, DAY)
    )
"
);
m9b.DisplayFolder = folderName;
m9b.Description = "Calculates the number of days between the first sighting and the 100th sighting in the current filter context.";


// ============================================================================
// MEASURE 10: MEDIAN PER GROUP - Median Annual Sightings by Classification
// ============================================================================
// "What is the median number of sightings per year for Class A reports?"
//
// WHY IT'S HARD: MEDIANX exists but behaves unexpectedly in matrix visuals.
// Must explicitly control the granularity of what we're taking the median OF.
// ============================================================================

var m10 = measuresTable.AddMeasure(
    "Median Annual Sightings",
    @"
// Median number of sightings per year (within current filter context)
VAR YearlyCounts =
    ADDCOLUMNS(
        VALUES(DateTable[Year]),
        ""YearCount"", CALCULATE(COUNTROWS(bfro_reports))
    )

RETURN
    MEDIANX(YearlyCounts, [YearCount])
"
);
m10.DisplayFolder = folderName;
m10.Description = "Calculates the median number of sightings per year. Use with Classification slicer to compare median activity across sighting types.";

var m10b = measuresTable.AddMeasure(
    "Median Monthly Sightings",
    @"
// Median number of sightings per month (within current filter context)
VAR MonthlyCounts =
    ADDCOLUMNS(
        SUMMARIZE(DateTable, DateTable[Year], DateTable[Month]),
        ""MonthCount"", CALCULATE(COUNTROWS(bfro_reports))
    )

VAR NonZeroMonths =
    FILTER(MonthlyCounts, [MonthCount] > 0)

RETURN
    MEDIANX(NonZeroMonths, [MonthCount])
"
);
m10b.DisplayFolder = folderName;
m10b.Description = "Calculates the median number of sightings per month, excluding months with zero sightings.";


// ============================================================================
// BONUS MEASURES - Useful Supporting Calculations
// ============================================================================

var mBonus1 = measuresTable.AddMeasure(
    "Total Sightings",
    @"COUNTROWS(bfro_reports)"
);
mBonus1.DisplayFolder = folderName + "\\Basic";
mBonus1.Description = "Simple count of all sightings in current filter context.";

var mBonus2 = measuresTable.AddMeasure(
    "Unique States",
    @"DISTINCTCOUNT(bfro_reports[state])"
);
mBonus2.DisplayFolder = folderName + "\\Basic";
mBonus2.Description = "Count of unique states with sightings in current filter context.";

var mBonus3 = measuresTable.AddMeasure(
    "Unique Counties",
    @"DISTINCTCOUNT(bfro_reports[county])"
);
mBonus3.DisplayFolder = folderName + "\\Basic";
mBonus3.Description = "Count of unique counties with sightings in current filter context.";

var mBonus4 = measuresTable.AddMeasure(
    "Class A Sightings",
    @"CALCULATE(COUNTROWS(bfro_reports), bfro_reports[classification] = ""Class A"")"
);
mBonus4.DisplayFolder = folderName + "\\Basic";
mBonus4.Description = "Count of Class A (direct visual) sightings.";

var mBonus5 = measuresTable.AddMeasure(
    "Class A %",
    @"
DIVIDE(
    CALCULATE(COUNTROWS(bfro_reports), bfro_reports[classification] = ""Class A""),
    COUNTROWS(bfro_reports)
)
"
);
mBonus5.DisplayFolder = folderName + "\\Basic";
mBonus5.FormatString = "0.0%";
mBonus5.Description = "Percentage of sightings that are Class A (direct visual encounters).";

var mBonus6 = measuresTable.AddMeasure(
    "Avg Moon Phase",
    @"AVERAGE(bfro_reports[moon_phase])"
);
mBonus6.DisplayFolder = folderName + "\\Basic";
mBonus6.FormatString = "0.00";
mBonus6.Description = "Average moon phase during sightings (0 = new moon, 0.5 = full moon, 1 = new moon again).";

var mBonus7 = measuresTable.AddMeasure(
    "Full Moon Sightings %",
    @"
// Percentage of sightings occurring during full moon (phase 0.45-0.55)
DIVIDE(
    CALCULATE(
        COUNTROWS(bfro_reports),
        bfro_reports[moon_phase] >= 0.45 && bfro_reports[moon_phase] <= 0.55
    ),
    COUNTROWS(bfro_reports)
)
"
);
mBonus7.DisplayFolder = folderName + "\\Basic";
mBonus7.FormatString = "0.0%";
mBonus7.Description = "Percentage of sightings that occurred during a full moon (phase between 0.45 and 0.55).";


// ============================================================================
// SCRIPT COMPLETE
// ============================================================================
//
// Summary of measures created:
//
// MAIN MEASURES (10 Difficult DAX Patterns):
// 1. Longest Sighting Streak (Days)      - Consecutive streak detection
// 2. Missing Report Numbers Count        - Gap detection in sequences
// 3. Cumulative Unique Counties          - Running distinct count
// 4. Temperature (Last Known)            - Previous non-blank value
// 5. Nth Highest State Sightings/Name    - Nth ranking retrieval
// 6. States for 80% of Sightings         - Pareto analysis
// 7. Sightings YoY Change/% /Trend       - Previous period comparison
// 8. Cumulative Sightings (Reset by...)  - Running total with reset
// 9. Date of 100th Sighting              - First date meeting condition
// 10. Median Annual/Monthly Sightings    - Median per group
//
// BONUS MEASURES (7 Supporting Calculations):
// - Total Sightings, Unique States, Unique Counties
// - Class A Sightings, Class A %
// - Avg Moon Phase, Full Moon Sightings %
//
// Total: 20 measures created
// ============================================================================

"Measures created successfully! Check the '_Measures' table.";
