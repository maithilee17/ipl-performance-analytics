# Tableau workbook verification

## Verification scope

The existing `tableau/IPL_Performance_Analytics.twbx` was inspected read-only after manual completion in Tableau Desktop/Public. The package, embedded workbook XML, worksheet inventory, dashboard structure, data-source metadata, actions, formatting tokens, and KPI field encodings were verified. The workbook was not opened for editing, recreated, renamed, or overwritten.

## Package integrity

| Check | Actual result | Status |
|---|---|---|
| Target packaged workbook exists | Yes; 256,275 bytes | PASS |
| ZIP/package CRC test | No corrupt member | PASS |
| Embedded Tableau workbook | Exactly one `.twb` | PASS |
| Embedded extracts | Three `.hyper` files | PASS |
| Embedded workbook XML | Parsed successfully | PASS |
| Tableau source build | Tableau Public 2025.3.1 | PASS |
| SHA-256 | `2f5b26750ca1559676f48c139003db233f85b0788c773d71741d837b33272073` | RECORDED |

## Workbook inventory

The workbook contains one dashboard named `IPL Performance Dashboard` and exactly nine worksheets:

1. `KPI - Total Matches`
2. `KPI - Total Runs`
3. `KPI - Total Seasons`
4. `KPI - Total Teams`
5. `KPI - Total Wickets`
6. `Matches by Season`
7. `Top 10 Batters`
8. `Top 10 Bowlers`
9. `Wins by Team`

All nine sheets appear as dashboard zones. The KPI worksheets occupy the aligned top row, followed by Wins by Team, Matches by Season, and the two player ranking views.

## Data sources

Three active Tableau datasource definitions and three packaged extracts were verified:

- `match_summary.csv (Multiple Connections)` — active worksheet relation uses `match_summary.csv`.
- `batting_summary` — active relation uses `batting_summary.csv`.
- `bowling_summary` — active relation uses `bowling_summary.csv`.

The workbook connection metadata also references `innings_summary.csv` and `team_season_summary.csv`, but neither appears as an active worksheet datasource or its own embedded extract. All five expected CSV filenames are present in connection metadata. Because extracts are packaged, the workbook is not dependent on live CSV access merely to render its saved views; refreshing original text connections on another machine may still require relinking.

## Worksheet measures and filters

| Worksheet | Verified encoding |
|---|---|
| KPI - Total Matches | `COUNTD(match_id)` |
| KPI - Total Runs | `SUM(match_total_runs)` |
| KPI - Total Seasons | `COUNTD(season_label)` |
| KPI - Total Teams | `COUNTD(team1)` |
| KPI - Total Wickets | `SUM(match_wickets)` |
| Matches by Season | `COUNT(match_id)` by `season_label`, line mark |
| Wins by Team | `COUNT(match_id)` by `winning_team` |
| Top 10 Batters | `SUM(runs)` by batter, Top 10 filter |
| Top 10 Bowlers | `SUM(wickets)` by bowler, Top 10 filter |

Four on-select filter actions originate from `Matches by Season`. Their targets include the match KPI cards, Wins by Team, Top 10 Batters, and Top 10 Bowlers. The packaged XML therefore supports the documented season-selection workflow structurally. Runtime clicking was manually tested by the workbook author; it was not replayed during this file-only verification.

No Tableau calculated-field definitions and no parameters are stored in the workbook XML. The completed dashboard relies on native aggregations and generated action filters.

## Titles and formatting

| Check | Actual result | Status |
|---|---|---|
| Dashboard object | `IPL Performance Dashboard` | PASS |
| Visible title text | `IPL Performance Analytics Dashboard` | PASS |
| Subtitle | `Team, Player & Season Performance Analysis \| 2007–2024` | PASS |
| Font token | `Berlin Sans FB` occurs 24 times | PASS |
| Dashboard sizing | Fixed 1000 × 800 | WARN |

The verified fixed size differs from the earlier 1366 × 768 design specification. It is documented rather than changed because Phase 9 is verification-only.

## KPI reconciliation

The source columns underlying four KPI cards reconcile with the project anchors when unfiltered:

- Total Matches: 1,095
- Total Runs: 347,756
- Total Teams using `COUNTD(team1)`: 15 in the full dataset
- Total Seasons: 17

`KPI - Total Wickets` uses `SUM(match_wickets)`, which counts all recorded wicket events and totals 12,950. The project’s bowler-credit wicket anchor is 11,815 and corresponds to `SUM(match_bowler_wickets)`. This is a documented analytical warning; the workbook was not changed.

The saved XML retains a 2021 action-filter member on the affected worksheets, consistent with the manual season-interaction test before saving. In that saved context the source contains 60 matches, 18,637 runs, 717 all-dismissal wickets, 670 bowler-credit wickets, eight `team1` values, and one selected season. Clear the selection/Revert in Tableau to display overall values.

## Validation summary

| Category | Status |
|---|---|
| Packaged workbook exists and is readable | PASS |
| Expected nine worksheets | PASS |
| Expected dashboard | PASS |
| Expected title, subtitle, and font tokens | PASS |
| Season filter-action definitions | PASS |
| Five expected CSV filenames referenced | PASS |
| Active packaged data sources | PASS — three active extracts |
| Calculated fields | NONE FOUND |
| Parameters | NONE FOUND |
| Earlier 1366 × 768 size | WARN — actual fixed size is 1000 × 800 |
| Bowler-credit wicket KPI anchor | WARN — sheet uses all wicket events |
| Live UI interaction replay | NOT PERFORMED — manually confirmed by user |

## Final status

Phase 9 is complete for the manually produced deliverable: the intended `.twbx` exists, passes package integrity checks, and contains the expected dashboard and nine worksheets. The two analytical/layout differences above remain documented limitations and were not silently modified.
