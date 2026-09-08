# IPL analytical feature definitions

## Scope

Phase 6 consumes only `matches_clean.csv` and `deliveries_clean.csv`. It does not edit raw or cleaned source files. Five analytical outputs are created. `innings_summary.csv` is the only output beyond the four requested summaries; it is retained because innings 3–6 contain super-over activity that cannot be represented safely in fixed first/second-innings columns.

## Shared cricket conventions

- **Legal delivery:** `extras_type` is not `wides` or `noballs`, exactly as established in Phase 4.
- **Batting ball faced:** every recorded delivery faced by a batter except a wide. A no-ball is not a legal delivery for the over, but it is a ball faced by the striker under the metric used here.
- **Dot ball:** a legal delivery with `total_runs = 0`.
- **Bowler wicket:** dismissal type is `bowled`, `caught`, `caught and bowled`, `lbw`, `stumped`, or `hit wicket`. Run outs, retired hurt, retired out, and obstructing the field are excluded.
- **Bowler runs conceded:** `total_runs` minus byes, leg-byes, and penalty extras. Batter runs, wides, and no-ball extras are charged to the bowler.
- **Standard teams/cities/venues:** only Phase 4 standardized fields are used. No additional identity mapping occurs.
- All season fields retain the cleaned IPL season label, including split-year labels.

## Formulas

| Metric | Formula | Zero-denominator/null treatment |
|---|---|---|
| Run Rate | `total_runs / legal_balls × 6` | Null when legal balls are zero |
| Strike Rate | `runs / balls_faced × 100` | Null when balls faced are zero |
| Batting Average | `runs / dismissals` | Null when dismissals are zero |
| Economy Rate | `runs_conceded / legal_balls × 6` | Null when legal balls are zero |
| Win Percentage | `wins / (wins + losses) × 100` | Null when there are no decided matches |
| Toss-to-Match-Win Percentage | `toss_match_wins / toss_decided_matches × 100` | Null when a team won no toss in a normally decided match |
| Boundary Runs | `fours × 4 + sixes × 6` | Integer count; zero is meaningful |
| Boundary Percentage | `boundary_runs / runs × 100` | Null when runs are zero |
| Batting Dot Ball Percentage | `dot_balls / balls_faced × 100` | Null when balls faced are zero |
| Bowling Dot Ball Percentage | `dot_balls / legal_balls × 100` | Null when legal balls are zero |
| Overs Bowled | `legal_balls / 6` | Numeric overs, not cricket `overs.balls` notation |

## `match_summary.csv`

Grain: one row per `match_id` (1,095 rows).

| Feature | Definition | Source / null handling |
|---|---|---|
| `match_id` | Unique match key | Clean match key |
| `season_label` | Preserved analytical IPL season | `season_standard` |
| `match_date` | Parsed match date | Clean date |
| `city`, `venue` | Standardized location | Phase 4 fields |
| `team1`, `team2` | Standardized participants | Phase 4 fields |
| `toss_winner`, `toss_decision` | Toss result | Clean match fields |
| `winning_team` | Source-provided standardized winner | Null for no-result; retained for source-resolved ties |
| `losing_team` | Other participant for `runs`/`wickets` results | Null for ties and no-results |
| `match_decided` | Whether source provides a winner | True for source-resolved super-over ties; false for no-result |
| `toss_winner_is_match_winner` | Toss winner equals source winner | Null for no-result |
| `win_margin_type` | `runs` or `wickets` | Null for tie/no-result |
| `match_stage` | League, Playoffs, or Final | Derived from existing `match_type`; detail retained separately |
| `innings_count` | Distinct recorded innings | Includes super-over innings |
| `match_recorded_deliveries` | All delivery rows for match | Sum of innings records |
| `match_legal_balls`, `match_illegal_deliveries` | Delivery classification totals | Phase 4 flags |
| `match_total_runs`, `match_batsman_runs`, `match_extra_runs` | Match scoring totals | Sums across all innings |
| `match_wickets` | All recorded wicket flags | Includes non-bowler dismissals |
| `match_bowler_wickets` | Bowler-credited wickets | Shared convention above |
| `match_fours`, `match_sixes`, `match_dot_balls` | Match event counts | Delivery-derived |

`result`, `result_margin`, `player_of_match`, `match_type`, `super_over`, and `method` remain available with their cleaned conditional nulls.

## `innings_summary.csv`

Grain: one row per `match_id + inning` (2,217 rows).

