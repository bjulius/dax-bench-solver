"""
Bigfoot DAX Validator - Python Calculation Module
==================================================

This module calculates the "ground truth" answers for 10 complex DAX patterns
using the BFRO Bigfoot Sightings dataset. Use these results to verify that
your Power BI DAX measures are returning correct values.

Usage:
    from bigfoot_calculations import BigfootCalculator

    calc = BigfootCalculator("bfro_reports_geocoded.csv")
    print(calc.longest_streak())
    print(calc.missing_report_numbers())
    # ... etc
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Union, List, Tuple


class BigfootCalculator:
    """
    Calculator for verifying DAX measures against the Bigfoot sightings dataset.

    Each method corresponds to one of the 10 "Easy to See, Hard to DAX" patterns.
    """

    def __init__(self, filepath: str):
        """
        Load and preprocess the Bigfoot sightings data.

        Args:
            filepath: Path to bfro_reports_geocoded.csv
        """
        self.filepath = Path(filepath)
        self.df = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """Load and clean the dataset."""
        df = pd.read_csv(self.filepath)

        # Parse dates - handle various formats
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Clean up numeric columns
        numeric_cols = ['temperature_high', 'temperature_mid', 'temperature_low',
                       'humidity', 'moon_phase', 'cloud_cover', 'visibility',
                       'wind_speed', 'pressure', 'dew_point', 'uv_index',
                       'precip_intensity', 'precip_probability']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Extract date components
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['decade'] = (df['year'] // 10) * 10

        # Clean state names
        df['state'] = df['state'].str.strip()

        return df

    def get_filtered_data(self,
                          state: Optional[str] = None,
                          classification: Optional[str] = None,
                          year: Optional[int] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get a filtered subset of the data.

        Args:
            state: Filter to specific state (e.g., "Washington")
            classification: Filter to classification (e.g., "Class A")
            year: Filter to specific year
            start_date: Filter to dates >= this (YYYY-MM-DD)
            end_date: Filter to dates <= this (YYYY-MM-DD)

        Returns:
            Filtered DataFrame
        """
        df = self.df.copy()

        if state:
            df = df[df['state'] == state]
        if classification:
            df = df[df['classification'] == classification]
        if year:
            df = df[df['year'] == year]
        if start_date:
            df = df[df['date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['date'] <= pd.to_datetime(end_date)]

        return df

    # =========================================================================
    # CALCULATION 1: LONGEST CONSECUTIVE STREAK
    # =========================================================================
    def longest_streak(self, state: Optional[str] = None) -> dict:
        """
        Calculate the longest streak of consecutive days with sightings.

        This uses the "islands and gaps" pattern:
        1. Get unique dates with sightings
        2. Assign a rank to each date
        3. Subtract rank from date - consecutive dates will have same result
        4. Group by this "island ID" and count

        Args:
            state: Optional state filter

        Returns:
            Dict with streak length and date range
        """
        df = self.get_filtered_data(state=state)

        # Get unique dates with sightings
        dates = df['date'].dropna().dt.normalize().drop_duplicates().sort_values()

        if len(dates) == 0:
            return {"streak_length": 0, "start_date": None, "end_date": None}

        dates_df = pd.DataFrame({'date': dates}).reset_index(drop=True)
        dates_df['rank'] = range(len(dates_df))

        # Island detection: date minus rank gives same value for consecutive dates
        dates_df['island_id'] = dates_df['date'] - pd.to_timedelta(dates_df['rank'], unit='D')

        # Find size of each island
        island_sizes = dates_df.groupby('island_id').agg(
            streak_length=('date', 'count'),
            start_date=('date', 'min'),
            end_date=('date', 'max')
        ).reset_index()

        # Get the longest streak
        longest = island_sizes.loc[island_sizes['streak_length'].idxmax()]

        return {
            "streak_length": int(longest['streak_length']),
            "start_date": longest['start_date'].strftime('%Y-%m-%d'),
            "end_date": longest['end_date'].strftime('%Y-%m-%d'),
            "filter_applied": f"state={state}" if state else "none"
        }

    # =========================================================================
    # CALCULATION 2: MISSING REPORT NUMBERS (GAP DETECTION)
    # =========================================================================
    def missing_report_numbers(self,
                                min_num: Optional[int] = None,
                                max_num: Optional[int] = None) -> dict:
        """
        Find missing report numbers in the sequence.

        Args:
            min_num: Start of range to check (default: min in data)
            max_num: End of range to check (default: max in data)

        Returns:
            Dict with count of missing and list of missing numbers
        """
        numbers = self.df['number'].dropna().astype(int)

        if min_num is None:
            min_num = int(numbers.min())
        if max_num is None:
            max_num = int(numbers.max())

        expected = set(range(min_num, max_num + 1))
        actual = set(numbers)

        missing = sorted(expected - actual)

        return {
            "range_checked": f"{min_num} to {max_num}",
            "expected_count": len(expected),
            "actual_count": len(actual),
            "missing_count": len(missing),
            "missing_numbers": missing[:50] if len(missing) > 50 else missing,  # Truncate if too many
            "note": f"Showing first 50 of {len(missing)} missing" if len(missing) > 50 else None
        }

    # =========================================================================
    # CALCULATION 3: RUNNING DISTINCT COUNT
    # =========================================================================
    def cumulative_unique_counties(self,
                                    as_of_date: Optional[str] = None,
                                    by_year: bool = False) -> Union[dict, pd.DataFrame]:
        """
        Calculate cumulative unique counties over time.

        Args:
            as_of_date: Calculate up to this date (YYYY-MM-DD)
            by_year: If True, return cumulative count for each year

        Returns:
            Dict with count, or DataFrame with yearly progression
        """
        df = self.df.dropna(subset=['date', 'county']).sort_values('date')

        if by_year:
            # Calculate cumulative unique counties per year
            results = []
            seen_counties = set()

            for year in sorted(df['year'].dropna().unique()):
                year_counties = set(df[df['year'] == year]['county'].unique())
                seen_counties.update(year_counties)
                results.append({
                    'year': int(year),
                    'new_counties': len(year_counties - (seen_counties - year_counties)),
                    'cumulative_counties': len(seen_counties)
                })

            return pd.DataFrame(results)

        else:
            if as_of_date:
                df = df[df['date'] <= pd.to_datetime(as_of_date)]

            unique_counties = df['county'].nunique()

            return {
                "cumulative_unique_counties": unique_counties,
                "as_of_date": as_of_date if as_of_date else "all time",
                "total_sightings_included": len(df)
            }

    # =========================================================================
    # CALCULATION 4: PREVIOUS NON-BLANK (LAST KNOWN VALUE)
    # =========================================================================
    def last_known_temperature(self,
                                target_date: str,
                                temp_column: str = 'temperature_high') -> dict:
        """
        Get temperature for a date, or last known value if missing.

        Args:
            target_date: The date to check (YYYY-MM-DD)
            temp_column: Which temperature column to use

        Returns:
            Dict with temperature and source date
        """
        target = pd.to_datetime(target_date)
        df = self.df.dropna(subset=['date']).sort_values('date')

        # Check if we have data for the target date
        target_data = df[df['date'].dt.normalize() == target.normalize()]

        if len(target_data) > 0 and not target_data[temp_column].isna().all():
            temp = target_data[temp_column].mean()
            return {
                "temperature": round(temp, 2),
                "source_date": target_date,
                "note": "Direct value found"
            }

        # Find last known value before target date
        prior_data = df[df['date'] < target].dropna(subset=[temp_column])

        if len(prior_data) == 0:
            return {
                "temperature": None,
                "source_date": None,
                "note": "No prior temperature data available"
            }

        last_row = prior_data.iloc[-1]

        return {
            "temperature": round(last_row[temp_column], 2),
            "source_date": last_row['date'].strftime('%Y-%m-%d'),
            "note": f"Using last known value (target date had no data)"
        }

    # =========================================================================
    # CALCULATION 5: NTH HIGHEST STATE
    # =========================================================================
    def nth_highest_state(self, n: int = 3) -> dict:
        """
        Get the Nth highest state by sighting count.

        Args:
            n: Which rank to retrieve (1 = highest, 2 = second, etc.)

        Returns:
            Dict with state name, count, and full rankings
        """
        state_counts = self.df.groupby('state').size().sort_values(ascending=False)

        rankings = state_counts.reset_index()
        rankings.columns = ['state', 'sighting_count']
        rankings['rank'] = range(1, len(rankings) + 1)

        if n > len(rankings):
            return {
                "error": f"Only {len(rankings)} states in data, cannot get rank {n}"
            }

        nth_state = rankings.iloc[n - 1]

        return {
            "rank": n,
            "state": nth_state['state'],
            "sighting_count": int(nth_state['sighting_count']),
            "top_10": rankings.head(10).to_dict('records')
        }

    # =========================================================================
    # CALCULATION 6: PARETO (STATES FOR 80% OF SIGHTINGS)
    # =========================================================================
    def pareto_states(self, threshold: float = 0.80) -> dict:
        """
        Calculate how many states account for X% of sightings.

        Args:
            threshold: Percentage threshold (0.80 = 80%)

        Returns:
            Dict with count of states and the states themselves
        """
        total = len(self.df)
        state_counts = self.df.groupby('state').size().sort_values(ascending=False)

        cumulative = state_counts.cumsum()
        cumulative_pct = cumulative / total

        # Find first state where cumulative % >= threshold
        states_needed = (cumulative_pct >= threshold).idxmax()
        states_needed_idx = cumulative_pct.index.tolist().index(states_needed) + 1

        pareto_states = state_counts.head(states_needed_idx)

        return {
            "threshold": f"{threshold:.0%}",
            "states_needed": states_needed_idx,
            "total_states": len(state_counts),
            "states_list": pareto_states.index.tolist(),
            "cumulative_sightings": int(pareto_states.sum()),
            "cumulative_percentage": f"{pareto_states.sum() / total:.1%}",
            "detail": pareto_states.reset_index().rename(
                columns={0: 'sighting_count', 'index': 'state'}
            ).to_dict('records')
        }

    # =========================================================================
    # CALCULATION 7: YEAR-OVER-YEAR COMPARISON
    # =========================================================================
    def yoy_change(self, year: Optional[int] = None) -> Union[dict, pd.DataFrame]:
        """
        Calculate year-over-year change in sightings.

        Args:
            year: Specific year to compare to prior year. If None, returns all years.

        Returns:
            Dict for single year, or DataFrame with all years
        """
        yearly = self.df.groupby('year').size().reset_index(name='sightings')
        yearly = yearly.sort_values('year')
        yearly['prior_year'] = yearly['sightings'].shift(1)
        yearly['yoy_change'] = yearly['sightings'] - yearly['prior_year']
        yearly['yoy_pct_change'] = yearly['yoy_change'] / yearly['prior_year']

        if year:
            row = yearly[yearly['year'] == year]
            if len(row) == 0:
                return {"error": f"No data for year {year}"}

            row = row.iloc[0]
            return {
                "year": int(year),
                "sightings": int(row['sightings']),
                "prior_year_sightings": int(row['prior_year']) if pd.notna(row['prior_year']) else None,
                "yoy_change": int(row['yoy_change']) if pd.notna(row['yoy_change']) else None,
                "yoy_pct_change": f"{row['yoy_pct_change']:.1%}" if pd.notna(row['yoy_pct_change']) else None,
                "trend": "Up" if row['yoy_change'] > 0 else ("Down" if row['yoy_change'] < 0 else "Flat") if pd.notna(row['yoy_change']) else None
            }

        return yearly

    # =========================================================================
    # CALCULATION 8: CUMULATIVE WITH RESET BY PERIOD
    # =========================================================================
    def cumulative_reset_by_period(self,
                                    period: str = 'decade',
                                    state: Optional[str] = None) -> pd.DataFrame:
        """
        Calculate running total that resets at period boundaries.

        Args:
            period: 'decade' or 'year'
            state: Optional state filter

        Returns:
            DataFrame with cumulative values that reset each period
        """
        df = self.get_filtered_data(state=state)
        df = df.dropna(subset=['date']).sort_values('date')

        if period == 'decade':
            df['period'] = df['decade']
        elif period == 'year':
            df['period'] = df['year']
        else:
            raise ValueError(f"Unknown period: {period}")

        # Group by date and period, count sightings
        daily = df.groupby([df['date'].dt.normalize(), 'period']).size().reset_index(name='daily_count')
        daily.columns = ['date', 'period', 'daily_count']

        # Calculate cumulative within each period
        daily['cumulative'] = daily.groupby('period')['daily_count'].cumsum()

        # Add period summary
        period_summary = daily.groupby('period').agg(
            start_date=('date', 'min'),
            end_date=('date', 'max'),
            total_sightings=('daily_count', 'sum'),
            peak_cumulative=('cumulative', 'max')
        ).reset_index()

        return {
            "period_type": period,
            "filter_applied": f"state={state}" if state else "none",
            "summary": period_summary.to_dict('records'),
            "daily_detail_sample": daily.head(20).to_dict('records')
        }

    # =========================================================================
    # CALCULATION 9: FIRST DATE MEETING THRESHOLD
    # =========================================================================
    def date_of_nth_sighting(self,
                              threshold: int = 100,
                              state: Optional[str] = None) -> dict:
        """
        Find the date when cumulative sightings first reached a threshold.

        Args:
            threshold: The cumulative count to find (e.g., 100)
            state: Optional state filter

        Returns:
            Dict with the date and related info
        """
        df = self.get_filtered_data(state=state)
        df = df.dropna(subset=['date']).sort_values('date')

        if len(df) < threshold:
            return {
                "threshold": threshold,
                "filter_applied": f"state={state}" if state else "none",
                "date": None,
                "note": f"Total sightings ({len(df)}) is less than threshold ({threshold})"
            }

        # Calculate cumulative count
        daily = df.groupby(df['date'].dt.normalize()).size().reset_index(name='daily_count')
        daily.columns = ['date', 'daily_count']
        daily['cumulative'] = daily['daily_count'].cumsum()

        # Find first date >= threshold
        threshold_row = daily[daily['cumulative'] >= threshold].iloc[0]

        first_date = df['date'].min()
        threshold_date = threshold_row['date']
        days_to_threshold = (threshold_date - first_date).days

        return {
            "threshold": threshold,
            "filter_applied": f"state={state}" if state else "none",
            "first_sighting_date": first_date.strftime('%Y-%m-%d'),
            "threshold_reached_date": threshold_date.strftime('%Y-%m-%d'),
            "days_to_threshold": days_to_threshold,
            "cumulative_at_threshold": int(threshold_row['cumulative'])
        }

    # =========================================================================
    # CALCULATION 10: MEDIAN PER GROUP
    # =========================================================================
    def median_by_group(self,
                        group_by: str = 'classification',
                        value: str = 'annual_sightings') -> dict:
        """
        Calculate median of a metric grouped by category.

        Args:
            group_by: Column to group by ('classification', 'state', 'season')
            value: What to calculate median of ('annual_sightings', 'monthly_sightings')

        Returns:
            Dict with median values per group
        """
        df = self.df.dropna(subset=['date', group_by])

        if value == 'annual_sightings':
            # Calculate sightings per year per group
            grouped = df.groupby([group_by, 'year']).size().reset_index(name='count')
            medians = grouped.groupby(group_by)['count'].median()

        elif value == 'monthly_sightings':
            # Calculate sightings per month per group
            df['yearmonth'] = df['date'].dt.to_period('M')
            grouped = df.groupby([group_by, 'yearmonth']).size().reset_index(name='count')
            medians = grouped.groupby(group_by)['count'].median()

        else:
            raise ValueError(f"Unknown value type: {value}")

        return {
            "group_by": group_by,
            "value_calculated": f"median {value}",
            "results": medians.to_dict(),
            "overall_median": float(medians.median())
        }

    # =========================================================================
    # SUMMARY: RUN ALL CALCULATIONS
    # =========================================================================
    def run_all(self) -> dict:
        """Run all 10 calculations with default parameters and return results."""
        return {
            "1_longest_streak": self.longest_streak(),
            "2_missing_numbers": self.missing_report_numbers(),
            "3_cumulative_counties": self.cumulative_unique_counties(),
            "4_last_known_temp": self.last_known_temperature("2010-01-01"),
            "5_nth_highest_state": self.nth_highest_state(3),
            "6_pareto_80pct": self.pareto_states(0.80),
            "7_yoy_change": self.yoy_change(2010),
            "8_cumulative_by_decade": self.cumulative_reset_by_period('decade'),
            "9_date_of_100th": self.date_of_nth_sighting(100),
            "10_median_by_class": self.median_by_group('classification'),
            "metadata": {
                "total_records": len(self.df),
                "date_range": f"{self.df['date'].min()} to {self.df['date'].max()}",
                "unique_states": self.df['state'].nunique(),
                "unique_counties": self.df['county'].nunique()
            }
        }


# =============================================================================
# CLI INTERFACE
# =============================================================================
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Bigfoot DAX Validator")
    parser.add_argument("csv_path", help="Path to bfro_reports_geocoded.csv")
    parser.add_argument("--calculation", "-c",
                        choices=['streak', 'gaps', 'counties', 'temp', 'nth',
                                'pareto', 'yoy', 'cumulative', 'threshold', 'median', 'all'],
                        default='all',
                        help="Which calculation to run")
    parser.add_argument("--state", "-s", help="Filter by state")
    parser.add_argument("--year", "-y", type=int, help="Filter by year")
    parser.add_argument("--n", type=int, default=3, help="N for Nth highest")
    parser.add_argument("--threshold", "-t", type=float, default=0.80, help="Threshold for Pareto")

    args = parser.parse_args()

    calc = BigfootCalculator(args.csv_path)

    if args.calculation == 'all':
        result = calc.run_all()
    elif args.calculation == 'streak':
        result = calc.longest_streak(state=args.state)
    elif args.calculation == 'gaps':
        result = calc.missing_report_numbers()
    elif args.calculation == 'counties':
        result = calc.cumulative_unique_counties()
    elif args.calculation == 'temp':
        result = calc.last_known_temperature("2010-01-01")
    elif args.calculation == 'nth':
        result = calc.nth_highest_state(args.n)
    elif args.calculation == 'pareto':
        result = calc.pareto_states(args.threshold)
    elif args.calculation == 'yoy':
        result = calc.yoy_change(args.year)
    elif args.calculation == 'cumulative':
        result = calc.cumulative_reset_by_period('decade', state=args.state)
    elif args.calculation == 'threshold':
        result = calc.date_of_nth_sighting(100, state=args.state)
    elif args.calculation == 'median':
        result = calc.median_by_group('classification')

    print(json.dumps(result, indent=2, default=str))
