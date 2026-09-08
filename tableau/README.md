# Tableau workbook

## Deliverable

- Workbook: `IPL_Performance_Analytics.twbx`
- Dashboard object: `IPL Performance Dashboard`
- Visible title: `IPL Performance Analytics Dashboard`
- Tableau build recorded in the package: Tableau Public 2025.3.1

Open the `.twbx` directly in Tableau Public or Tableau Desktop. It contains packaged Hyper extracts, so its saved views do not require the project CSVs merely to render. Refreshing the original text connections on another computer may require relinking the files under `data/processed/`.

## Worksheets

1. `KPI - Total Matches`
2. `KPI - Total Runs`
3. `KPI - Total Teams`
4. `KPI - Total Seasons`
5. `KPI - Total Wickets`
6. `Wins by Team`
7. `Matches by Season`
8. `Top 10 Batters`
9. `Top 10 Bowlers`

## Data sources

Three active worksheet data sources and embedded extracts were verified:

- Match summary
- Batting summary
- Bowling summary

The workbook metadata also references innings and team-season CSVs, but they are not active worksheet sources.

## Season interaction

Four on-select actions originate from `Matches by Season`. Selecting a season updates Total Matches, Total Runs, Total Wickets, Wins by Team, Top 10 Batters, and Top 10 Bowlers. Total Teams and Total Seasons remain overall context cards. The interaction was manually tested by the workbook author.

## Validation notes

- The packaged workbook contains one valid `.twb` and three valid Hyper extracts.
- Its SHA-256 is `2f5b26750ca1559676f48c139003db233f85b0788c773d71741d837b33272073`.
- The actual fixed dashboard size is 1000 × 800.
- The workbook was saved with a 2021 action-filter state; use Clear/Revert to return to overall totals.
- Total Wickets uses all recorded wicket events (`match_wickets`, 12,950 overall). Bowler-credit wickets total 11,815 and are used for bowler analysis.
- No Tableau calculated fields or parameters were found in the packaged workbook XML; the dashboard uses native aggregations and generated action filters.

See [`../docs/tableau_workbook_validation.md`](../docs/tableau_workbook_validation.md) for the complete read-only verification report. Do not regenerate or overwrite the workbook during documentation or portfolio updates.
