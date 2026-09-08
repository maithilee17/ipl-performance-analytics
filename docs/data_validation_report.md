# IPL cleaned-data validation report

## 1. Validation objective

Phase 5 establishes whether the Phase 4 cleaned data is structurally valid, internally consistent, cricket-aware, reproducible, and suitable for later feature engineering, SQL, and Tableau work. Validation is read-only: it reports limitations instead of repairing or rewriting data.

## 2. Dataset versions and files validated

| File | Grain | Rows | Columns |
|---|---|---:|---:|
| `data/processed/matches_clean.csv` | One match | 1,095 | 32 |
| `data/processed/deliveries_clean.csv` | One recorded delivery | 260,920 | 21 |

The corresponding raw files were used only for reconciliation and SHA-256 comparison.

## 3. Environment

- Windows
- Python 3.11.2
- Pandas 3.0.5
- NumPy 2.4.6
- pytest 9.1.1
- Project virtual environment: `.venv`

## 4. Schema validation

| Check | Expected | Actual | Status | Explanation |
|---|---|---|---|---|
| Match schema | 32 documented columns; no extras | 32; 0 missing; 0 unexpected | PASS | Exact Phase 4 contract matched. |
| Delivery schema | 21 documented columns; no extras | 21; 0 missing; 0 unexpected | PASS | Exact Phase 4 contract matched. |
| Identifier/calendar/run types | Integer-like | All integer-like | PASS | CSV-compatible inferred types are sufficient. |
| Nullable match measures | Numeric | `float64` | PASS | Float is expected where numeric values coexist with CSV nulls. |
| `match_date` | Parsed datetime | `datetime64[us]` | PASS | The loader explicitly parses the serialized ISO date. |
| `is_legal_delivery` | Boolean | `bool` | PASS | Serialized values infer correctly. |
| Accidental blank strings | 0 | 0 | PASS | Contextual nulls are distinct from empty strings. |
| Categorical domains | No undocumented values | 0 invalid values | PASS | Match type, result, toss, super over, method, extras, and dismissals checked. |

## 5. Row-count validation

| Check | Expected | Actual | Status | Explanation |
|---|---:|---:|---|---|
| Match rows | 1,095 | 1,095 | PASS | No matches added or removed. |
| Delivery rows | 260,920 | 260,920 | PASS | Recorded-delivery grain preserved. |

## 6. Primary-key validation

| Check | Expected | Actual | Status | Explanation |
|---|---:|---:|---|---|
| Null `matches_clean.match_id` | 0 | 0 | PASS | Cleaned match key is complete. |
| Duplicate match IDs | 0 | 0 | PASS | One row per match. |
| Null delivery match IDs | 0 | 0 | PASS | Foreign key is complete. |
| Duplicate `(match_id, inning, over, ball)` keys | 0 | 0 | PASS | Delivery grain remains unique. |

## 7. Referential-integrity validation

| Check | Expected | Actual | Status | Explanation |
|---|---:|---:|---|---|
| Orphan delivery match IDs | 0 | 0 | PASS | Every delivery ID exists in matches. |
| Orphan delivery rows | 0 | 0 | PASS | No delivery references another/unknown match. |
| Matches without deliveries | 0 | 0 | PASS | Every match has delivery rows. |

## 8. Team validation

| Check | Expected | Actual | Status | Explanation |
|---|---:|---:|---|---|
| Standard team values | 15 | 15 | PASS | Reconciles with 19 raw values and four mappings. |
| Old names in standardized fields | 0 | 0 | PASS | Old values remain only in `_raw` audit fields. |
| `team1 = team2` | 0 | 0 | PASS | Match participants differ. |
| Batting team equals bowling team | 0 | 0 | PASS | Delivery opponents differ. |
| Invalid toss winners | 0 | 0 | PASS | Every toss winner is a participant. |
| Invalid match winners | 0 | 0 | PASS | Every populated winner is a participant. |
| Documented mapping mismatches | 0 | 0 | PASS | All four mappings agree across six team roles. |

## 9. Venue and city validation

