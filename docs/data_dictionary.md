# Cleaned data dictionary

The Phase 4 analytical layer contains two CSV files. Examples are representative source-style values, not fabricated performance results. `string` and `datetime64[ns]` describe in-memory Pandas types; dates are serialized as `YYYY-MM-DD` in CSV.

## `matches_clean.csv`

Grain: one row per IPL match.

| Field | Type | Description | Example | Source / transformation |
|---|---|---|---|---|
| `match_id` | integer | Unique match identifier | `335982` | Raw `id`, renamed |
| `season_raw` | string | Original season label | `2007/08` | Raw `season` |
| `season_standard` | string | Audited season identity label | `2007/08` | Trim-validated; identity preserved |
| `season_start_year` | integer | First calendar year in season label | `2007` | First four characters; not a replacement season ID |
| `date_raw` | string | Original match date text | `2008-04-18` | Raw `date` |
| `match_date` | datetime | Parsed match date | `2008-04-18` | Parsed with `%Y-%m-%d` |
| `match_year` | integer | Calendar year of match | `2008` | From `match_date` |
| `match_month` | integer | Calendar month number | `4` | From `match_date` |
| `match_day` | integer | Calendar day number | `18` | From `match_date` |
| `match_type` | string | Raw competition stage | `League` | Unchanged |
| `city_raw` | string | Original city, including nulls | `Bangalore` | Raw `city` |
| `city_standard` | string | Reviewed analytical city | `Bengaluru` | City mapping or unambiguous Dubai/Sharjah fill |
| `venue_raw` | string | Original venue label | `Eden Gardens, Kolkata` | Raw `venue` |
| `venue_standard` | string | Conservative canonical venue label | `Eden Gardens` | Explicit venue mapping |
| `team1_raw` | string | Original first-team label | `Delhi Daredevils` | Raw `team1` |
| `team1_standard` | string | Standardized first-team label | `Delhi Capitals` | Explicit team mapping |
| `team2_raw` | string | Original second-team label | `Kings XI Punjab` | Raw `team2` |
| `team2_standard` | string | Standardized second-team label | `Punjab Kings` | Explicit team mapping |
| `toss_winner_raw` | string | Original toss-winner label | `Delhi Daredevils` | Raw `toss_winner` |
| `toss_winner_standard` | string | Standardized toss winner | `Delhi Capitals` | Explicit team mapping |
| `toss_decision` | string | Toss choice | `field` | Unchanged |
| `winner_raw` | string | Original winner; null for no-result | `Kings XI Punjab` | Raw `winner` |
| `winner_standard` | string | Standardized winner; null for no-result | `Punjab Kings` | Explicit team mapping |
| `player_of_match` | string | Award recipient; null when unavailable | `BB McCullum` | Unchanged |
| `result` | string | Outcome type | `runs` | Unchanged |
| `result_margin` | number | Winning runs/wickets according to `result` | `140` | Unchanged; conditional null retained |
| `target_runs` | number | Chase target | `223` | Unchanged; conditional null retained |
| `target_overs` | number | Overs available for target | `20` | Unchanged; conditional null retained |
| `super_over` | string | Super-over indicator | `N` | Unchanged |
| `method` | string | Rain-adjustment method | `D/L` | Unchanged; non-applicable null retained |
| `umpire1` | string | First on-field umpire | `Asad Rauf` | Unchanged |
| `umpire2` | string | Second on-field umpire | `RE Koertzen` | Unchanged |

## `deliveries_clean.csv`

Grain: one row per recorded delivery, including wides and no-balls.

| Field | Type | Description | Example | Source / transformation |
|---|---|---|---|---|
| `match_id` | integer | Match foreign key | `335982` | Unchanged |
| `inning` | integer | Innings number, including super-over innings | `1` | Unchanged |
| `batting_team_raw` | string | Original batting-team label | `Kolkata Knight Riders` | Raw `batting_team` |
| `batting_team_standard` | string | Standardized batting team | `Kolkata Knight Riders` | Explicit team mapping |
| `bowling_team_raw` | string | Original bowling-team label | `Royal Challengers Bangalore` | Raw `bowling_team` |
| `bowling_team_standard` | string | Standardized bowling team | `Royal Challengers Bengaluru` | Explicit team mapping |
| `over` | integer | Zero-based over number | `0` | Unchanged |
| `ball` | integer | Recorded delivery sequence within over | `1` | Unchanged; may exceed 6 |
| `batter` | string | Striker name | `SC Ganguly` | Unchanged |
| `bowler` | string | Bowler name | `P Kumar` | Unchanged |
| `non_striker` | string | Non-striker name | `BB McCullum` | Unchanged |
| `batsman_runs` | integer | Runs credited to batter | `0` | Unchanged source terminology |
| `extra_runs` | integer | Extras on delivery | `1` | Unchanged |
| `total_runs` | integer | Batter plus extra runs | `1` | Unchanged and arithmetic-validated |
| `extras_type` | string | Extras category, null without extras | `wides` | Conditional null retained |
| `is_wicket` | integer | Recorded dismissal indicator, 0/1 | `0` | Unchanged and validated |
| `player_dismissed` | string | Dismissed player, when applicable | `AA Noffke` | Conditional null retained |
| `dismissal_kind` | string | Dismissal type, when applicable | `caught` | Conditional null retained |
| `fielder` | string | Involved fielder, when applicable | `M Kartik` | Conditional null retained |
| `is_legal_delivery` | boolean | False for wides and no-balls | `False` | Derived from `extras_type` |
| `legal_ball` | integer | Additive legal-ball indicator | `0` | Integer form of `is_legal_delivery` |
