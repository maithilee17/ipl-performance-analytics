"""Phase 4 tests against the real IPL source data and cleaning logic."""

import pandas as pd
import pytest

from src.data_cleaning import (
    CITY_NAME_MAP,
    ILLEGAL_DELIVERY_EXTRA_TYPES,
    TEAM_NAME_MAP,
    VENUE_NAME_MAP,
    VENUE_TO_CITY_FILL,
    clean_deliveries,
    clean_matches,
    validate_cleaned_data,
)
from src.data_loader import get_data_paths, load_clean_data, load_feature_data, load_raw_data
from src.feature_engineering import (
    BOWLER_WICKET_TYPES,
    FEATURE_OUTPUT_NAMES,
    run_feature_engineering,
    validate_feature_datasets,
)
from src.validation import (
    EXPECTED_DELIVERY_COLUMNS,
    EXPECTED_MATCH_COLUMNS,
    validate_project,
)


@pytest.fixture(scope="module")
def datasets():
    matches_raw, deliveries_raw = load_raw_data()
    return (
        matches_raw,
        deliveries_raw,
        clean_matches(matches_raw),
        clean_deliveries(deliveries_raw),
    )


def test_team_mappings_use_documented_rules(datasets):
    _, _, matches_clean, deliveries_clean = datasets
    pairs = [
        (matches_clean, "team1_raw", "team1_standard"),
        (matches_clean, "team2_raw", "team2_standard"),
        (matches_clean, "toss_winner_raw", "toss_winner_standard"),
        (matches_clean, "winner_raw", "winner_standard"),
        (deliveries_clean, "batting_team_raw", "batting_team_standard"),
        (deliveries_clean, "bowling_team_raw", "bowling_team_standard"),
    ]
    for frame, raw_column, standard_column in pairs:
        expected = frame[raw_column].replace(TEAM_NAME_MAP)
        pd.testing.assert_series_equal(
            frame[standard_column], expected, check_names=False
        )


def test_venue_and_city_mappings_use_observed_rows(datasets):
    matches_raw, _, matches_clean, _ = datasets
    assert set(VENUE_NAME_MAP).issubset(set(matches_raw["venue"]))
    expected_venues = matches_clean["venue_raw"].replace(VENUE_NAME_MAP)
    pd.testing.assert_series_equal(
        matches_clean["venue_standard"], expected_venues, check_names=False
    )
    assert set(CITY_NAME_MAP).issubset(set(matches_raw["city"].dropna()))
    assert matches_clean["city_standard"].isna().sum() == 0
    for venue, city in VENUE_TO_CITY_FILL.items():
        filled = matches_clean.loc[
            matches_clean["city_raw"].isna()
            & matches_clean["venue_standard"].eq(venue),
            "city_standard",
        ]
        assert not filled.empty
        assert filled.eq(city).all()


def test_dates_parse_without_loss(datasets):
    matches_raw, _, matches_clean, _ = datasets
    assert matches_clean["match_date"].notna().all()
    assert matches_clean["date_raw"].eq(matches_raw["date"]).all()
    assert matches_clean["match_date"].dt.strftime("%Y-%m-%d").eq(
        matches_clean["date_raw"]
    ).all()


def test_legal_delivery_logic_uses_wides_and_no_balls(datasets):
    _, _, _, deliveries_clean = datasets
    expected = ~deliveries_clean["extras_type"].isin(ILLEGAL_DELIVERY_EXTRA_TYPES)
    assert deliveries_clean["is_legal_delivery"].eq(expected).all()
    assert deliveries_clean["legal_ball"].eq(expected.astype(int)).all()
    assert deliveries_clean.loc[
        deliveries_clean["extras_type"].isin(ILLEGAL_DELIVERY_EXTRA_TYPES),
        "is_legal_delivery",
    ].eq(False).all()


def test_keys_runs_and_referential_integrity(datasets):
    _, _, matches_clean, deliveries_clean = datasets
    assert matches_clean["match_id"].is_unique
    assert not deliveries_clean.duplicated(
        ["match_id", "inning", "over", "ball"]
    ).any()
    assert set(deliveries_clean["match_id"]) <= set(matches_clean["match_id"])
    assert deliveries_clean[["batsman_runs", "extra_runs", "total_runs"]].ge(0).all().all()
    assert deliveries_clean["total_runs"].eq(
        deliveries_clean["batsman_runs"] + deliveries_clean["extra_runs"]
    ).all()


def test_complete_phase_four_validation_passes(datasets):
    _, _, matches_clean, deliveries_clean = datasets
    results = validate_cleaned_data(matches_clean, deliveries_clean)
    assert results["status"].eq("PASS").all(), results.to_string(index=False)


@pytest.fixture(scope="module")
def cleaned_files():
    return load_clean_data()


@pytest.fixture(scope="module")
def phase_five_results():
    return validate_project()


def test_serialized_cleaned_schema_and_grain(cleaned_files):
    matches, deliveries = cleaned_files
    assert matches.columns.tolist() == EXPECTED_MATCH_COLUMNS
    assert deliveries.columns.tolist() == EXPECTED_DELIVERY_COLUMNS
    assert matches.shape == (1095, 32)
    assert deliveries.shape == (260920, 21)
    assert matches["match_id"].is_unique
    assert not deliveries.duplicated(["match_id", "inning", "over", "ball"]).any()


