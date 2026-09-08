# IPL data-cleaning rules and before/after report

## Scope and reproducibility

Phase 4 reads `data/raw/matches.csv` and `data/raw/deliveries.csv`, applies the rules in `src/data_cleaning.py`, and writes only `data/processed/matches_clean.csv` and `data/processed/deliveries_clean.csv`. Raw fields used in standardization are retained with a `_raw` suffix. No rows are removed.

## Before/after summary

| Measure | Raw | Cleaned | Change |
|---|---:|---:|---:|
| Match rows | 1,095 | 1,095 | 0 |
| Delivery rows | 260,920 | 260,920 | 0 |
| Season labels | 17 | 17 | 0 |
| Team-name values | 19 | 15 | -4 |
| Venue-name values | 58 | 40 | -18 |
| Non-null city-name values | 36 | 35 | -1 |
| Missing city values | 51 | 0 | -51 |

## Date and season rules

| Field | Original state | Transformation | Reason | Result |
|---|---|---|---|---|
| `date` | ISO-like text | Preserve as `date_raw`; parse with `%Y-%m-%d` into `match_date` | Reliable date filtering and validation | 1,095 parsed dates; 0 failures |
| `match_date` | Not present | Derive `match_year`, `match_month`, and `match_day` | Simple calendar filtering | Integer calendar components |
| `season` | 17 text labels with single- and split-year formats | Preserve as `season_raw`; create `season_standard` without changing identity | Avoid inventing a numeric season convention | All 17 labels retained |
| `season_start_year` | Not present | Extract the first four digits of `season_standard` | Optional numeric ordering helper | Starting calendar year, not the original label |

## Team rules

These four rules apply to `team1`, `team2`, `toss_winner`, `winner`, `batting_team`, and `bowling_team`. Each source field is retained as `<field>_raw`; the mapped value is stored as `<field>_standard`.

| Raw value | Standard value | Decision basis |
|---|---|---|
| Delhi Daredevils | Delhi Capitals | Same franchise rename |
| Kings XI Punjab | Punjab Kings | Same franchise rename |
| Royal Challengers Bangalore | Royal Challengers Bengaluru | Same franchise rename |
| Rising Pune Supergiants | Rising Pune Supergiant | Same temporary franchise naming variation |

The following remain distinct: Gujarat Lions/Gujarat Titans, Pune Warriors/Rising Pune Supergiant, Deccan Chargers/Sunrisers Hyderabad, and Kochi Tuskers Kerala/all other teams.

## Venue rules

Only reviewed punctuation, suffix, and clearly equivalent Mohali label variants are consolidated. These rules affect 361 matches.

| Raw venue | Standard venue |
|---|---|
| Arun Jaitley Stadium, Delhi | Arun Jaitley Stadium |
| Brabourne Stadium, Mumbai | Brabourne Stadium |
| Dr DY Patil Sports Academy, Mumbai | Dr DY Patil Sports Academy |
| Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium, Visakhapatnam | Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium |
| Eden Gardens, Kolkata | Eden Gardens |
| Himachal Pradesh Cricket Association Stadium, Dharamsala | Himachal Pradesh Cricket Association Stadium |
| M Chinnaswamy Stadium, Bengaluru | M Chinnaswamy Stadium |
| M.Chinnaswamy Stadium | M Chinnaswamy Stadium |
| MA Chidambaram Stadium, Chepauk | MA Chidambaram Stadium |
| MA Chidambaram Stadium, Chepauk, Chennai | MA Chidambaram Stadium |
| Maharashtra Cricket Association Stadium, Pune | Maharashtra Cricket Association Stadium |
| Punjab Cricket Association IS Bindra Stadium, Mohali | Punjab Cricket Association IS Bindra Stadium |
| Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh | Punjab Cricket Association IS Bindra Stadium |
| Punjab Cricket Association Stadium, Mohali | Punjab Cricket Association IS Bindra Stadium |
| Rajiv Gandhi International Stadium, Uppal | Rajiv Gandhi International Stadium |
| Rajiv Gandhi International Stadium, Uppal, Hyderabad | Rajiv Gandhi International Stadium |
| Sawai Mansingh Stadium, Jaipur | Sawai Mansingh Stadium |
| Wankhede Stadium, Mumbai | Wankhede Stadium |

Historical labels that may describe the same physical site—but imply a broader rename policy—remain separate. Examples include Feroz Shah Kotla/Arun Jaitley Stadium and Sardar Patel Stadium/Narendra Modi Stadium.

## City and missing-value rules

| Original state | Transformation | Reason | Result |
|---|---|---|---|
| `Bangalore` (65 rows) | `Bengaluru` in `city_standard` | Clear city-name variant | Raw value retained in `city_raw` |
| Missing city at Dubai International Cricket Stadium (33 rows) | Fill `city_standard` with `Dubai` | Venue is unambiguous and other rows confirm the city | 33 filled |
| Missing city at Sharjah Cricket Stadium (18 rows) | Fill `city_standard` with `Sharjah` | Venue is unambiguous and other rows confirm the city | 18 filled |

No global null fill is used. The following are preserved because absence has domain meaning:

- `winner` and `player_of_match` for no-result matches;
- `result_margin` for ties and no-results;
- `method` when D/L was not used;
- `extras_type` when no extras occurred;
- dismissal and fielder fields when no dismissal or fielder applies.

## Delivery and legal-ball rules

One cleaned row remains one recorded delivery. No row is removed because its ball number exceeds six or because it records extras.

`is_legal_delivery` is `False` when `extras_type` is `wides` or `noballs`; otherwise it is `True`. `legal_ball` contains the equivalent integer value, 0 or 1. Byes, leg-byes, penalties, and deliveries without extras count as legal balls.

| Delivery classification | Rows |
|---|---:|
| All recorded deliveries | 260,920 |
| Legal deliveries | 251,471 |
| Illegal deliveries | 9,449 |
| Wides | 8,380 |
| No-balls | 1,069 |
| Recorded rows with `ball > 6`, retained | 9,340 |

## Limitations

- Player names are not standardized because no stable player ID or master table exists.
- Historical stadium renames are not broadly merged.
- CSV does not persist Pandas extension dtypes; the pipeline explicitly restores types when loaded for processing.
- Performance metrics and rankings are intentionally deferred to Phase 6.
