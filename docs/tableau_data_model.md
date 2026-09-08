# Tableau data model and dashboard design

## Phase 8 scope and implementation status

Phase 8 defines and validates the Tableau analytical layer before workbook construction. Tableau Public 2025.3 is installed, but native Tableau UI control is not available in the current automation environment. No `.twb`, `.twbx`, or Tableau extract was created. The specification below is the implementation contract for Phase 9.

The five Phase 6 CSVs remain the Tableau sources. They are small, portable, Tableau Public-compatible, and already validated, so a `.hyper` extract would add refresh complexity without a material benefit. The SQLite database remains the SQL portfolio artifact and reconciliation reference; it is not required by the workbook.

## Data-source strategy

Use five separately named Tableau data sources. Do not physically join them into a single table.

| Tableau source name | File | Grain | Rows | Primary use |
|---|---|---|---:|---|
| `IPL Matches` | `data/processed/match_summary.csv` | One row per `match_id` | 1,095 | Overview, match outcomes, toss analysis |
| `IPL Innings` | `data/processed/innings_summary.csv` | One row per `match_id + inning` | 2,217 | Innings scoring and run rate |
| `IPL Team Season` | `data/processed/team_season_summary.csv` | One row per `season + team` | 146 | Team performance and team KPI sheets |
| `IPL Batting` | `data/processed/batting_summary.csv` | One row per `season + batter` | 2,617 | Batting dashboard |
| `IPL Bowling` | `data/processed/bowling_summary.csv` | One row per `season + bowler` | 1,948 | Bowling dashboard |

### Relationship policy

- Keep `IPL Team Season`, `IPL Batting`, and `IPL Bowling` separate. Relating them on season would create many-to-many paths and could duplicate measures.
- Keep `IPL Matches` and `IPL Innings` separate for the initial workbook. Each required sheet can be answered at its native grain.
- If a later worksheet genuinely needs match attributes and innings measures together, create a dedicated logical data source with a Tableau relationship from `match_summary.match_id` (one) to `innings_summary.match_id` (many). Set referential integrity to “all innings have a match.” Never use a physical join.
- Do not sum match-level measures in a view that also uses innings-level dimensions; a match total could repeat once per innings.
- Cross-source dashboard coordination uses parameters and targeted actions, not cross-database joins or data blending.

## Tableau field roles and types

| Source | Dimensions | Measures | Required type corrections |
|---|---|---|---|
| IPL Matches | match ID, season, date, city, venue, teams, toss fields, result, stage | margins, delivery/run/wicket/boundary totals | `match_date` = Date; `match_id` = Number (whole)/Dimension; boolean fields = Boolean |
| IPL Innings | match ID, season, inning, batting team, bowling team | deliveries, legal balls, runs, wickets, boundaries, run rate | `match_id` and `inning` = Number (whole)/Dimension |
| IPL Team Season | season, team | matches, outcomes, runs, wickets, toss totals and rates | season = String/Dimension |
| IPL Batting | season, batter | matches, runs, balls, boundaries, dismissals and rates | season and batter = Dimension |
| IPL Bowling | season, bowler | matches, legal balls, overs, runs, wickets, economy, dots, extras | season and bowler = Dimension |

Preserve season labels as strings so `2007/08`, `2009/10`, and `2020/21` are not silently converted. Sort season labels with an explicit manual order based on their four-digit starting year.

## Validated source fields versus Tableau calculations

Row-grain fields such as `run_rate`, `win_percentage`, `strike_rate`, `economy_rate`, `boundary_runs`, and dot-ball percentages already exist. Use them in row-level tables and tooltips. When multiple seasons or players are aggregated, do not average those percentages: recompute the weighted metric from additive numerators and denominators.

### Required calculated fields

Create each calculation only in the named source.

**IPL Team Season — `Win % (Weighted)`**

```tableau
IF SUM([decided_matches]) = 0 THEN NULL
ELSE 100.0 * SUM([wins]) / SUM([decided_matches])
END
```

**IPL Team Season — `Toss Win % (Weighted)`**

```tableau
IF SUM([matches_played]) = 0 THEN NULL
ELSE 100.0 * SUM([toss_wins]) / SUM([matches_played])
END
```

**IPL Team Season — `Toss-to-Match Win % (Weighted)`**

```tableau
IF SUM([toss_decided_matches]) = 0 THEN NULL
ELSE 100.0 * SUM([toss_match_wins]) / SUM([toss_decided_matches])
END
```

