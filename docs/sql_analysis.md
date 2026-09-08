# IPL SQL analysis layer

## Purpose and scope

Phase 7 provides a reproducible SQLite analytics layer over the five validated Phase 6 summaries. The database is generated at `data/processed/ipl_analysis.db` with Python's standard-library `sqlite3` module. Raw files, cleaned files, and Phase 6 CSVs remain immutable inputs. Delivery-level raw and cleaned tables are intentionally excluded because the five summaries answer the defined SQL questions without duplicating 260,920 delivery rows.

## Tables and relationships

| Table | Grain | Rows | Natural key |
|---|---|---:|---|
| `match_summary` | One match | 1,095 | `match_id` |
| `innings_summary` | One match and innings | 2,217 | `match_id, inning` |
| `team_season_summary` | One season and team | 146 | `season, team` |
| `batting_summary` | One season and batter | 2,617 | `season, batter` |
| `bowling_summary` | One season and bowler | 1,948 | `season, bowler` |

`match_summary.match_id` has a one-to-many relationship with `innings_summary.match_id`, enforced by a foreign key. The season/team and season/player summaries are aggregated analytical facts rather than dimensions; they can be compared through their season labels, but no unsupported player-team relationship is imposed. Four views provide correctly recomputed career and toss metrics: `v_team_overall`, `v_batting_career`, `v_bowling_career`, and `v_toss_by_season`.

Important columns include match outcome and toss fields in `match_summary`, legal-ball and scoring totals in `innings_summary`, additive outcome denominators in `team_season_summary`, batter runs/balls/dismissals in `batting_summary`, and bowler runs/legal balls/wickets in `bowling_summary`.

## Build and SQL methodology

`src/sql_analysis.py` inspects the five CSVs, creates a temporary SQLite database from `sql/schema.sql`, loads each table into its declared schema, creates the views, runs integrity and foreign-key checks, and only then atomically replaces the generated database. A pre-existing database is inspected before replacement and rebuilding is refused if it contains an unexpected object.

The five topic files contain 30 named analytical queries. They use aggregation, `HAVING`, conditional `CASE` expressions, joins, subqueries, CTEs, and window functions. Career rates are always recomputed from additive totals; season percentages are never averaged. `RANK()` preserves performance ties, while `ROW_NUMBER()` is used only when a deterministic single result per season is requested.

## Metric definitions

- Team win percentage: `wins / (wins + losses) × 100`. Ties and no-results are excluded.
- Team scoring rate: `total runs / legal balls × 6`.
- Batter strike rate: `runs / balls faced × 100`.
- Batting average: `runs / supported dismissals`.
- Bowler economy: `bowler-chargeable runs / legal balls × 6`.
- Toss-to-match-win percentage: ordinary match wins after winning the toss divided by eligible toss wins.
- Composite profiles are transparent averages of ordinal ranks. They summarize selected metrics and are not an official IPL rating.

Bowler wickets retain the Phase 6 convention: bowled, caught, caught and bowled, lbw, stumped, and hit wicket are credited. Run outs and other non-bowler dismissals are excluded. Bowler runs exclude byes, leg-byes, and penalty runs.

## Qualification thresholds

| Analysis | Threshold | Reason |
|---|---:|---|
| Team career win percentage/composite | 50 decided matches | Excludes short-lived, very small team samples |
| Team scoring rate | 3,000 legal balls | Requires substantial batting exposure |
| Batter strike rate | 1,000 balls faced | Avoids short cameo leaders |
| Batter average | 50 dismissals | Requires sustained dismissal exposure |
| High-volume/high-rate batter | 2,000 runs and 1,000 balls | Balances output and pace |
| Bowler economy/composite | 1,200 legal balls | Approximately 200 six-ball overs |
| High-wicket/good-economy bowler | 100 wickets | Requires long-term wicket volume |
| Team toss-win percentage | 50 matches | Removes very small franchise samples |
| Toss-to-match-win percentage | 25 eligible toss wins | Requires repeated eligible events |
| Toss split comparison | 20 toss wins and 20 toss losses | Requires both comparison groups |

Thresholds are analytical safeguards, not claims that excluded players or teams lack quality.

## Key results

- Mumbai Indians lead career wins with 142; Chennai Super Kings have the highest qualified win percentage at 58.47% across 236 decided matches.
- Gujarat Titans have the highest aggregate scoring rate among teams with at least 3,000 legal balls at 8.83 runs per six legal balls. Their shorter history should still be considered when comparing them with long-running franchises.
- The transparent team composite places Mumbai Indians first (1.75 average rank) and Chennai Super Kings second (2.00).
- V Kohli leads batter runs with 8,014. AD Russell has the highest qualified strike rate at 174.84 among batters with at least 1,000 balls, while KL Rahul has the highest qualified average at 44.66 among batters with at least 50 dismissals.
- YS Chahal leads bowler-credit wickets with 205. M Muralitharan has the best qualified economy at 6.70 among bowlers with at least 1,200 legal balls.
- In the 1,076 ordinary runs/wickets results, the toss winner also won 548 times, or 50.93%. This is an association, not evidence that winning the toss caused the result.
- Chennai Super Kings have the highest qualified toss-to-match-win percentage at 62.50% across 120 eligible toss wins.

## Validation and reconciliation

The database passed 49 automated database/query checks during the Phase 7 build. All 30 named analysis queries executed successfully, SQLite returned `ok` from `PRAGMA integrity_check`, and `PRAGMA foreign_key_check` returned zero violations.

| Reconciliation | SQLite result | Phase 6 anchor | Status |
|---|---:|---:|---|
| Matches | 1,095 | 1,095 | PASS |
| Total runs | 347,756 | 347,756 | PASS |
| Batter runs | 330,064 | 330,064 | PASS |
| Extras | 17,692 | 17,692 | PASS |
| Legal balls | 251,471 | 251,471 | PASS |
| Bowler-credit wickets | 11,815 | 11,815 | PASS |

Team runs scored and conceded both reconcile with innings runs; batting runs reconcile with innings batter runs; bowling legal balls reconcile with innings legal balls; and team wickets taken reconcile with bowler-credit wickets.

## Limitations

- The source has no stable player ID, so names remain the player key.
- Season match appearances in player summaries mean matches with at least one recorded batting or bowling delivery, not official squad appearances.
- Super-over innings are included in aggregate totals.
- Standardized historical franchise names follow Phase 4 and do not reconstruct ownership history.
- Composite ranks depend on the selected dimensions and qualification thresholds.
- Toss results are descriptive associations and must not be interpreted causally.