| Check | Expected | Actual | Status | Explanation |
|---|---|---|---|---|
| Venue mapping mismatches | 0 | 0 | PASS | All 18 Phase 4 mappings reproduced; no new mapping added. |
| Empty/null standard venues | 0 | 0 | PASS | Every match retains a venue. |
| `Bangalore` in standard city | 0 | 0 | PASS | All 65 source occurrences map to Bengaluru. |
| Dubai fills | 33 | 33 | PASS | Filled only from the documented venue. |
| Sharjah fills | 18 | 18 | PASS | Filled only from the documented venue. |
| Missing standard cities | 0 | 0 | PASS | All 51 supported source nulls were filled. |
| Standard venues with multiple city labels | 0 preferred | Dr DY Patil Sports Academy has 2 | WARN | Source rows use both Mumbai and Navi Mumbai. No geography was invented or overwritten. |

## 10. Date and season validation

| Check | Expected | Actual | Status | Explanation |
|---|---|---|---|---|
| Null/invalid match dates | 0 | 0 | PASS | All dates parse. |
| Date coverage | 2008-04-18 to 2024-05-26 | 2008-04-18 to 2024-05-26 | PASS | Matches observed source bounds. |
| Season labels | 17 documented text labels | Exact match | PASS | Split-year values remain strings. |
| Raw/standard season identity differences | 0 | 0 | PASS | No invented season mapping. |
| Invalid `season_start_year` | 0 | 0 | PASS | Matches first four characters of label. |
| Inconsistent season/date rows | 0 | 0 | PASS | Single-year labels match date year; split-year labels permit either year. |
| Calendar component mismatches | 0 | 0 | PASS | Year, month, and day reconcile to `match_date`. |

## 11. Run reconciliation

| Check | Expected | Actual | Status | Explanation |
|---|---:|---:|---|---|
| Negative run values | 0 | 0 | PASS | Batter, extra, and total runs checked. |
| Per-row arithmetic mismatches | 0 | 0 | PASS | `total_runs = batsman_runs + extra_runs` everywhere. |
| Raw/clean aggregate run differences | 0 | 0 | PASS | Cleaning did not change scoring measures. |
| Non-D/L target mismatches | 0 among 1,071 eligible matches | 0 among 1,071 | PASS | D/L and missing targets excluded because they are not directly comparable. |

## 12. Wicket validation

| Check | Expected | Actual | Status | Explanation |
|---|---:|---:|---|---|
| Wicket flag domain | `{0, 1}` | `{0, 1}` | PASS | Binary indicator preserved. |
| Wicket rows missing player | 0 | 0 | PASS | Conditional player field is complete. |
| Wicket rows missing dismissal kind | 0 | 0 | PASS | Conditional dismissal field is complete. |
| Dismissed player without wicket flag | 0 | 0 | PASS | Reverse condition reconciles. |
| Non-wicket rows with dismissal details | 0 | 0 | PASS | Conditional nulls are preserved. |
| Caught/stumped rows missing fielder | 0 | 0 | PASS | Fielder required for these source categories. |
| Fielder populated for inapplicable type | 0 | 0 | PASS | Named fielders appear only for caught, run out, or stumped. |
| Run-out rows missing fielder | 0 preferred | 181 | WARN | The source omits the fielder; no name can be defensibly inferred. |

`caught and bowled` does not require the `fielder` field because the bowler is already explicit. Bowled, lbw, hit-wicket, retired, and obstructing-field records also do not require a fielder.

## 13. Legal-ball validation

| Check | Expected | Actual | Status | Explanation |
|---|---:|---:|---|---|
| Legal-rule mismatches | 0 | 0 | PASS | Only wides/no-balls are illegal. |
| `legal_ball` mismatches | 0 | 0 | PASS | Integer and boolean flags agree. |
| Total classified deliveries | 260,920 | 260,920 | PASS | Legal plus illegal equals total. |
| Legal deliveries | 251,471 | 251,471 | PASS | Matches Phase 4 baseline. |
| Illegal deliveries | 9,449 | 9,449 | PASS | Matches Phase 4 baseline. |
| Wides | 8,380 | 8,380 | PASS | Source extras category. |
| No-balls | 1,069 | 1,069 | PASS | Source extras category. |
| Wides + no-balls | 9,449 | 9,449 | PASS | Exact because this dataset stores one extras type per row. |
| Other extras classified illegally | 0 | 0 | PASS | Byes, leg-byes, and penalties remain legal. |
| Rows with `ball > 6` preserved | 9,340 | 9,340 | PASS | These values are recorded sequence positions, not automatic errors. |

## 14. Match-outcome validation