**IPL Team Season — `Runs per Match`**

```tableau
IF SUM([matches_played]) = 0 THEN NULL
ELSE SUM([total_runs_scored]) / SUM([matches_played])
END
```

**IPL Team Season — `Wickets per Match`**

```tableau
IF SUM([matches_played]) = 0 THEN NULL
ELSE SUM([total_wickets_taken]) / SUM([matches_played])
END
```

**IPL Innings — `Run Rate (Weighted)`**

```tableau
IF SUM([legal_balls]) = 0 THEN NULL
ELSE 6.0 * SUM([total_runs]) / SUM([legal_balls])
END
```

**IPL Batting — `Strike Rate (Weighted)`**

```tableau
IF SUM([balls_faced]) = 0 THEN NULL
ELSE 100.0 * SUM([runs]) / SUM([balls_faced])
END
```

**IPL Batting — `Batting Average (Weighted)`**

```tableau
IF SUM([dismissals]) = 0 THEN NULL
ELSE SUM([runs]) / SUM([dismissals])
END
```

**IPL Batting — `Boundary % (Weighted)`**

```tableau
IF SUM([runs]) = 0 THEN NULL
ELSE 100.0 * SUM([boundary_runs]) / SUM([runs])
END
```

Use `SUM([boundary_runs])` directly; it is already validated as `fours × 4 + sixes × 6`.

**IPL Bowling — `Economy (Weighted)`**

```tableau
IF SUM([legal_balls]) = 0 THEN NULL
ELSE 6.0 * SUM([runs_conceded]) / SUM([legal_balls])
END
```

**IPL Bowling — `Bowling Dot Ball % (Weighted)`**

```tableau
IF SUM([legal_balls]) = 0 THEN NULL
ELSE 100.0 * SUM([dot_balls]) / SUM([legal_balls])
END
```

**IPL Matches — `Eligible Toss Match`**

```tableau
[result] = "runs" OR [result] = "wickets"
```

**IPL Matches — `Toss Winner Also Won`**

```tableau
IF [Eligible Toss Match] THEN IIF([toss_winner] = [winning_team], 1, 0) END
```

**IPL Matches — `Toss Winner Match Win %`**

```tableau
IF SUM(IIF([Eligible Toss Match], 1, 0)) = 0 THEN NULL
ELSE 100.0 * SUM([Toss Winner Also Won])
    / SUM(IIF([Eligible Toss Match], 1, 0))
END
```

This calculation should display 50.93% with no filters: 548 of 1,076 ordinary decided matches.

### Parameter-driven calculations

**`Selected Team Metric` — IPL Team Season**

```tableau
CASE [p Team Metric]
WHEN "Wins" THEN SUM([wins])
WHEN "Win %" THEN [Win % (Weighted)]
WHEN "Runs Scored" THEN SUM([total_runs_scored])
WHEN "Wickets Taken" THEN SUM([total_wickets_taken])
END
```

**`Season Included`** must be created once per applicable source, referencing its season field:

```tableau
[p Season] = "All" OR [season] = [p Season]
```

Use `[season_label]` instead of `[season]` in `IPL Matches`.

**`Team Included`** should be source-specific:

```tableau
// IPL Matches
[p Team] = "All" OR [team1] = [p Team] OR [team2] = [p Team]

// IPL Team Season
[p Team] = "All" OR [team] = [p Team]

// IPL Innings
[p Team] = "All" OR [batting_team] = [p Team] OR [bowling_team] = [p Team]
```

Do not apply a team parameter to batting or bowling sources: those sources do not contain a defensible player-team association.

## Parameters

| Parameter | Type/default | Values | Purpose |
|---|---|---|---|
| `p Season` | String / All | All plus the 17 cleaned season labels | Synchronizes season context across separate match, innings, and team sources |
| `p Team` | String / All | All plus the 15 standardized team names | Synchronizes team context across match, innings, and team dashboards |
| `p Top N Players` | Integer / 15 | Range 5–25, step 5 | Controls batting and bowling ranked views |
| `p Minimum Balls Faced` | Integer / 1,000 | Range 0–5,000, step 100 | Prevents low-volume batters from leading rate views |
| `p Minimum Legal Balls` | Integer / 1,200 | Range 0–5,000, step 100 | Prevents low-volume bowlers from leading economy views |
| `p Team Metric` | String / Wins | Wins, Win %, Runs Scored, Wickets Taken | Lets one team ranking answer several related questions without duplicate charts |

