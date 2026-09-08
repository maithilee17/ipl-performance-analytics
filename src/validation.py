"""Transparent Phase 5 validation for cleaned IPL data.

The functions in this module are read-only. They return PASS/WARN/FAIL rows
with expected and actual results; they never repair or rewrite a dataset.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pandas as pd
from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_integer_dtype, is_numeric_dtype

from src.data_cleaning import (
    CITY_NAME_MAP,
    EXPECTED_SEASON_LABELS,
    ILLEGAL_DELIVERY_EXTRA_TYPES,
    TEAM_NAME_MAP,
    VENUE_NAME_MAP,
    VENUE_TO_CITY_FILL,
)
from src.data_loader import get_data_paths, get_project_root, load_clean_data, load_raw_data


EXPECTED_RAW_HASHES = {
    "matches.csv": "8a0394246d2a76b44526565f2245d8f4feff91babe57ab16676a2c3d67aa0846",
    "deliveries.csv": "142236ea52950795dab266d4aa392c7645bd1a0db4704f0b8058afd96e24e2c2",
}

EXPECTED_MATCH_COLUMNS = [
    "match_id", "season_raw", "season_standard", "season_start_year",
    "date_raw", "match_date", "match_year", "match_month", "match_day",
    "match_type", "city_raw", "city_standard", "venue_raw",
    "venue_standard", "team1_raw", "team1_standard", "team2_raw",
    "team2_standard", "toss_winner_raw", "toss_winner_standard",
    "toss_decision", "winner_raw", "winner_standard", "player_of_match",
    "result", "result_margin", "target_runs", "target_overs", "super_over",
    "method", "umpire1", "umpire2",
]

EXPECTED_DELIVERY_COLUMNS = [
    "match_id", "inning", "batting_team_raw", "batting_team_standard",
    "bowling_team_raw", "bowling_team_standard", "over", "ball", "batter",
    "bowler", "non_striker", "batsman_runs", "extra_runs", "total_runs",
    "extras_type", "is_wicket", "player_dismissed", "dismissal_kind",
    "fielder", "is_legal_delivery", "legal_ball",
]

VALID_MATCH_TYPES = {
    "League", "Final", "Qualifier 1", "Qualifier 2", "Eliminator",
    "Semi Final", "Elimination Final", "3rd Place Play-Off",
}
VALID_RESULTS = {"runs", "wickets", "tie", "no result"}
VALID_TOSS_DECISIONS = {"bat", "field"}
VALID_SUPER_OVER_VALUES = {"Y", "N"}
VALID_METHOD_VALUES = {"D/L"}
VALID_EXTRAS_TYPES = {"wides", "legbyes", "noballs", "byes", "penalty"}
VALID_DISMISSAL_TYPES = {
    "bowled", "caught", "caught and bowled", "hit wicket", "lbw",
    "obstructing the field", "retired hurt", "retired out", "run out",
    "stumped",
}
FIELDER_REQUIRED_TYPES = {"caught", "stumped"}
FIELDER_ALLOWED_TYPES = {"caught", "run out", "stumped"}


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _add(
    rows: list[dict[str, object]],
    category: str,
    check: str,
    expected: object,
    actual: object,
    passed: bool,
    explanation: str,
) -> None:
    rows.append({
        "category": category,
        "check": check,
        "expected": str(expected),
        "actual": str(actual),
        "status": "PASS" if bool(passed) else "FAIL",
        "explanation": explanation,
    })


def _warn(
    rows: list[dict[str, object]],
    category: str,
    check: str,
    expected: object,
    actual: object,
    explanation: str,
) -> None:
    rows.append({
        "category": category,
        "check": check,
        "expected": str(expected),
        "actual": str(actual),
        "status": "WARN",
        "explanation": explanation,
    })


def _blank_string_count(frame: pd.DataFrame) -> int:
    count = 0
    for column in frame.select_dtypes(include=["object", "string"]).columns:
        count += int(frame[column].dropna().astype(str).str.strip().eq("").sum())
    return count


def _season_matches_date(row: pd.Series) -> bool:
    label = str(row["season_standard"])
    match_year = int(row["match_year"])
    if "/" not in label:
        return match_year == int(label)
    start_year = int(label[:4])
    short_end_year = int(label.split("/")[1])
    end_year = (start_year // 100) * 100 + short_end_year
    if end_year < start_year:
        end_year += 100
    return match_year in {start_year, end_year}


def run_validation(
    matches: pd.DataFrame,
    deliveries: pd.DataFrame,
    matches_raw: pd.DataFrame,
    deliveries_raw: pd.DataFrame,
    root: Path | None = None,
) -> pd.DataFrame:
    """Run the complete Phase 5 validation suite and return result rows."""
    root = Path(root) if root is not None else get_project_root()
    rows: list[dict[str, object]] = []

    # Schema and serialization types.
    match_missing = sorted(set(EXPECTED_MATCH_COLUMNS) - set(matches.columns))
    match_extra = sorted(set(matches.columns) - set(EXPECTED_MATCH_COLUMNS))
    delivery_missing = sorted(set(EXPECTED_DELIVERY_COLUMNS) - set(deliveries.columns))
    delivery_extra = sorted(set(deliveries.columns) - set(EXPECTED_DELIVERY_COLUMNS))
    _add(rows, "Schema", "Match columns match contract", "0 missing; 0 unexpected", f"{len(match_missing)} missing; {len(match_extra)} unexpected", not match_missing and not match_extra, "Exact Phase 4 match schema is required.")
    _add(rows, "Schema", "Delivery columns match contract", "0 missing; 0 unexpected", f"{len(delivery_missing)} missing; {len(delivery_extra)} unexpected", not delivery_missing and not delivery_extra, "Exact Phase 4 delivery schema is required.")
    match_integer_columns = ["match_id", "season_start_year", "match_year", "match_month", "match_day"]
    delivery_integer_columns = ["match_id", "inning", "over", "ball", "batsman_runs", "extra_runs", "total_runs", "is_wicket", "legal_ball"]
    bad_match_integer_types = [c for c in match_integer_columns if not is_integer_dtype(matches[c])]
    bad_delivery_integer_types = [c for c in delivery_integer_columns if not is_integer_dtype(deliveries[c])]
    _add(rows, "Schema", "Match identifier/calendar fields are integer-like", "all integer-like", bad_match_integer_types or "all integer-like", not bad_match_integer_types, "CSV-compatible integer inference is sufficient.")
    _add(rows, "Schema", "Delivery identifier/run fields are integer-like", "all integer-like", bad_delivery_integer_types or "all integer-like", not bad_delivery_integer_types, "Includes match, innings position, runs, wicket, and legal-ball fields.")
    numeric_match_columns = ["result_margin", "target_runs", "target_overs"]
    bad_numeric_types = [c for c in numeric_match_columns if not is_numeric_dtype(matches[c])]
    _add(rows, "Schema", "Nullable match measures are numeric", "all numeric", bad_numeric_types or "all numeric", not bad_numeric_types, "Float inference is expected because CSV nulls coexist with numeric values.")
    _add(rows, "Schema", "match_date is parsed datetime", "datetime-like", str(matches["match_date"].dtype), is_datetime64_any_dtype(matches["match_date"]), "The loader restores the serialized ISO date.")
    _add(rows, "Schema", "is_legal_delivery is boolean", "bool", str(deliveries["is_legal_delivery"].dtype), is_bool_dtype(deliveries["is_legal_delivery"]), "CSV values infer cleanly as boolean.")
    _add(rows, "Schema", "No accidental blank strings", 0, _blank_string_count(matches) + _blank_string_count(deliveries), _blank_string_count(matches) + _blank_string_count(deliveries) == 0, "Nulls are allowed where documented; blank/whitespace-only strings are not.")
    categorical_domains = {
        "match_type": VALID_MATCH_TYPES,
        "result": VALID_RESULTS,
        "toss_decision": VALID_TOSS_DECISIONS,
        "super_over": VALID_SUPER_OVER_VALUES,
    }
    domain_issues = sum(len(set(matches[column].dropna()) - valid) for column, valid in categorical_domains.items())
    domain_issues += len(set(matches["method"].dropna()) - VALID_METHOD_VALUES)
    domain_issues += len(set(deliveries["extras_type"].dropna()) - VALID_EXTRAS_TYPES)
    domain_issues += len(set(deliveries["dismissal_kind"].dropna()) - VALID_DISMISSAL_TYPES)
    _add(rows, "Schema", "Categorical domains contain documented values", 0, domain_issues, domain_issues == 0, "Checks match type, result, toss, super over, method, extras, and dismissals.")

    # Row counts and keys.
    _add(rows, "Row counts", "Match rows preserved", 1095, len(matches), len(matches) == 1095, "No match should be added or removed.")
    _add(rows, "Row counts", "Delivery rows preserved", 260920, len(deliveries), len(deliveries) == 260920, "One row remains one recorded delivery.")
    _add(rows, "Primary keys", "Match IDs are non-null", 0, int(matches["match_id"].isna().sum()), matches["match_id"].notna().all(), "Cleaned primary key.")
    _add(rows, "Primary keys", "Match IDs are unique", 0, int(matches["match_id"].duplicated().sum()), matches["match_id"].is_unique, "One record per match.")
    _add(rows, "Primary keys", "Delivery match IDs are non-null", 0, int(deliveries["match_id"].isna().sum()), deliveries["match_id"].notna().all(), "Required foreign key.")
    delivery_key = ["match_id", "inning", "over", "ball"]
    delivery_key_duplicates = int(deliveries.duplicated(delivery_key).sum())
    _add(rows, "Primary keys", "Delivery composite key is unique", 0, delivery_key_duplicates, delivery_key_duplicates == 0, "Validated at recorded-delivery grain.")

    # Referential integrity and cross-table consistency.
    match_ids = set(matches["match_id"])
    delivery_ids = set(deliveries["match_id"])
    orphan_ids = delivery_ids - match_ids
    matches_without_deliveries = match_ids - delivery_ids
    orphan_rows = int(deliveries["match_id"].isin(orphan_ids).sum())
    _add(rows, "Referential integrity", "Orphan delivery match IDs", 0, len(orphan_ids), not orphan_ids, f"{orphan_rows} delivery rows reference orphan IDs.")
    _add(rows, "Referential integrity", "Matches without deliveries", 0, len(matches_without_deliveries), not matches_without_deliveries, "Every cleaned match must have delivery data.")
    participant_lookup = matches.set_index("match_id")[["team1_standard", "team2_standard"]]
    delivery_team_rows = deliveries[["match_id", "batting_team_standard", "bowling_team_standard"]].merge(participant_lookup, left_on="match_id", right_index=True, how="left", validate="many_to_one")
    batting_valid = delivery_team_rows["batting_team_standard"].eq(delivery_team_rows["team1_standard"]) | delivery_team_rows["batting_team_standard"].eq(delivery_team_rows["team2_standard"])
    bowling_valid = delivery_team_rows["bowling_team_standard"].eq(delivery_team_rows["team1_standard"]) | delivery_team_rows["bowling_team_standard"].eq(delivery_team_rows["team2_standard"])
    _add(rows, "Cross-table consistency", "Delivery batting team belongs to match", 0, int((~batting_valid).sum()), batting_valid.all(), "Uses standardized match participants.")
    _add(rows, "Cross-table consistency", "Delivery bowling team belongs to match", 0, int((~bowling_valid).sum()), bowling_valid.all(), "Uses standardized match participants.")
    match_team_sets = participant_lookup.apply(lambda row: frozenset(row), axis=1)
    delivery_team_sets = deliveries.groupby("match_id").apply(lambda group: frozenset(pd.concat([group["batting_team_standard"], group["bowling_team_standard"]]).dropna().unique()), include_groups=False)
    team_set_mismatches = sum(match_team_sets.loc[mid] != delivery_team_sets.loc[mid] for mid in match_ids)
    _add(rows, "Cross-table consistency", "Per-match team sets agree", 0, team_set_mismatches, team_set_mismatches == 0, "No unexpected team appears in a match's deliveries.")

    # Team mapping and match logic.
    standard_team_columns = ["team1_standard", "team2_standard", "toss_winner_standard", "winner_standard"]
    standard_delivery_team_columns = ["batting_team_standard", "bowling_team_standard"]
    standard_teams = set(pd.concat([matches[c] for c in ["team1_standard", "team2_standard"]]).dropna())
    old_names = set(TEAM_NAME_MAP)
    old_name_occurrences = sum(int(matches[c].isin(old_names).sum()) for c in standard_team_columns) + sum(int(deliveries[c].isin(old_names).sum()) for c in standard_delivery_team_columns)
    _add(rows, "Teams", "Standardized team domain has expected size", 15, len(standard_teams), len(standard_teams) == 15, "Four documented consolidations reduce 19 raw labels to 15.")
    _add(rows, "Teams", "Old team labels absent from standard fields", 0, old_name_occurrences, old_name_occurrences == 0, "Raw audit fields intentionally retain original labels.")
    _add(rows, "Teams", "Match participants differ", 0, int(matches["team1_standard"].eq(matches["team2_standard"]).sum()), matches["team1_standard"].ne(matches["team2_standard"]).all(), "A team cannot play itself.")
    _add(rows, "Teams", "Delivery batting and bowling teams differ", 0, int(deliveries["batting_team_standard"].eq(deliveries["bowling_team_standard"]).sum()), deliveries["batting_team_standard"].ne(deliveries["bowling_team_standard"]).all(), "Opposing teams are required on every delivery.")
    toss_team_valid = matches["toss_winner_standard"].eq(matches["team1_standard"]) | matches["toss_winner_standard"].eq(matches["team2_standard"])
    winner_team_valid = matches["winner_standard"].isna() | matches["winner_standard"].eq(matches["team1_standard"]) | matches["winner_standard"].eq(matches["team2_standard"])
    _add(rows, "Teams", "Toss winner is a participant", 0, int((~toss_team_valid).sum()), toss_team_valid.all(), "Checked after standardization.")
    _add(rows, "Teams", "Winner is a participant when present", 0, int((~winner_team_valid).sum()), winner_team_valid.all(), "No-result null winners are allowed.")
    mapping_mismatches = 0
    for raw_column, standard_column in [("team1_raw", "team1_standard"), ("team2_raw", "team2_standard"), ("toss_winner_raw", "toss_winner_standard"), ("winner_raw", "winner_standard")]:
        expected = matches[raw_column].replace(TEAM_NAME_MAP)
        mapping_mismatches += int(matches[standard_column].fillna("<NULL>").ne(expected.fillna("<NULL>")).sum())
    for raw_column, standard_column in [("batting_team_raw", "batting_team_standard"), ("bowling_team_raw", "bowling_team_standard")]:
        expected = deliveries[raw_column].replace(TEAM_NAME_MAP)
        mapping_mismatches += int(deliveries[standard_column].fillna("<NULL>").ne(expected.fillna("<NULL>")).sum())
    _add(rows, "Teams", "Four documented mappings are applied consistently", 0, mapping_mismatches, mapping_mismatches == 0, "Checks all six mapped match/delivery fields.")

    # Venue and city.
    venue_mismatches = int(matches["venue_standard"].ne(matches["venue_raw"].replace(VENUE_NAME_MAP)).sum())
    _add(rows, "Venue and city", "Venue mapping matches documented rules", 0, venue_mismatches, venue_mismatches == 0, "No Phase 5 venue mappings are introduced.")
    _add(rows, "Venue and city", "Standard venue labels are non-empty", 0, int(matches["venue_standard"].isna().sum()) + int(matches["venue_standard"].astype(str).str.strip().eq("").sum()), matches["venue_standard"].notna().all() and not matches["venue_standard"].astype(str).str.strip().eq("").any(), "Every match retains a venue.")
    unresolved_bangalore = int(matches["city_standard"].eq("Bangalore").sum())
    _add(rows, "Venue and city", "Bangalore is absent from standard city", 0, unresolved_bangalore, unresolved_bangalore == 0, "Bengaluru is the documented standard value.")
    city_mapping_errors = int(matches.loc[matches["city_raw"].notna(), "city_standard"].ne(matches.loc[matches["city_raw"].notna(), "city_raw"].replace(CITY_NAME_MAP)).sum())
    _add(rows, "Venue and city", "Non-null city mapping matches documented rule", 0, city_mapping_errors, city_mapping_errors == 0, "Only Bangalore is renamed.")
    fill_errors = 0
    fill_actual_parts = []
    for venue, city in VENUE_TO_CITY_FILL.items():
        mask = matches["city_raw"].isna() & matches["venue_standard"].eq(venue)
        errors = int(matches.loc[mask, "city_standard"].ne(city).sum())
        fill_errors += errors
        fill_actual_parts.append(f"{city}={int(mask.sum())}")
    _add(rows, "Venue and city", "Dubai/Sharjah city fills are correct", "Dubai=33; Sharjah=18; 0 errors", "; ".join(fill_actual_parts) + f"; errors={fill_errors}", fill_errors == 0 and fill_actual_parts == ["Dubai=33", "Sharjah=18"], "Only unambiguous venue-derived fills are accepted.")
    _add(rows, "Venue and city", "Standard city has no missing values", 0, int(matches["city_standard"].isna().sum()), matches["city_standard"].notna().all(), "Phase 4 filled exactly 51 supported values.")
    multi_city_venues = matches.groupby("venue_standard")["city_standard"].nunique().loc[lambda values: values.gt(1)]
    if multi_city_venues.empty:
        _add(rows, "Venue and city", "Each standard venue has one city label", 0, 0, True, "No conflicting venue/city combinations.")
    else:
        details = "; ".join(f"{venue}={count}" for venue, count in multi_city_venues.items())
        _warn(rows, "Venue and city", "Standard venues associated with multiple city labels", "0 venues", details, "Dr DY Patil inherits Mumbai and Navi Mumbai from source rows; no geography was invented or overwritten.")

    # Dates and seasons.
    _add(rows, "Dates and seasons", "All match dates are non-null", 0, int(matches["match_date"].isna().sum()), matches["match_date"].notna().all(), "Dates were parsed on load.")
    date_min, date_max = matches["match_date"].min(), matches["match_date"].max()
    expected_min, expected_max = pd.Timestamp("2008-04-18"), pd.Timestamp("2024-05-26")
    _add(rows, "Dates and seasons", "Date range matches source coverage", "2008-04-18 to 2024-05-26", f"{date_min.date()} to {date_max.date()}", date_min == expected_min and date_max == expected_max, "Observed dataset bounds, not a claim of future coverage.")
    season_domain = set(matches["season_standard"])
    _add(rows, "Dates and seasons", "Season domain is preserved", sorted(EXPECTED_SEASON_LABELS), sorted(season_domain), season_domain == EXPECTED_SEASON_LABELS, "Split-year labels remain strings.")
    season_identity_errors = int(matches["season_raw"].ne(matches["season_standard"]).sum())
    _add(rows, "Dates and seasons", "Standard season preserves raw identity", 0, season_identity_errors, season_identity_errors == 0, "No invented season mapping.")
    season_start_errors = int(matches["season_start_year"].ne(matches["season_standard"].str[:4].astype(int)).sum())
    _add(rows, "Dates and seasons", "Season start year follows documented definition", 0, season_start_errors, season_start_errors == 0, "First four digits only.")
    season_date_errors = int((~matches.apply(_season_matches_date, axis=1)).sum())
    _add(rows, "Dates and seasons", "Match year is consistent with season label", 0, season_date_errors, season_date_errors == 0, "Single-year labels equal match year; split labels permit start or end year.")
    calendar_errors = int(matches["match_year"].ne(matches["match_date"].dt.year).sum() + matches["match_month"].ne(matches["match_date"].dt.month).sum() + matches["match_day"].ne(matches["match_date"].dt.day).sum())
    _add(rows, "Dates and seasons", "Calendar components match date", 0, calendar_errors, calendar_errors == 0, "Year/month/day derived columns reconcile exactly.")

    # Runs and target reconciliation.
    negative_runs = int(deliveries[["batsman_runs", "extra_runs", "total_runs"]].lt(0).sum().sum())
    arithmetic_errors = int(deliveries["total_runs"].ne(deliveries["batsman_runs"] + deliveries["extra_runs"]).sum())
    _add(rows, "Runs", "Run values are non-negative", 0, negative_runs, negative_runs == 0, "Checks all three run columns.")
    _add(rows, "Runs", "Delivery run arithmetic reconciles", 0, arithmetic_errors, arithmetic_errors == 0, "total_runs equals batsman_runs plus extra_runs on every row.")
    numeric_total_mismatches = sum(int(deliveries[column].sum() != deliveries_raw[column].sum()) for column in ["batsman_runs", "extra_runs", "total_runs"])
    _add(rows, "Runs", "Aggregate run totals equal raw data", 0, numeric_total_mismatches, numeric_total_mismatches == 0, "Cleaning did not alter run measures.")
    innings_totals = deliveries.groupby(["match_id", "inning"], as_index=False)["total_runs"].sum()
    first_innings = innings_totals.loc[innings_totals["inning"].eq(1), ["match_id", "total_runs"]].rename(columns={"total_runs": "first_innings_runs"})
    target_check = matches[["match_id", "method", "target_runs"]].merge(first_innings, on="match_id", how="left", validate="one_to_one")
    target_eligible = target_check["target_runs"].notna() & target_check["method"].isna() & target_check["first_innings_runs"].notna()
    target_errors = int(target_check.loc[target_eligible, "target_runs"].ne(target_check.loc[target_eligible, "first_innings_runs"] + 1).sum())
    _add(rows, "Runs", "Non-D/L targets equal first-innings runs plus one", "0 mismatches among 1,071 eligible matches", f"{target_errors} mismatches among {int(target_eligible.sum()):,} eligible matches", target_errors == 0 and int(target_eligible.sum()) == 1071, "D/L and missing targets are excluded because they are not directly comparable.")

    # Wickets and conditional fielder rules.
    wicket_domain = set(deliveries["is_wicket"])
    _add(rows, "Wickets", "Wicket indicator is binary", "{0, 1}", sorted(wicket_domain), wicket_domain <= {0, 1}, "No other flags are present.")
    wicket_missing_player = int((deliveries["is_wicket"].eq(1) & deliveries["player_dismissed"].isna()).sum())
    wicket_missing_kind = int((deliveries["is_wicket"].eq(1) & deliveries["dismissal_kind"].isna()).sum())
    player_without_wicket = int((deliveries["player_dismissed"].notna() & deliveries["is_wicket"].ne(1)).sum())
    non_wicket_dismissal = int((deliveries["is_wicket"].eq(0) & (deliveries["player_dismissed"].notna() | deliveries["dismissal_kind"].notna())).sum())
    _add(rows, "Wickets", "Wicket rows have dismissed player", 0, wicket_missing_player, wicket_missing_player == 0, "Required conditional field.")
    _add(rows, "Wickets", "Wicket rows have dismissal kind", 0, wicket_missing_kind, wicket_missing_kind == 0, "Required conditional field.")
    _add(rows, "Wickets", "Dismissed-player rows have wicket flag", 0, player_without_wicket, player_without_wicket == 0, "Reverse conditional check.")
    _add(rows, "Wickets", "Non-wicket rows keep dismissal fields null", 0, non_wicket_dismissal, non_wicket_dismissal == 0, "Confirms conditional null semantics.")
    fielder_required_missing = int((deliveries["dismissal_kind"].isin(FIELDER_REQUIRED_TYPES) & deliveries["fielder"].isna()).sum())
    invalid_fielder_type = int((deliveries["fielder"].notna() & ~deliveries["dismissal_kind"].isin(FIELDER_ALLOWED_TYPES)).sum())
    _add(rows, "Wickets", "Caught/stumped rows name a fielder", 0, fielder_required_missing, fielder_required_missing == 0, "Caught-and-bowled is excluded because the bowler is implicit.")
    _add(rows, "Wickets", "Populated fielders use applicable dismissal types", 0, invalid_fielder_type, invalid_fielder_type == 0, "Only caught, run out, and stumped rows name fielders.")
    run_out_missing_fielder = int((deliveries["dismissal_kind"].eq("run out") & deliveries["fielder"].isna()).sum())
    if run_out_missing_fielder:
        _warn(rows, "Wickets", "Run-out rows without named fielder", 0, run_out_missing_fielder, "The source omits a fielder on some run outs; values remain null rather than invented.")
    else:
        _add(rows, "Wickets", "Run-out rows without named fielder", 0, 0, True, "All run outs name a fielder.")

    # Legal delivery rules.
    expected_legal = ~deliveries["extras_type"].isin(ILLEGAL_DELIVERY_EXTRA_TYPES)
    legal_logic_errors = int(deliveries["is_legal_delivery"].ne(expected_legal).sum())
    legal_ball_errors = int(deliveries["legal_ball"].ne(deliveries["is_legal_delivery"].astype(int)).sum())
    legal_count = int(deliveries["is_legal_delivery"].sum())
    illegal_count = int((~deliveries["is_legal_delivery"]).sum())
    wide_count = int(deliveries["extras_type"].eq("wides").sum())
    no_ball_count = int(deliveries["extras_type"].eq("noballs").sum())
    other_extra_illegal = int((deliveries["extras_type"].notna() & ~deliveries["extras_type"].isin(ILLEGAL_DELIVERY_EXTRA_TYPES) & ~deliveries["is_legal_delivery"]).sum())
    _add(rows, "Legal deliveries", "Legal flag follows extras rule", 0, legal_logic_errors, legal_logic_errors == 0, "Only wides and no-balls are illegal.")
    _add(rows, "Legal deliveries", "legal_ball matches boolean flag", 0, legal_ball_errors, legal_ball_errors == 0, "Integer indicator is safe for aggregation.")
    _add(rows, "Legal deliveries", "Legal plus illegal equals total", 260920, legal_count + illegal_count, legal_count + illegal_count == len(deliveries) == 260920, "Complete classification.")
    _add(rows, "Legal deliveries", "Legal-delivery count matches Phase 4", 251471, legal_count, legal_count == 251471, "Documented baseline.")
    _add(rows, "Legal deliveries", "Illegal-delivery count matches Phase 4", 9449, illegal_count, illegal_count == 9449, "Documented baseline.")
    _add(rows, "Legal deliveries", "Wides plus no-balls reconcile to illegal", 9449, wide_count + no_ball_count, wide_count == 8380 and no_ball_count == 1069 and wide_count + no_ball_count == illegal_count, "The dataset stores one extras type per row, supporting exact reconciliation.")
    _add(rows, "Legal deliveries", "Other extras remain legal", 0, other_extra_illegal, other_extra_illegal == 0, "Byes, leg-byes, and penalties are not misclassified.")
    ball_over_six = int(deliveries["ball"].gt(6).sum())
    raw_ball_over_six = int(deliveries_raw["ball"].gt(6).sum())
    _add(rows, "Legal deliveries", "Ball > 6 rows are preserved", 9340, ball_over_six, ball_over_six == raw_ball_over_six == 9340, "Recorded sequence values are not treated as invalid.")

    # Outcomes and tosses.
    result_counts = matches["result"].value_counts()
    winner_missing_decided = int((matches["winner_standard"].isna() & matches["result"].ne("no result")).sum())
    winner_present_no_result = int((matches["winner_standard"].notna() & matches["result"].eq("no result")).sum())
    _add(rows, "Match outcomes", "Decided matches have winners", 0, winner_missing_decided, winner_missing_decided == 0, "Ties decided by super over retain a winner in this source.")
    _add(rows, "Match outcomes", "No-results have null winners", 0, winner_present_no_result, winner_present_no_result == 0 and matches.loc[matches["result"].eq("no result"), "winner_standard"].isna().all(), "Preserves five structural nulls.")
    outcome_baseline_ok = result_counts.get("tie", 0) == 14 and result_counts.get("no result", 0) == 5
    _add(rows, "Match outcomes", "Tie and no-result counts match baseline", "ties=14; no-results=5", f"ties={result_counts.get('tie', 0)}; no-results={result_counts.get('no result', 0)}", outcome_baseline_ok, "No outcomes changed during cleaning.")
    margin_errors = int((matches["result"].isin(["runs", "wickets"]) & matches["result_margin"].isna()).sum() + (matches["result"].isin(["tie", "no result"]) & matches["result_margin"].notna()).sum())
    _add(rows, "Match outcomes", "Result margin is populated only when meaningful", 0, margin_errors, margin_errors == 0, "Run/wicket wins have margins; ties/no-results do not.")
    super_domain = set(matches["super_over"])
    super_count = int(matches["super_over"].eq("Y").sum())
    _add(rows, "Match outcomes", "Super-over values and count are valid", "{N, Y}; Y=14", f"{sorted(super_domain)}; Y={super_count}", super_domain == VALID_SUPER_OVER_VALUES and super_count == 14, "Matches the Phase 1/4 baseline.")
    tie_super_mismatch = int((matches["result"].eq("tie") ^ matches["super_over"].eq("Y")).sum())
    _add(rows, "Match outcomes", "Tie and super-over indicators reconcile", 0, tie_super_mismatch, tie_super_mismatch == 0, "All 14 source ties correspond to the 14 super-over indicators.")
    invalid_method_rows = int((matches["method"].notna() & matches["method"].ne("D/L")).sum())
    _add(rows, "Match outcomes", "Method is null or documented D/L", 0, invalid_method_rows, invalid_method_rows == 0, f"D/L is populated on {int(matches['method'].eq('D/L').sum())} matches.")
    toss_domain = set(matches["toss_decision"])
    _add(rows, "Toss", "Toss decisions use documented values", sorted(VALID_TOSS_DECISIONS), sorted(toss_domain), toss_domain == VALID_TOSS_DECISIONS, "No unexpected decision category.")
    decided = matches.loc[matches["winner_standard"].notna()]
    toss_winner_won = decided["toss_winner_standard"].eq(decided["winner_standard"])
    toss_count, toss_wins = len(decided), int(toss_winner_won.sum())
    toss_rate = toss_winner_won.mean() * 100
    _add(rows, "Toss", "Toss outcome reconciles with EDA baseline", "1,090 decided; 554 wins; 50.8%", f"{toss_count:,} decided; {toss_wins} wins; {toss_rate:.1f}%", toss_count == 1090 and toss_wins == 554 and round(toss_rate, 1) == 50.8, "Association only; no causal claim.")

    # Phase 4 reconciliation and raw-vs-clean data loss.
    raw_team_count = len(set(matches_raw["team1"]) | set(matches_raw["team2"]))
    raw_venue_count, raw_city_count = matches_raw["venue"].nunique(), matches_raw["city"].nunique()
    _add(rows, "Cleaning reconciliation", "Team labels reconcile", "19 -> 15", f"{raw_team_count} -> {len(standard_teams)}", raw_team_count == 19 and len(standard_teams) == 15, "Four mappings only.")
    _add(rows, "Cleaning reconciliation", "Venue labels reconcile", "58 -> 40", f"{raw_venue_count} -> {matches['venue_standard'].nunique()}", raw_venue_count == 58 and matches["venue_standard"].nunique() == 40, "Eighteen documented mappings only.")
    _add(rows, "Cleaning reconciliation", "City labels reconcile", "36 -> 35", f"{raw_city_count} -> {matches['city_standard'].nunique()}", raw_city_count == 36 and matches["city_standard"].nunique() == 35, "Bangalore/Bengaluru consolidation.")
    _add(rows, "Cleaning reconciliation", "Missing standard cities reconcile", "51 raw -> 0 standard", f"{int(matches_raw['city'].isna().sum())} raw -> {int(matches['city_standard'].isna().sum())} standard", matches_raw["city"].isna().sum() == 51 and matches["city_standard"].isna().sum() == 0, "Only Dubai and Sharjah fills.")
    _add(rows, "Data loss", "Match ID sequence is preserved", "identical", "identical" if matches["match_id"].tolist() == matches_raw["id"].tolist() else "different", matches["match_id"].tolist() == matches_raw["id"].tolist(), "Detects dropped, duplicated, or reordered match records.")
    clean_delivery_keys = deliveries[delivery_key].reset_index(drop=True)
    raw_delivery_keys = deliveries_raw[delivery_key].reset_index(drop=True)
    keys_equal = clean_delivery_keys.equals(raw_delivery_keys)
    _add(rows, "Data loss", "Delivery key sequence is preserved", "identical", "identical" if keys_equal else "different", keys_equal, "Detects dropped, duplicated, or reordered deliveries.")
    null_preservation_pairs = [
        (matches_raw["winner"], matches["winner_raw"]),
        (matches_raw["player_of_match"], matches["player_of_match"]),
        (matches_raw["result_margin"], matches["result_margin"]),
        (matches_raw["method"], matches["method"]),
        (deliveries_raw["extras_type"], deliveries["extras_type"]),
        (deliveries_raw["player_dismissed"], deliveries["player_dismissed"]),
        (deliveries_raw["dismissal_kind"], deliveries["dismissal_kind"]),
        (deliveries_raw["fielder"], deliveries["fielder"]),
    ]
    null_count_changes = sum(int(left.isna().sum() != right.isna().sum()) for left, right in null_preservation_pairs)
    _add(rows, "Data loss", "Conditional null counts are preserved", 0, null_count_changes, null_count_changes == 0, "Excludes city_standard, the only documented fill target.")

    # Raw immutability.
    paths = get_data_paths(root)
    for name, key in [("matches.csv", "matches_raw"), ("deliveries.csv", "deliveries_raw")]:
        actual_hash = _hash_file(paths[key])
        expected_hash = EXPECTED_RAW_HASHES[name]
        _add(rows, "Raw integrity", f"{name} SHA-256 matches baseline", expected_hash, actual_hash, actual_hash == expected_hash, "Raw data must remain immutable.")

    return pd.DataFrame(rows, columns=["category", "check", "expected", "actual", "status", "explanation"])


def validate_project(root: Path | None = None) -> pd.DataFrame:
    """Load the current project files and run all Phase 5 checks."""
    root = Path(root) if root is not None else get_project_root()
    matches, deliveries = load_clean_data(root)
    matches_raw, deliveries_raw = load_raw_data(root)
    return run_validation(matches, deliveries, matches_raw, deliveries_raw, root)