| Check | Expected | Actual | Status | Explanation |
|---|---:|---:|---|---|
| Decided matches missing winner | 0 | 0 | PASS | Super-over ties retain source winners. |
| No-results with populated winner | 0 | 0 | PASS | Five structural winner nulls preserved. |
| Ties | 14 | 14 | PASS | Baseline reconciles. |
| No-results | 5 | 5 | PASS | Baseline reconciles. |
| Margin semantic errors | 0 | 0 | PASS | Only run/wicket wins have margins. |
| Super-over matches | 14 | 14 | PASS | Domain is only `Y`/`N`. |
| Tie/super-over mismatches | 0 | 0 | PASS | All 14 source ties correspond to super overs. |
| Invalid non-null methods | 0 | 0 | PASS | All 21 non-null methods are `D/L`. |

## 15. Toss validation

| Check | Expected | Actual | Status | Explanation |
|---|---|---|---|---|
| Toss decisions | `bat`, `field` | `bat`, `field` | PASS | No unexpected category. |
| Decided matches | 1,090 | 1,090 | PASS | No-results excluded. |
| Toss winner also won | 554 | 554 | PASS | Reconciles with EDA. |
| Toss-winner match-win rate | 50.8% | 50.8% | PASS | Descriptive association only, not causation. |

## 16. Cross-table validation

| Check | Expected | Actual | Status | Explanation |
|---|---:|---:|---|---|
| Invalid delivery batting-team rows | 0 | 0 | PASS | Team belongs to corresponding match. |
| Invalid delivery bowling-team rows | 0 | 0 | PASS | Team belongs to corresponding match. |
| Per-match participant-set differences | 0 | 0 | PASS | No unexpected team appears in deliveries. |

## 17. Cleaning reconciliation

| Check | Expected | Actual | Status | Explanation |
|---|---|---|---|---|
| Team labels | 19 → 15 | 19 → 15 | PASS | Four documented mappings only. |
| Venue labels | 58 → 40 | 58 → 40 | PASS | Eighteen documented mappings only. |
| City labels | 36 → 35 | 36 → 35 | PASS | Bangalore/Bengaluru consolidated. |
| Missing city values | 51 raw → 0 standard | 51 → 0 | PASS | Only Dubai/Sharjah venue fills. |

## 18. Raw-file integrity

| File | Expected SHA-256 | Actual SHA-256 | Status | Explanation |
|---|---|---|---|---|
| `matches.csv` | `8a0394246d2a76b44526565f2245d8f4feff91babe57ab16676a2c3d67aa0846` | `8a0394246d2a76b44526565f2245d8f4feff91babe57ab16676a2c3d67aa0846` | PASS | Raw match data unchanged. |
| `deliveries.csv` | `142236ea52950795dab266d4aa392c7645bd1a0db4704f0b8058afd96e24e2c2` | `142236ea52950795dab266d4aa392c7645bd1a0db4704f0b8058afd96e24e2c2` | PASS | Raw delivery data unchanged. |

## 19. Test results

| Command | Actual result | Status |
|---|---|---|
| `.venv/Scripts/pytest -q` | 10 passed | PASS |
| `.venv/Scripts/python -m pytest -q` | 10 passed | PASS |

The direct pytest launcher initially exposed an import-path portability problem. A minimal `pytest.ini` now declares the repository root as the Python path; no data or validation rule was weakened.

## 20. Final PASS / WARN / FAIL summary

| Status | Checks |
|---|---:|
| PASS | 77 |
| WARN | 2 |
| FAIL | 0 |

**Overall result: PASS WITH DOCUMENTED WARNINGS.** The cleaned datasets are structurally and logically suitable for subsequent analytics work.

## 21. Known limitations

- Player identity is name-based because no stable player master ID is supplied.
- Historical stadium renames remain conservatively separate.
- Dr DY Patil Sports Academy retains two source city labels.
- Some run-out records omit the fielder.
- CSV serialization requires explicit date parsing when data is loaded.

## 22. Issues discovered

No blocking data defects were found. Two warnings were discovered and intentionally retained:

1. Dr DY Patil Sports Academy has both Mumbai and Navi Mumbai source city labels.
2. 181 run-out rows do not name a fielder.

Neither warning changes row grain, match identity, scoring, legal-ball calculations, or team integrity.

## 23. Raw-data statement

Phase 5 did not modify either raw CSV or either cleaned CSV. No synthetic data, SQL database, Tableau dataset, or Phase 6 metric was created.