Do not add a Top N teams parameter: only 15 standardized teams exist, and the team dashboard benefits from showing the full field. Use native filters for player names, venue, city, and match stage rather than additional parameters.

For rate-scatter qualification, place `SUM([balls_faced]) >= [p Minimum Balls Faced]` or `SUM([legal_balls]) >= [p Minimum Legal Balls]` on Filters after the player dimension is in the view. For Top N, sort by the target measure and use `INDEX() <= [p Top N Players]` as a table-calculation filter.

## Filter strategy

| Filter/control | Scope | Application rule |
|---|---|---|
| `p Season` + `Season Included = True` | Overview, Team, Toss; optionally player dashboards | Apply the source-specific calculation only to worksheets intended to synchronize |
| `p Team` + `Team Included = True` | Overview, Team, Toss | Never apply to player sources because team membership is unavailable |
| Venue | IPL Overview | Apply to IPL Matches worksheets only; label it “Match context” so users do not expect team-season charts to change |
| City | IPL Overview | Apply only to IPL Matches worksheets |
| Match stage | IPL Overview and Toss | Apply only to eligible IPL Matches worksheets and group it under “Match context” |
| Batter | Batting dashboard | Apply to selected batting detail sheets, not the Top N discovery chart by default |
| Bowler | Bowling dashboard | Apply to selected bowling detail sheets, not the Top N discovery chart by default |
| Toss decision | Toss dashboard | Apply only to match-grain toss sheets |
| Minimum sample parameters | Batting/Bowling rate views | Do not suppress volume-only leaderboards unless explicitly desired |

Use “Apply to Worksheets → Selected Worksheets.” Avoid “All Using Related Data Sources,” which can silently broaden filters across incompatible grains.

Because Venue, City, and Match Stage do not exist at team-season grain, those controls must not filter Team Wins, Team Win %, or Total Teams. Their “Match context” label and selected-worksheet scope make this behavior explicit rather than silently presenting incomparable results.

## KPI definitions

### IPL Overview

| KPI | Source and expression | Unfiltered anchor |
|---|---|---:|
| Total Matches | IPL Matches: `COUNTD([match_id])` | 1,095 |
| Total Runs | IPL Matches: `SUM([match_total_runs])` | 347,756 |
| Total Teams | IPL Team Season: `COUNTD([team])` | 15 |
| Total Seasons | IPL Matches: `COUNTD([season_label])` | 17 |
| Total Wickets | IPL Matches: `SUM([match_bowler_wickets])` | 11,815 |

### Team Performance

Selected team matches, wins, weighted win percentage, runs scored, and wickets taken use `IPL Team Season`. Ties and no-results remain excluded from the win-percentage denominator.

### Batting Analysis

- Total Runs: `SUM([runs])` under the current filters.
- Average Strike Rate: use `Strike Rate (Weighted)`, never `AVG([strike_rate])`.
- Top Run Scorer: a one-mark sheet sorted by `SUM([runs])`, filtered to rank 1.
- Most Sixes: a one-mark sheet sorted by `SUM([sixes])`, filtered to rank 1.

### Bowling Analysis

- Total Wickets: `SUM([wickets])` using the bowler-credit convention.
- Average Economy: use `Economy (Weighted)`, never `AVG([economy_rate])`.
- Top Wicket Taker: one-mark sheet sorted by `SUM([wickets])`, rank 1.
- Most Legal Balls: one-mark sheet sorted by `SUM([legal_balls])`, rank 1.

### Toss & Match Analysis

Eligible matches, toss-winner match wins, and `Toss Winner Match Win %`. Always title the percentage “Toss winners also won” and include the eligible-match denominator in the tooltip.

## Worksheet inventory and visual choices

