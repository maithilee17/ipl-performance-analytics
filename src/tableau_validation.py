"""Validate the five immutable analytical CSVs for Tableau consumption."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_loader import get_data_paths, get_project_root, load_clean_data, load_feature_data
from src.feature_engineering import validate_feature_datasets


TABLEAU_SOURCE_COLUMNS = {
    "match_summary": [
        "match_id", "season_label", "match_date", "city", "venue", "team1", "team2",
        "toss_winner", "toss_decision", "winning_team", "result", "result_margin",
        "player_of_match", "match_type", "super_over", "method", "match_decided",
        "toss_winner_is_match_winner", "losing_team", "win_margin_type", "match_stage",
        "innings_count", "match_recorded_deliveries", "match_legal_balls",
        "match_illegal_deliveries", "match_total_runs", "match_batsman_runs",
        "match_extra_runs", "match_wickets", "match_bowler_wickets", "match_fours",
        "match_sixes", "match_dot_balls",
    ],
    "innings_summary": [
        "match_id", "season", "inning", "batting_team", "bowling_team",
        "recorded_deliveries", "legal_balls", "illegal_deliveries", "total_runs",
        "batsman_runs", "extra_runs", "wickets", "bowler_wickets", "fours", "sixes",
        "dot_balls", "run_rate",
    ],
    "team_season_summary": [
        "season", "team", "matches_played", "decided_matches", "wins", "losses", "ties",
        "no_results", "win_percentage", "total_runs_scored", "total_runs_conceded",
        "average_runs_scored", "average_runs_conceded", "total_wickets_taken",
        "total_wickets_lost", "toss_wins", "toss_decided_matches", "toss_match_wins",
        "toss_to_match_win_percentage",
    ],
    "batting_summary": [
        "season", "batter", "matches", "runs", "balls_faced", "fours", "sixes",
        "boundary_runs", "dot_balls", "dismissals", "strike_rate", "batting_average",
        "boundary_percentage", "dot_ball_percentage",
    ],
    "bowling_summary": [
        "season", "bowler", "matches", "legal_balls", "overs_bowled", "runs_conceded",
        "wickets", "economy_rate", "dot_balls", "dot_ball_percentage", "wides", "no_balls",
    ],
}


TABLEAU_SOURCE_RULES = {
    "match_summary": {
        "rows": 1095,
        "numeric": ["match_id", "result_margin", "innings_count", "match_total_runs", "match_bowler_wickets"],
        "key": ["match_id"],
        "required": ["match_id", "season_label", "match_date", "team1", "team2"],
        "nullable": {
            "winning_team", "result_margin", "player_of_match", "method",
            "toss_winner_is_match_winner", "losing_team", "win_margin_type",
        },
    },
    "innings_summary": {
        "rows": 2217,
        "numeric": ["match_id", "inning", "legal_balls", "total_runs", "wickets", "run_rate"],
        "key": ["match_id", "inning"],
        "required": ["match_id", "season", "inning", "batting_team", "bowling_team"],
        "nullable": set(),
    },
    "team_season_summary": {
        "rows": 146,
        "numeric": ["matches_played", "wins", "decided_matches", "win_percentage", "total_runs_scored", "total_wickets_taken"],
        "key": ["season", "team"],
        "required": ["season", "team", "matches_played", "wins", "decided_matches"],
        "nullable": set(),
    },
    "batting_summary": {
        "rows": 2617,
        "numeric": ["matches", "runs", "balls_faced", "dismissals", "strike_rate", "batting_average"],
        "key": ["season", "batter"],
        "required": ["season", "batter", "runs", "balls_faced", "dismissals"],
        "nullable": {"batting_average", "boundary_percentage"},
    },
    "bowling_summary": {
        "rows": 1948,
        "numeric": ["matches", "legal_balls", "runs_conceded", "wickets", "economy_rate"],
        "key": ["season", "bowler"],
        "required": ["season", "bowler", "legal_balls", "runs_conceded", "wickets"],
        "nullable": set(),
    },
}


def validate_tableau_sources(root: Path | None = None) -> pd.DataFrame:
    """Return PASS/FAIL checks for Tableau source readiness and reconciliation."""
    root = Path(root) if root is not None else get_project_root()
    paths = get_data_paths(root)
    frames = load_feature_data(root)
    checks: list[tuple[str, str, str]] = []

    def add(check: str, passed: bool, actual: object) -> None:
        checks.append((check, "PASS" if passed else "FAIL", str(actual)))

    for name, rules in TABLEAU_SOURCE_RULES.items():
        frame = frames[name]
        source_path = paths[name]
        add(f"{name} exists", source_path.is_file(), source_path.name)
        add(f"{name} row count", len(frame) == rules["rows"], len(frame))
        schema_matches = list(frame.columns) == TABLEAU_SOURCE_COLUMNS[name]
        add(f"{name} columns match", schema_matches, len(frame.columns))
        numeric_types_valid = all(
            pd.api.types.is_numeric_dtype(frame[column]) for column in rules["numeric"]
        )
        add(f"{name} numeric types are valid", numeric_types_valid, rules["numeric"])
        if name == "match_summary":
            add(
                "match_summary date type is valid",
                pd.api.types.is_datetime64_any_dtype(frame["match_date"]),
                str(frame["match_date"].dtype),
            )
        text_columns = frame.select_dtypes(include=["object", "string"]).columns
        empty_strings = int(
            sum(frame[column].dropna().astype(str).str.strip().eq("").sum() for column in text_columns)
        )
        add(f"{name} has no empty strings", empty_strings == 0, empty_strings)
        duplicates = int(frame.duplicated(rules["key"]).sum())
        add(f"{name} grain is unique", duplicates == 0, duplicates)
        missing_required = int(frame[rules["required"]].isna().sum().sum())
        add(f"{name} required fields are complete", missing_required == 0, missing_required)
        nullable_columns = set(frame.columns[frame.isna().any()])
        unexpected = sorted(nullable_columns - rules["nullable"])
        add(f"{name} nulls are documented", not unexpected, unexpected)

    matches, deliveries = load_clean_data(root)
    feature_validation = validate_feature_datasets(matches, deliveries, frames)
    feature_failures = int(feature_validation["status"].eq("FAIL").sum())
    add("Phase 6 feature validation remains valid", feature_failures == 0, feature_failures)

    anchors = {
        "matches": (len(frames["match_summary"]), 1095),
        "total_runs": (int(frames["match_summary"]["match_total_runs"].sum()), 347756),
        "batter_runs": (int(frames["batting_summary"]["runs"].sum()), 330064),
        "extras": (int(frames["innings_summary"]["extra_runs"].sum()), 17692),
        "legal_balls": (int(frames["bowling_summary"]["legal_balls"].sum()), 251471),
        "bowler_wickets": (int(frames["bowling_summary"]["wickets"].sum()), 11815),
    }
    for metric, (actual, expected) in anchors.items():
        add(f"{metric} Tableau anchor", actual == expected, actual)

    return pd.DataFrame(checks, columns=["check", "status", "actual"])


if __name__ == "__main__":
    results = validate_tableau_sources()
    print(results.to_string(index=False))
    print(f"Validation: {results['status'].eq('PASS').sum()}/{len(results)} PASS")
    if results["status"].eq("FAIL").any():
        raise SystemExit(1)
