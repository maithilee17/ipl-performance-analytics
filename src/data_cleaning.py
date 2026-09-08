"""Reusable cleaning functions for the IPL match and delivery datasets.

The module never edits files under ``data/raw``. Every transformation works on
a copy and cleaned outputs are written only when ``save_clean_data`` is called.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_loader import get_project_root, load_raw_data


TEAM_NAME_MAP = {
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Rising Pune Supergiants": "Rising Pune Supergiant",
}

# Only clear punctuation/city-suffix variants and the explicitly reviewed
# Mohali stadium naming variants are combined. Historical venue renames that
# require a broader identity policy remain separate.
VENUE_NAME_MAP = {
    "Arun Jaitley Stadium, Delhi": "Arun Jaitley Stadium",
    "Brabourne Stadium, Mumbai": "Brabourne Stadium",
    "Dr DY Patil Sports Academy, Mumbai": "Dr DY Patil Sports Academy",
    "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium, Visakhapatnam":
        "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium",
    "Eden Gardens, Kolkata": "Eden Gardens",
    "Himachal Pradesh Cricket Association Stadium, Dharamsala":
        "Himachal Pradesh Cricket Association Stadium",
    "M Chinnaswamy Stadium, Bengaluru": "M Chinnaswamy Stadium",
    "M.Chinnaswamy Stadium": "M Chinnaswamy Stadium",
    "MA Chidambaram Stadium, Chepauk": "MA Chidambaram Stadium",
    "MA Chidambaram Stadium, Chepauk, Chennai": "MA Chidambaram Stadium",
    "Maharashtra Cricket Association Stadium, Pune":
        "Maharashtra Cricket Association Stadium",
    "Punjab Cricket Association IS Bindra Stadium, Mohali":
        "Punjab Cricket Association IS Bindra Stadium",
    "Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh":
        "Punjab Cricket Association IS Bindra Stadium",
    "Punjab Cricket Association Stadium, Mohali":
        "Punjab Cricket Association IS Bindra Stadium",
    "Rajiv Gandhi International Stadium, Uppal":
        "Rajiv Gandhi International Stadium",
    "Rajiv Gandhi International Stadium, Uppal, Hyderabad":
        "Rajiv Gandhi International Stadium",
    "Sawai Mansingh Stadium, Jaipur": "Sawai Mansingh Stadium",
    "Wankhede Stadium, Mumbai": "Wankhede Stadium",
}

CITY_NAME_MAP = {"Bangalore": "Bengaluru"}

# Missing cities are filled only for venues whose location is explicit and
# confirmed by other non-null rows in the same raw dataset.
VENUE_TO_CITY_FILL = {
    "Dubai International Cricket Stadium": "Dubai",
    "Sharjah Cricket Stadium": "Sharjah",
}

EXPECTED_SEASON_LABELS = {
    "2007/08", "2009", "2009/10", "2011", "2012", "2013", "2014",
    "2015", "2016", "2017", "2018", "2019", "2020/21", "2021",
    "2022", "2023", "2024",
}

ILLEGAL_DELIVERY_EXTRA_TYPES = {"wides", "noballs"}


def clean_matches(matches: pd.DataFrame) -> pd.DataFrame:
    """Create a cleaned match-level copy with auditable raw dimensions."""
    cleaned = matches.copy(deep=True).rename(
        columns={
            "id": "match_id",
            "season": "season_raw",
            "date": "date_raw",
            "city": "city_raw",
            "venue": "venue_raw",
            "team1": "team1_raw",
            "team2": "team2_raw",
            "toss_winner": "toss_winner_raw",
            "winner": "winner_raw",
        }
    )

    cleaned["match_date"] = pd.to_datetime(
        cleaned["date_raw"], format="%Y-%m-%d", errors="coerce"
    )
    if cleaned["match_date"].isna().any():
        invalid_count = int(cleaned["match_date"].isna().sum())
        raise ValueError(f"Date parsing produced {invalid_count} null values.")
    cleaned["match_year"] = cleaned["match_date"].dt.year.astype("int64")
    cleaned["match_month"] = cleaned["match_date"].dt.month.astype("int64")
    cleaned["match_day"] = cleaned["match_date"].dt.day.astype("int64")

    # The standard label preserves the supplied season identity; the numeric
    # helper is explicitly the first calendar year in that label.
    cleaned["season_raw"] = cleaned["season_raw"].astype("string")
    cleaned["season_standard"] = cleaned["season_raw"].str.strip()
    cleaned["season_start_year"] = (
        cleaned["season_standard"].str.slice(0, 4).astype("int64")
    )

    for source in ["team1_raw", "team2_raw", "toss_winner_raw", "winner_raw"]:
        standard = source.replace("_raw", "_standard")
        cleaned[source] = cleaned[source].astype("string")
        cleaned[standard] = cleaned[source].replace(TEAM_NAME_MAP)

    cleaned["venue_raw"] = cleaned["venue_raw"].astype("string")
    cleaned["venue_standard"] = cleaned["venue_raw"].replace(VENUE_NAME_MAP)

    cleaned["city_raw"] = cleaned["city_raw"].astype("string")
    cleaned["city_standard"] = cleaned["city_raw"].replace(CITY_NAME_MAP)
    for venue, city in VENUE_TO_CITY_FILL.items():
        fill_mask = cleaned["city_standard"].isna() & cleaned["venue_standard"].eq(venue)
        cleaned.loc[fill_mask, "city_standard"] = city

    integer_columns = ["match_id", "match_year", "match_month", "match_day", "season_start_year"]
    cleaned[integer_columns] = cleaned[integer_columns].astype("int64")

    leading_columns = [
        "match_id", "season_raw", "season_standard", "season_start_year",
        "date_raw", "match_date", "match_year", "match_month", "match_day",
        "match_type", "city_raw", "city_standard", "venue_raw", "venue_standard",
        "team1_raw", "team1_standard", "team2_raw", "team2_standard",
        "toss_winner_raw", "toss_winner_standard", "toss_decision",
        "winner_raw", "winner_standard",
    ]
    remaining_columns = [column for column in cleaned.columns if column not in leading_columns]
    return cleaned[leading_columns + remaining_columns]


def clean_deliveries(deliveries: pd.DataFrame) -> pd.DataFrame:
    """Create a cleaned delivery-level copy while preserving every row."""
    cleaned = deliveries.copy(deep=True).rename(
        columns={
            "batting_team": "batting_team_raw",
            "bowling_team": "bowling_team_raw",
        }
    )

    for source in ["batting_team_raw", "bowling_team_raw"]:
        standard = source.replace("_raw", "_standard")
        cleaned[source] = cleaned[source].astype("string")
        cleaned[standard] = cleaned[source].replace(TEAM_NAME_MAP)

    cleaned["is_legal_delivery"] = ~cleaned["extras_type"].isin(
        ILLEGAL_DELIVERY_EXTRA_TYPES
    )
    cleaned["legal_ball"] = cleaned["is_legal_delivery"].astype("int64")

    integer_columns = [
        "match_id", "inning", "over", "ball", "batsman_runs",
        "extra_runs", "total_runs", "is_wicket", "legal_ball",
    ]
    cleaned[integer_columns] = cleaned[integer_columns].astype("int64")

    leading_columns = [
        "match_id", "inning", "batting_team_raw", "batting_team_standard",
        "bowling_team_raw", "bowling_team_standard", "over", "ball",
    ]
    remaining_columns = [column for column in cleaned.columns if column not in leading_columns]
    return cleaned[leading_columns + remaining_columns]


def validate_cleaned_data(
    matches_clean: pd.DataFrame, deliveries_clean: pd.DataFrame
) -> pd.DataFrame:
    """Return understandable Phase 4 validation results without raising."""
    delivery_key = ["match_id", "inning", "over", "ball"]
    match_ids = set(matches_clean["match_id"])
    participant_lookup = matches_clean.set_index("match_id")[[
        "team1_standard", "team2_standard"
    ]]
    delivery_team_check = deliveries_clean[[
        "match_id", "batting_team_standard", "bowling_team_standard"
    ]].merge(participant_lookup, left_on="match_id", right_index=True, how="left", validate="many_to_one")
    batting_is_participant = (
        delivery_team_check["batting_team_standard"].eq(delivery_team_check["team1_standard"])
        | delivery_team_check["batting_team_standard"].eq(delivery_team_check["team2_standard"])
    )
    bowling_is_participant = (
        delivery_team_check["bowling_team_standard"].eq(delivery_team_check["team1_standard"])
        | delivery_team_check["bowling_team_standard"].eq(delivery_team_check["team2_standard"])
    )
    winner_valid = matches_clean["winner_standard"].isna() | (
        matches_clean["winner_standard"].eq(matches_clean["team1_standard"])
        | matches_clean["winner_standard"].eq(matches_clean["team2_standard"])
    )
    toss_valid = matches_clean["toss_winner_standard"].isna() | (
        matches_clean["toss_winner_standard"].eq(matches_clean["team1_standard"])
        | matches_clean["toss_winner_standard"].eq(matches_clean["team2_standard"])
    )
    expected_legal = ~deliveries_clean["extras_type"].isin(ILLEGAL_DELIVERY_EXTRA_TYPES)
    mapping_issue_count = 0
    for raw_column, standard_column in [
        ("team1_raw", "team1_standard"),
        ("team2_raw", "team2_standard"),
        ("toss_winner_raw", "toss_winner_standard"),
        ("winner_raw", "winner_standard"),
    ]:
        expected_standard = matches_clean[raw_column].replace(TEAM_NAME_MAP)
        mapping_issue_count += int(
            matches_clean[standard_column]
            .fillna("<NULL>")
            .ne(expected_standard.fillna("<NULL>"))
            .sum()
        )
    for raw_column, standard_column in [
        ("batting_team_raw", "batting_team_standard"),
        ("bowling_team_raw", "bowling_team_standard"),
    ]:
        expected_standard = deliveries_clean[raw_column].replace(TEAM_NAME_MAP)
        mapping_issue_count += int(
            deliveries_clean[standard_column]
            .fillna("<NULL>")
            .ne(expected_standard.fillna("<NULL>"))
            .sum()
        )

    checks = [
        ("Match row count remains 1,095", len(matches_clean) == 1095, abs(len(matches_clean) - 1095)),
        ("Delivery row count remains 260,920", len(deliveries_clean) == 260920, abs(len(deliveries_clean) - 260920)),
        ("Match IDs are unique", matches_clean["match_id"].is_unique, matches_clean["match_id"].duplicated().sum()),
        ("Participating teams are non-null", matches_clean[["team1_standard", "team2_standard"]].notna().all().all(), matches_clean[["team1_standard", "team2_standard"]].isna().sum().sum()),
        ("Winners are participating teams when present", winner_valid.all(), (~winner_valid).sum()),
        ("Toss winners are participating teams", toss_valid.all(), (~toss_valid).sum()),
        ("All match dates parsed", matches_clean["match_date"].notna().all(), matches_clean["match_date"].isna().sum()),
        ("Season labels remain in the observed domain", set(matches_clean["season_standard"]) == EXPECTED_SEASON_LABELS, len(set(matches_clean["season_standard"]) ^ EXPECTED_SEASON_LABELS)),
        ("Only documented team mappings were applied", mapping_issue_count == 0, mapping_issue_count),
        ("Delivery match IDs are non-null", deliveries_clean["match_id"].notna().all(), deliveries_clean["match_id"].isna().sum()),
        ("Every delivery maps to a match", set(deliveries_clean["match_id"]) <= match_ids, len(set(deliveries_clean["match_id"]) - match_ids)),
        ("Delivery keys remain unique", ~deliveries_clean.duplicated(delivery_key).any(), deliveries_clean.duplicated(delivery_key).sum()),
        ("Run values are non-negative", deliveries_clean[["batsman_runs", "extra_runs", "total_runs"]].ge(0).all().all(), deliveries_clean[["batsman_runs", "extra_runs", "total_runs"]].lt(0).sum().sum()),
        ("Run arithmetic remains valid", deliveries_clean["total_runs"].eq(deliveries_clean["batsman_runs"] + deliveries_clean["extra_runs"]).all(), (~deliveries_clean["total_runs"].eq(deliveries_clean["batsman_runs"] + deliveries_clean["extra_runs"])).sum()),
        ("Wicket flag remains binary", set(deliveries_clean["is_wicket"]) <= {0, 1}, len(set(deliveries_clean["is_wicket"]) - {0, 1})),
        ("Wicket rows have dismissal details", deliveries_clean.loc[deliveries_clean["is_wicket"].eq(1), ["player_dismissed", "dismissal_kind"]].notna().all().all(), deliveries_clean.loc[deliveries_clean["is_wicket"].eq(1), ["player_dismissed", "dismissal_kind"]].isna().sum().sum()),
        ("Dismissed-player rows have wicket flag", deliveries_clean.loc[deliveries_clean["player_dismissed"].notna(), "is_wicket"].eq(1).all(), deliveries_clean.loc[deliveries_clean["player_dismissed"].notna(), "is_wicket"].ne(1).sum()),
        ("Legal-delivery flag follows extras rule", deliveries_clean["is_legal_delivery"].eq(expected_legal).all(), deliveries_clean["is_legal_delivery"].ne(expected_legal).sum()),
        ("Legal-ball integer matches boolean flag", deliveries_clean["legal_ball"].eq(deliveries_clean["is_legal_delivery"].astype(int)).all(), deliveries_clean["legal_ball"].ne(deliveries_clean["is_legal_delivery"].astype(int)).sum()),
        ("Batting teams belong to their match", batting_is_participant.all(), (~batting_is_participant).sum()),
        ("Bowling teams belong to their match", bowling_is_participant.all(), (~bowling_is_participant).sum()),
    ]
    results = pd.DataFrame(checks, columns=["check", "passed", "issue_count"])
    results["status"] = results["passed"].map({True: "PASS", False: "FAIL"})
    return results[["check", "status", "issue_count"]]


def save_clean_data(
    matches_clean: pd.DataFrame,
    deliveries_clean: pd.DataFrame,
    root: Path | None = None,
) -> tuple[Path, Path]:
    """Write the two intended cleaned CSV outputs under data/processed."""
    root = Path(root) if root is not None else get_project_root()
    processed_dir = root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    matches_path = processed_dir / "matches_clean.csv"
    deliveries_path = processed_dir / "deliveries_clean.csv"
    matches_clean.to_csv(matches_path, index=False, date_format="%Y-%m-%d")
    deliveries_clean.to_csv(deliveries_path, index=False)
    return matches_path, deliveries_path