| Dashboard | Worksheet | Source | Mark/chart | Core encoding |
|---|---|---|---|---|
| Overview | KPI × 5 | Matches/Team Season | Text cards | Large value, small label |
| Overview | Matches by Season | Matches | Line with circles | season → x, count distinct match → y |
| Overview | Team Wins | Team Season | Horizontal bars | team → rows, wins → columns |
| Overview | Team Win % | Team Season | Horizontal bars/reference line | weighted win %; 50-match qualification for career view |
| Overview | Toss Outcome | Matches | 100% stacked bar | toss winner also won/lost among eligible matches |
| Overview | Result Distribution | Matches | Horizontal bars | result → rows, count matches → columns |
| Team | Dynamic Team Ranking | Team Season | Horizontal bars | selected team metric |
| Team | Performance by Season | Team Season | Line | season, wins/win %; team color/highlight |
| Team | Runs vs Wickets | Team Season | Scatter | runs scored → x, wickets taken → y, matches → size |
| Team | Toss Win % vs Match Win % | Team Season | Scatter + 45° reference | weighted toss win % vs weighted win % |
| Team | Season Ranking | Team Season | Highlight table | season × team, rank/wins color |
| Batting | Top Run Scorers | Batting | Horizontal bars | runs; Top N parameter |
| Batting | Strike Rate vs Runs | Batting | Scatter | runs → x, weighted strike rate → y, balls → size |
| Batting | Most Sixes / Fours | Batting | Ranked bars | boundary counts |
| Batting | Season Ranking | Batting | Highlight table | season × batter, run rank |
| Batting | Batter Detail | Batting | Text table | runs, balls, SR, average, boundaries, dots |
| Bowling | Top Wicket Takers | Bowling | Horizontal bars | wickets; Top N parameter |
| Bowling | Economy vs Wickets | Bowling | Scatter | wickets → x, weighted economy → y, balls → size |
| Bowling | Economical Bowlers | Bowling | Ranked bars | economy ascending after minimum balls filter |
| Bowling | Season Wicket Leaders | Bowling | Highlight table | season × bowler, wicket rank |
| Bowling | Bowler Detail | Bowling | Text table | balls, wickets, economy, dots, wides/no-balls |
| Toss | Toss Winner vs Match Winner | Matches | 100% stacked bar | also won / did not win |
| Toss | Toss Decision | Matches | Bars | bat/field by match count |
| Toss | Team Toss Win % | Team Season | Ranked bars | weighted toss win % |
| Toss | Toss-to-Match Win % | Team Season | Ranked bars | qualified weighted conversion rate |
| Toss | Season Toss Relationship | Matches | Line | season → x, eligible toss-win rate → y |

Avoid pie charts, gauges, dual axes with unrelated scales, 3D marks, and rainbow coloring.

## Dashboard layout

All dashboards use a fixed **1,366 × 768 px** canvas for a normal laptop. Use tiled containers for structural regions and floating objects only for navigation or brief annotations.

### Dashboard 1 — IPL Overview exact placement

| Region | X | Y | Width | Height |
|---|---:|---:|---:|---:|
| Header/navigation | 0 | 0 | 1,366 | 64 |
| Filter rail | 16 | 80 | 220 | 632 |
| KPI row | 252 | 80 | 1,098 | 112 |
| Matches by Season | 252 | 208 | 535 | 230 |
| Team Wins | 803 | 208 | 547 | 230 |
| Team Win % | 252 | 454 | 350 | 258 |
| Toss Outcome | 618 | 454 | 350 | 258 |
| Result Distribution | 984 | 454 | 366 | 258 |
| Footer/source note | 0 | 728 | 1,366 | 40 |

The five KPI cards are 210 px wide with 12 px gaps. The filter rail contains Season, Team, Venue, and Match Stage in that order. Footer text: “Source: validated IPL analytical layer, 2008–2024 | Updated through 2024.”

### Supporting dashboards

Use the same 1,366 × 768 shell: header 64 px; control strip at y=72, height 48; KPI row at y=128, height 96; main visual row at y=240, height 320; supporting/detail row at y=576, height 152; footer at y=736, height 32. Team uses three main visuals; Batting and Bowling use a large scatter plus ranked bar; Toss uses a large season line plus two ranked bars. Keep all essential interpretation above y=728.

## Visual design system

- Background: `#F5F7FA`; worksheet/card: `#FFFFFF`; primary text: `#172B4D`; secondary text: `#5E6C84`.
- Primary analytical accent: `#2F6BFF`; positive/highlight: `#1F9D72`; caution: `#F2A93B`; negative only when semantically appropriate: `#D64550`; neutral comparison marks: `#C7CED9`.
- Typography: Tableau Book or Arial. Dashboard title 24 pt semibold, section title 15 pt, KPI value 26–30 pt, body/axis 10–11 pt, source note 8–9 pt.
- Use 8 px corner spacing, 12–16 px internal padding, light `#DFE3E8` borders, and no heavy gridlines.
- Default to neutral bars and use a team-specific color only for the selected/highlighted team. Maintain one documented team color assignment throughout the workbook; do not show all 15 team colors unless direct identification is necessary.
- Format counts with thousands separators, percentages with one decimal in dashboards/two decimals in tooltips, strike/economy/run rate with two decimals.