| Feature | Definition | Source / null handling |
|---|---|---|
| `season` | Clean season label | Match-to-delivery join |
| `batting_team`, `bowling_team` | Standardized innings teams | Delivery fields |
| `recorded_deliveries` | All delivery rows | Group size |
| `legal_balls` | Sum of `legal_ball` | Wides/no-balls excluded |
| `illegal_deliveries` | Recorded minus legal deliveries | Count of wide/no-ball rows |
| `total_runs`, `batsman_runs`, `extra_runs` | Innings scoring totals | Direct sums |
| `wickets` | All recorded wicket flags | Direct sum |
| `bowler_wickets` | Credited wickets | Shared convention |
| `fours`, `sixes` | Deliveries with 4/6 batter runs | Event counts |
| `dot_balls` | Legal deliveries with zero total runs | Event count |
| `run_rate` | Runs per six legal deliveries | Null only if legal balls are zero |

## `team_season_summary.csv`

Grain: one row per `season + team` (146 rows). Participation is built from both match-team columns.

| Feature | Definition | Source / null handling |
|---|---|---|
| `matches_played` | Distinct matches involving team | Both participants |
| `wins`, `losses` | Outcomes from `runs`/`wickets` results only | Ties/no-results excluded |
| `decided_matches` | `wins + losses` | Win-percentage denominator |
| `ties`, `no_results` | Team appearances in those result types | Both teams receive the event count |
| `win_percentage` | Wins among decided matches | Formula above |
| `total_runs_scored` | Runs while team batted | Includes all recorded innings, including super overs |
| `total_runs_conceded` | Total runs while team bowled | Includes all recorded innings |
| `average_runs_scored`, `average_runs_conceded` | Respective total per match played | Not an innings average |
| `total_wickets_taken` | Bowler-credited wickets by team | Shared convention |
| `total_wickets_lost` | Bowler-credited wickets against team | Uses same convention for reconciliation |
| `toss_wins` | All matches where team won toss | Includes ties/no-results |
| `toss_decided_matches` | Normally decided matches where team won toss | Toss-rate denominator |
| `toss_match_wins` | Team won both toss and normally decided match | Numerator |
| `toss_to_match_win_percentage` | Toss/match wins among eligible toss wins | Descriptive, not causal |

## `batting_summary.csv`

Grain: one row per `season + batter` (2,617 rows). `matches` means matches in which the batter faced at least one recorded delivery, not official squad appearances.

| Feature | Definition | Source / null handling |
|---|---|---|
| `matches` | Distinct matches with a batter delivery | Batter field |
| `runs` | Batter runs | Sum of `batsman_runs` |
| `balls_faced` | Recorded batter deliveries excluding wides | No-ball rows included |
| `fours`, `sixes` | Boundary delivery counts | `batsman_runs = 4/6` |
| `boundary_runs` | Runs scored in fours and sixes | Formula above |
| `dot_balls` | Legal, zero-total-run deliveries faced | Event count |
| `dismissals` | Rows naming batter as dismissed, excluding retired hurt | Does not infer not-outs |
| `strike_rate` | Runs per 100 balls faced | Formula above |
| `batting_average` | Runs per supported dismissal | Null for 253 batter-seasons with no dismissal |
| `boundary_percentage` | Share of batter runs from boundaries | Null for 128 zero-run batter-seasons |
| `dot_ball_percentage` | Dot balls per ball faced | Formula above |

## `bowling_summary.csv`

Grain: one row per `season + bowler` (1,948 rows). `matches` means matches in which the player bowled at least one recorded delivery.

| Feature | Definition | Source / null handling |
|---|---|---|
| `legal_balls` | Legal balls bowled | Phase 4 indicator |
| `overs_bowled` | Legal balls divided by six | Decimal numeric measure |
| `runs_conceded` | Bowler-chargeable runs | Excludes byes, leg-byes, penalties |
| `wickets` | Bowler-credited dismissals | Excludes run outs and retirement/non-bowler types |
| `economy_rate` | Runs conceded per six legal balls | Formula above |
| `dot_balls` | Legal balls with zero total runs | Event count |
| `dot_ball_percentage` | Dot balls per legal ball | Formula above |
| `wides`, `no_balls` | Delivery rows with each extras type | Counts events, not extra-run magnitude |

## Reconciliation baselines

| Measure | Validated total |
|---|---:|
| Batter runs | 330,064 |
| Extras | 17,692 |
| Total runs | 347,756 |
| Legal balls | 251,471 |
| Bowler-credited wickets | 11,815 |
| Bowler runs conceded | 341,232 |

## Limitations

- No stable player ID exists; batter and bowler names remain source identifiers.
- No universal player-team table is created because delivery roles do not prove official squad membership.
- Player-of-the-Match counts can be aggregated directly from `match_summary.csv`; a separate file would duplicate that grain without adding analytical value.
- Totals include super-over innings. Filters can use `inning` in `innings_summary.csv` when regulation-only analysis is required.