def test_phase_five_has_no_failures_and_only_explained_warnings(phase_five_results):
    assert not phase_five_results["status"].eq("FAIL").any(), phase_five_results.loc[
        phase_five_results["status"].eq("FAIL")
    ].to_string(index=False)
    warning_checks = set(
        phase_five_results.loc[phase_five_results["status"].eq("WARN"), "check"]
    )
    assert warning_checks == {
        "Standard venues associated with multiple city labels",
        "Run-out rows without named fielder",
    }


def test_cross_table_teams_and_match_ids_reconcile(cleaned_files):
    matches, deliveries = cleaned_files
    participants = matches.set_index("match_id")[["team1_standard", "team2_standard"]]
    joined = deliveries[["match_id", "batting_team_standard", "bowling_team_standard"]].merge(
        participants, left_on="match_id", right_index=True, validate="many_to_one"
    )
    assert set(deliveries["match_id"]) == set(matches["match_id"])
    for role in ["batting_team_standard", "bowling_team_standard"]:
        assert (
            joined[role].eq(joined["team1_standard"])
            | joined[role].eq(joined["team2_standard"])
        ).all()


def test_outcome_and_toss_baselines_reconcile(cleaned_files):
    matches, _ = cleaned_files
    assert matches["result"].value_counts().to_dict() == {
        "wickets": 578,
        "runs": 498,
        "tie": 14,
        "no result": 5,
    }
    decided = matches.loc[matches["winner_standard"].notna()]
    toss_winner_won = decided["toss_winner_standard"].eq(decided["winner_standard"])
    assert len(decided) == 1090
    assert int(toss_winner_won.sum()) == 554
    assert round(toss_winner_won.mean() * 100, 1) == 50.8


@pytest.fixture(scope="module")
def feature_files():
    return load_feature_data()


def test_feature_files_exist_and_have_expected_columns(feature_files):
    paths = get_data_paths()
    assert all(paths[name].is_file() for name in FEATURE_OUTPUT_NAMES)
    expected_columns = {
        "match_summary": {"match_id", "season_label", "match_date", "team1", "team2", "winning_team", "losing_team", "match_total_runs", "match_legal_balls"},
        "innings_summary": {"match_id", "season", "inning", "batting_team", "bowling_team", "recorded_deliveries", "legal_balls", "illegal_deliveries", "total_runs", "run_rate"},
        "team_season_summary": {"season", "team", "matches_played", "wins", "losses", "ties", "no_results", "win_percentage", "total_runs_scored", "total_runs_conceded"},
        "batting_summary": {"season", "batter", "matches", "runs", "balls_faced", "fours", "sixes", "strike_rate", "batting_average", "boundary_percentage"},
        "bowling_summary": {"season", "bowler", "matches", "legal_balls", "overs_bowled", "runs_conceded", "wickets", "economy_rate", "wides", "no_balls"},
    }
    for name, columns in expected_columns.items():
        assert columns <= set(feature_files[name].columns)


def test_feature_dataset_grains_are_unique(feature_files):
    keys = {
        "match_summary": ["match_id"],
        "innings_summary": ["match_id", "inning"],
        "team_season_summary": ["season", "team"],
        "batting_summary": ["season", "batter"],
        "bowling_summary": ["season", "bowler"],
    }
    for name, key in keys.items():
        assert not feature_files[name].duplicated(key).any(), name


def test_feature_validation_and_metric_ranges(cleaned_files, feature_files):
    matches, deliveries = cleaned_files
    results = validate_feature_datasets(matches, deliveries, feature_files)
    assert results["status"].eq("PASS").all(), results.loc[
        results["status"].eq("FAIL")
    ].to_string(index=False)


def test_feature_totals_reconcile_with_cleaned_deliveries(cleaned_files, feature_files):
    _, deliveries = cleaned_files
    innings = feature_files["innings_summary"]
    teams = feature_files["team_season_summary"]
    batting = feature_files["batting_summary"]
    bowling = feature_files["bowling_summary"]
    assert innings["total_runs"].sum() == deliveries["total_runs"].sum()
    assert innings["extra_runs"].sum() == deliveries["extra_runs"].sum()
    assert batting["runs"].sum() == deliveries["batsman_runs"].sum()
    assert teams["total_runs_scored"].sum() == deliveries["total_runs"].sum()
    assert teams["total_runs_conceded"].sum() == deliveries["total_runs"].sum()
    expected_wickets = deliveries["dismissal_kind"].isin(BOWLER_WICKET_TYPES).sum()
    assert bowling["wickets"].sum() == expected_wickets
    assert teams["total_wickets_taken"].sum() == expected_wickets
    assert teams["total_wickets_lost"].sum() == expected_wickets


def test_module_output_matches_serialized_feature_files(feature_files):
    generated, validation = run_feature_engineering(save=False)
    assert validation["status"].eq("PASS").all()
    for name, frame in generated.items():
        assert frame.shape == feature_files[name].shape
        assert frame.columns.tolist() == feature_files[name].columns.tolist()