## Tooltips

Start with the entity and season, then show the primary measure and its denominator. Examples:

- Team: matches, wins, losses, ties, no-results, weighted win %, runs, wickets.
- Batter: runs, balls faced, weighted strike rate, dismissals, weighted average, fours, sixes.
- Bowler: wickets, legal balls, six-ball-equivalent overs, weighted economy, dot-ball %, wides, no-balls.
- Toss: eligible matches, toss winner match wins, percentage, and the note “Descriptive association; not a causal estimate.”

## Interaction design

1. Team bar selection filters/highlights only team-compatible sheets on Overview and Team dashboards.
2. Season line selection updates sheets sharing the same native source; the `p Season` parameter provides deliberate cross-source synchronization.
3. Scatter selection highlights the same player in the corresponding ranked bar and detail table.
4. “Reset view” buttons use Tableau’s Revert action; do not require users to clear filters individually.
5. Navigation buttons link Overview, Team, Batting, Bowling, and Toss dashboards in a consistent header.
6. Hover supplies detail; clicks change analytical context only when a visible filter/highlight cue remains.
7. Do not allow a player selection to filter team views because the source does not provide a stable player-team bridge.

## Dashboard storytelling

- Overview: establish league scale, then show team success, efficiency, and match/toss context.
- Team: move from outcome volume to season trend, scoring/wicket balance, and toss association.
- Batting: contrast career volume with scoring speed, then reveal boundaries and season consistency.
- Bowling: contrast wicket volume with run control, then reveal workload and season leadership.
- Toss: begin with the near-even overall result, expose team/season variation, and end with a non-causality reminder.

## Phase 9 implementation plan

1. Open Tableau Public and create a new workbook.
2. Connect to each of the five CSVs with **Text File** and rename the sources exactly as documented.
3. Verify source row counts and field types before creating any sheet.
4. Keep sources separate. Add the optional match-to-innings relationship only if a specific combined worksheet requires it.
5. Create the six parameters and source-specific synchronization calculations.
6. Create weighted calculations in their designated sources and validate them in simple text sheets.
7. Build KPI sheets and compare unfiltered values with the anchors below.
8. Build worksheets in dashboard order, applying minimum-sample filters only to rate-based views.
9. Assemble the five 1,366 × 768 dashboards using the documented containers and coordinates.
10. Add selected-sheet filter/highlight actions, navigation buttons, reset controls, and contextual tooltips.
11. Validate filtered and unfiltered totals, check for row multiplication, and test every interaction.
12. Save the future workbook as `tableau/IPL_Performance_Analytics.twbx` only after it opens cleanly and passes KPI validation.

## Tableau validation baseline

| Source | Rows | Columns | Duplicate grain keys | Unexpected nulls | Status |
|---|---:|---:|---:|---:|---|
| IPL Matches | 1,095 | 33 | 0 | 0 | PASS |
| IPL Innings | 2,217 | 17 | 0 | 0 | PASS |
| IPL Team Season | 146 | 19 | 0 | 0 | PASS |
| IPL Batting | 2,617 | 14 | 0 | 0 | PASS |
| IPL Bowling | 1,948 | 12 | 0 | 0 | PASS |

Expected conditional nulls remain in IPL Matches (`winning_team`, result margin, player of match, method, toss/match indicator, losing team, margin type) and IPL Batting (average when dismissals are zero; boundary percentage when runs are zero). They are not errors and must not be replaced in Tableau.

The reusable `src/tableau_validation.py` check returned **48 PASS / 0 FAIL**. It verifies file existence, exact columns, numeric/date types, empty strings, grain keys, required-field completeness, contextual nulls, the complete Phase 6 feature validation, and the reconciliation anchors.

Unfiltered workbook anchors are 1,095 matches, 347,756 total runs, 15 standardized teams, 17 seasons, 11,815 bowler-credit wickets, 330,064 batter runs, 17,692 extras, and 251,471 legal balls.

## Known limitations

- Player names are source identifiers rather than stable IDs.
- Batting and bowling sources do not support a defensible team filter.
- Player match counts reflect recorded role appearances, not squad selection.
- Super-over innings are included unless an innings filter explicitly removes them.
- Team standardization follows Phase 4 and does not reconstruct ownership history.
- Tableau Public publishing may package local CSVs; refresh paths must be checked after moving the repository.
- Parameter lists for the fixed 2008–2024 dataset require maintenance if future seasons are added.
- Toss comparisons are descriptive and cannot establish causation.
