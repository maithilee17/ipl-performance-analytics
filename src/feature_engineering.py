"""Reusable Phase 6 feature engineering for IPL analytical datasets."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.data_loader import get_project_root, load_clean_data


BOWLER_WICKET_TYPES = {
    "bowled", "caught", "caught and bowled", "lbw", "stumped", "hit wicket"
}
BATTER_DISMISSAL_EXCLUSIONS = {"retired hurt"}
MATCH_STAGE_MAP = {
    "League": "League",
    "Final": "Final",
    "Qualifier 1": "Playoffs",
    "Qualifier 2": "Playoffs",
    "Eliminator": "Playoffs",
    "Semi Final": "Playoffs",
    "Elimination Final": "Playoffs",
    "3rd Place Play-Off": "Playoffs",
}

FEATURE_OUTPUT_NAMES = {
    "match_summary": "match_summary.csv",
    "innings_summary": "innings_summary.csv",
    "team_season_summary": "team_season_summary.csv",
    "batting_summary": "batting_summary.csv",
    "bowling_summary": "bowling_summary.csv",
}


def _safe_rate(numerator: pd.Series, denominator: pd.Series, multiplier: float) -> pd.Series:
    """Calculate a rate while leaving zero-denominator results null."""
    return numerator.div(denominator.where(denominator.gt(0))).mul(multiplier)


def _deliveries_with_season(
    matches: pd.DataFrame, deliveries: pd.DataFrame
) -> pd.DataFrame:
    """Attach the validated season label to each delivery."""
    return deliveries.merge(
        matches[["match_id", "season_standard"]],
        on="match_id",
        how="left",
        validate="many_to_one",
    ).rename(columns={"season_standard": "season"})


def build_innings_summary(
    matches: pd.DataFrame, deliveries: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate recorded deliveries to one row per match and innings."""
    working = _deliveries_with_season(matches, deliveries).assign(
        illegal_delivery=1 - deliveries["legal_ball"].to_numpy(),
        four=deliveries["batsman_runs"].eq(4).astype(int).to_numpy(),
        six=deliveries["batsman_runs"].eq(6).astype(int).to_numpy(),
        dot_ball=(deliveries["is_legal_delivery"] & deliveries["total_runs"].eq(0)).astype(int).to_numpy(),
        bowler_wicket=deliveries["dismissal_kind"].isin(BOWLER_WICKET_TYPES).astype(int).to_numpy(),
    )
    summary = (
        working.groupby(
            ["match_id", "season", "inning", "batting_team_standard", "bowling_team_standard"],
            as_index=False,
            sort=False,
            dropna=False,
        )
        .agg(
            recorded_deliveries=("match_id", "size"),
            legal_balls=("legal_ball", "sum"),
            illegal_deliveries=("illegal_delivery", "sum"),
            total_runs=("total_runs", "sum"),
            batsman_runs=("batsman_runs", "sum"),
            extra_runs=("extra_runs", "sum"),
            wickets=("is_wicket", "sum"),
            bowler_wickets=("bowler_wicket", "sum"),
            fours=("four", "sum"),
            sixes=("six", "sum"),
            dot_balls=("dot_ball", "sum"),
        )
        .rename(columns={
            "batting_team_standard": "batting_team",
            "bowling_team_standard": "bowling_team",
        })
    )
    summary["run_rate"] = _safe_rate(
        summary["total_runs"], summary["legal_balls"], 6
    )
    return summary


def build_match_features(
    matches: pd.DataFrame, innings_summary: pd.DataFrame
) -> pd.DataFrame:
    """Create one analytical record per match with outcome and score features."""
    columns = [
        "match_id", "season_standard", "match_date", "city_standard",
        "venue_standard", "team1_standard", "team2_standard",
        "toss_winner_standard", "toss_decision", "winner_standard", "result",
        "result_margin", "player_of_match", "match_type", "super_over", "method",
    ]
    summary = matches[columns].copy().rename(columns={
        "season_standard": "season_label",
        "city_standard": "city",
        "venue_standard": "venue",
        "team1_standard": "team1",
        "team2_standard": "team2",
        "toss_winner_standard": "toss_winner",
        "winner_standard": "winning_team",
    })
    summary["match_decided"] = summary["winning_team"].notna()
    summary["toss_winner_is_match_winner"] = (
        summary["toss_winner"].eq(summary["winning_team"])
        .where(summary["match_decided"])
        .astype("boolean")
    )
    normal_decision = summary["result"].isin(["runs", "wickets"])
    summary["losing_team"] = pd.Series(pd.NA, index=summary.index, dtype="string")
    summary.loc[normal_decision & summary["winning_team"].eq(summary["team1"]), "losing_team"] = summary["team2"]
    summary.loc[normal_decision & summary["winning_team"].eq(summary["team2"]), "losing_team"] = summary["team1"]
    summary["win_margin_type"] = summary["result"].where(normal_decision)
    summary["match_stage"] = summary["match_type"].map(MATCH_STAGE_MAP)

    match_totals = innings_summary.groupby("match_id", as_index=False).agg(
        innings_count=("inning", "nunique"),
        match_recorded_deliveries=("recorded_deliveries", "sum"),
        match_legal_balls=("legal_balls", "sum"),
        match_illegal_deliveries=("illegal_deliveries", "sum"),
        match_total_runs=("total_runs", "sum"),
        match_batsman_runs=("batsman_runs", "sum"),
        match_extra_runs=("extra_runs", "sum"),
        match_wickets=("wickets", "sum"),
        match_bowler_wickets=("bowler_wickets", "sum"),
        match_fours=("fours", "sum"),
        match_sixes=("sixes", "sum"),
        match_dot_balls=("dot_balls", "sum"),
    )
    return summary.merge(match_totals, on="match_id", how="left", validate="one_to_one")


def build_team_season_summary(
    matches: pd.DataFrame, deliveries: pd.DataFrame
) -> pd.DataFrame:
    """Create one row per standardized team and season."""
    base_columns = [
        "match_id", "season_standard", "team1_standard", "team2_standard",
        "winner_standard", "toss_winner_standard", "result",
    ]
    base = matches[base_columns]
    team1 = base.rename(columns={"team1_standard": "team"}).drop(columns="team2_standard")
    team2 = base.rename(columns={"team2_standard": "team"}).drop(columns="team1_standard")
    participation = pd.concat([team1, team2], ignore_index=True).rename(
        columns={"season_standard": "season"}
    )
    normal_decision = participation["result"].isin(["runs", "wickets"])
    participation = participation.assign(
        win=(normal_decision & participation["team"].eq(participation["winner_standard"])).astype(int),
        loss=(normal_decision & participation["team"].ne(participation["winner_standard"])).astype(int),
        tie=participation["result"].eq("tie").astype(int),
        no_result=participation["result"].eq("no result").astype(int),
        toss_win=participation["team"].eq(participation["toss_winner_standard"]).astype(int),
    )
    participation["toss_in_decided_match"] = (
        normal_decision & participation["team"].eq(participation["toss_winner_standard"])
    ).astype(int)
    participation["toss_and_match_win"] = (
        participation["toss_in_decided_match"].eq(1) & participation["win"].eq(1)
    ).astype(int)
    team_summary = participation.groupby(["season", "team"], as_index=False, sort=False).agg(
        matches_played=("match_id", "nunique"),
        wins=("win", "sum"),
        losses=("loss", "sum"),
        ties=("tie", "sum"),
        no_results=("no_result", "sum"),
        toss_wins=("toss_win", "sum"),
        toss_decided_matches=("toss_in_decided_match", "sum"),
        toss_match_wins=("toss_and_match_win", "sum"),
    )
    team_summary["decided_matches"] = team_summary["wins"] + team_summary["losses"]
    team_summary["win_percentage"] = _safe_rate(
        team_summary["wins"], team_summary["decided_matches"], 100
    )
    team_summary["toss_to_match_win_percentage"] = _safe_rate(
        team_summary["toss_match_wins"], team_summary["toss_decided_matches"], 100
    )

    working = _deliveries_with_season(matches, deliveries).assign(
        bowler_wicket=deliveries["dismissal_kind"].isin(BOWLER_WICKET_TYPES).astype(int).to_numpy()
    )
    scored = working.groupby(["season", "batting_team_standard"], as_index=False).agg(
        total_runs_scored=("total_runs", "sum"),
        total_wickets_lost=("bowler_wicket", "sum"),
    ).rename(columns={"batting_team_standard": "team"})
    conceded = working.groupby(["season", "bowling_team_standard"], as_index=False).agg(
        total_runs_conceded=("total_runs", "sum"),
        total_wickets_taken=("bowler_wicket", "sum"),
    ).rename(columns={"bowling_team_standard": "team"})
    team_summary = team_summary.merge(scored, on=["season", "team"], how="left", validate="one_to_one")
    team_summary = team_summary.merge(conceded, on=["season", "team"], how="left", validate="one_to_one")
    count_columns = ["total_runs_scored", "total_wickets_lost", "total_runs_conceded", "total_wickets_taken"]
    team_summary[count_columns] = team_summary[count_columns].fillna(0).astype(int)
    team_summary["average_runs_scored"] = team_summary["total_runs_scored"].div(team_summary["matches_played"])
    team_summary["average_runs_conceded"] = team_summary["total_runs_conceded"].div(team_summary["matches_played"])
    ordered = [
        "season", "team", "matches_played", "decided_matches", "wins", "losses",
        "ties", "no_results", "win_percentage", "total_runs_scored",
        "total_runs_conceded", "average_runs_scored", "average_runs_conceded",
        "total_wickets_taken", "total_wickets_lost", "toss_wins",
        "toss_decided_matches", "toss_match_wins", "toss_to_match_win_percentage",
    ]
    return team_summary[ordered]


def build_batting_summary(
    matches: pd.DataFrame, deliveries: pd.DataFrame
) -> pd.DataFrame:
    """Create one row per season and batter using cricket-aware denominators."""
    working = _deliveries_with_season(matches, deliveries).assign(
        ball_faced=deliveries["extras_type"].ne("wides").astype(int).to_numpy(),
        four=deliveries["batsman_runs"].eq(4).astype(int).to_numpy(),
        six=deliveries["batsman_runs"].eq(6).astype(int).to_numpy(),
        dot_ball=(deliveries["is_legal_delivery"] & deliveries["total_runs"].eq(0)).astype(int).to_numpy(),
    )
    summary = working.groupby(["season", "batter"], as_index=False, sort=False).agg(
        matches=("match_id", "nunique"),
        runs=("batsman_runs", "sum"),
        balls_faced=("ball_faced", "sum"),
        fours=("four", "sum"),
        sixes=("six", "sum"),
        dot_balls=("dot_ball", "sum"),
    )
    dismissals = (
        working.loc[
            working["player_dismissed"].notna()
            & ~working["dismissal_kind"].isin(BATTER_DISMISSAL_EXCLUSIONS)
        ]
        .groupby(["season", "player_dismissed"], as_index=False)
        .size()
        .rename(columns={"player_dismissed": "batter", "size": "dismissals"})
    )
    summary = summary.merge(dismissals, on=["season", "batter"], how="left", validate="one_to_one")
    summary["dismissals"] = summary["dismissals"].fillna(0).astype(int)
    summary["boundary_runs"] = summary["fours"] * 4 + summary["sixes"] * 6
    summary["strike_rate"] = _safe_rate(summary["runs"], summary["balls_faced"], 100)
    summary["batting_average"] = _safe_rate(summary["runs"], summary["dismissals"], 1)
    summary["boundary_percentage"] = _safe_rate(summary["boundary_runs"], summary["runs"], 100)
    summary["dot_ball_percentage"] = _safe_rate(summary["dot_balls"], summary["balls_faced"], 100)
    return summary[[
        "season", "batter", "matches", "runs", "balls_faced", "fours", "sixes",
        "boundary_runs", "dot_balls", "dismissals", "strike_rate",
        "batting_average", "boundary_percentage", "dot_ball_percentage",
    ]]


def build_bowling_summary(
    matches: pd.DataFrame, deliveries: pd.DataFrame
) -> pd.DataFrame:
    """Create one row per season and bowler with credited bowling measures."""
    working = _deliveries_with_season(matches, deliveries)
    non_bowler_extras = working["extra_runs"].where(
        working["extras_type"].isin(["byes", "legbyes", "penalty"]), 0
    )
    working = working.assign(
        runs_conceded=working["total_runs"] - non_bowler_extras,
        bowler_wicket=working["dismissal_kind"].isin(BOWLER_WICKET_TYPES).astype(int),
        dot_ball=(working["is_legal_delivery"] & working["total_runs"].eq(0)).astype(int),
        wide=working["extras_type"].eq("wides").astype(int),
        no_ball=working["extras_type"].eq("noballs").astype(int),
    )
    summary = working.groupby(["season", "bowler"], as_index=False, sort=False).agg(
        matches=("match_id", "nunique"),
        legal_balls=("legal_ball", "sum"),
        runs_conceded=("runs_conceded", "sum"),
        wickets=("bowler_wicket", "sum"),
        dot_balls=("dot_ball", "sum"),
        wides=("wide", "sum"),
        no_balls=("no_ball", "sum"),
    )
    summary["overs_bowled"] = summary["legal_balls"].div(6)
    summary["economy_rate"] = _safe_rate(summary["runs_conceded"], summary["legal_balls"], 6)
    summary["dot_ball_percentage"] = _safe_rate(summary["dot_balls"], summary["legal_balls"], 100)
    return summary[[
        "season", "bowler", "matches", "legal_balls", "overs_bowled",
        "runs_conceded", "wickets", "economy_rate", "dot_balls",
        "dot_ball_percentage", "wides", "no_balls",
    ]]


def validate_feature_datasets(
    matches: pd.DataFrame,
    deliveries: pd.DataFrame,
    datasets: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Validate grains, ranges, domains, and source reconciliation."""
    match_summary = datasets["match_summary"]
    innings = datasets["innings_summary"]
    teams = datasets["team_season_summary"]
    batting = datasets["batting_summary"]
    bowling = datasets["bowling_summary"]
    rows: list[tuple[str, bool, int | str]] = []

    def add(check: str, passed: bool, issue: int | str = 0) -> None:
        rows.append((check, bool(passed), issue))

    def rates_match(actual: pd.Series, expected: pd.Series) -> bool:
        """Compare rates while treating paired undefined values as equivalent."""
        return actual.round(10).fillna(-1).eq(expected.round(10).fillna(-1)).all()

    add("Match summary has one row per source match", len(match_summary) == len(matches) and match_summary["match_id"].is_unique, abs(len(match_summary) - len(matches)) + int(match_summary["match_id"].duplicated().sum()))
    add("Innings summary grain is unique", not innings.duplicated(["match_id", "inning"]).any(), int(innings.duplicated(["match_id", "inning"]).sum()))
    add("Team-season grain is unique", not teams.duplicated(["season", "team"]).any(), int(teams.duplicated(["season", "team"]).sum()))
    add("Batting grain is unique", not batting.duplicated(["season", "batter"]).any(), int(batting.duplicated(["season", "batter"]).sum()))
    add("Bowling grain is unique", not bowling.duplicated(["season", "bowler"]).any(), int(bowling.duplicated(["season", "bowler"]).sum()))

    required_fields = {
        "Match summary": (match_summary, ["match_id", "season_label", "match_date", "team1", "team2"]),
        "Innings summary": (innings, ["match_id", "season", "inning", "batting_team", "bowling_team"]),
        "Team-season summary": (teams, ["season", "team"]),
        "Batting summary": (batting, ["season", "batter"]),
        "Bowling summary": (bowling, ["season", "bowler"]),
    }
    for label, (frame, columns) in required_fields.items():
        issue_count = int(frame[columns].isna().sum().sum())
        add(f"{label} required dimensions are non-null", issue_count == 0, issue_count)

    season_domain = set(matches["season_standard"])
    team_domain = set(pd.concat([matches["team1_standard"], matches["team2_standard"]]))
    add("All feature seasons are valid", all(set(frame["season" if "season" in frame else "season_label"]) <= season_domain for frame in [innings, teams, batting, bowling, match_summary]), 0)
    add("All feature teams are valid", set(teams["team"]) <= team_domain and set(innings["batting_team"]) <= team_domain and set(innings["bowling_team"]) <= team_domain, 0)
    add("All batter names come from deliveries", set(batting["batter"]) <= set(deliveries["batter"].dropna()), 0)
    add("All bowler names come from deliveries", set(bowling["bowler"]) <= set(deliveries["bowler"].dropna()), 0)

    nonnegative_sets = {
        "innings": (innings, ["recorded_deliveries", "legal_balls", "illegal_deliveries", "total_runs", "batsman_runs", "extra_runs", "wickets", "bowler_wickets", "fours", "sixes", "dot_balls", "run_rate"]),
        "teams": (teams, ["matches_played", "wins", "losses", "ties", "no_results", "total_runs_scored", "total_runs_conceded", "total_wickets_taken", "total_wickets_lost"]),
        "batting": (batting, ["matches", "runs", "balls_faced", "fours", "sixes", "boundary_runs", "dot_balls", "dismissals", "strike_rate", "batting_average"]),
        "bowling": (bowling, ["matches", "legal_balls", "overs_bowled", "runs_conceded", "wickets", "economy_rate", "dot_balls", "wides", "no_balls"]),
    }
    for label, (frame, columns) in nonnegative_sets.items():
        issue_count = int(frame[columns].lt(0).sum().sum())
        add(f"{label.title()} metrics are non-negative", issue_count == 0, issue_count)
    for column, frame in [
        ("win_percentage", teams),
        ("toss_to_match_win_percentage", teams),
        ("boundary_percentage", batting),
        ("dot_ball_percentage", batting),
        ("dot_ball_percentage", bowling),
    ]:
        invalid = int((frame[column].notna() & ~frame[column].between(0, 100)).sum())
        add(f"{column} values are between 0 and 100", invalid == 0, invalid)

    add("Match total runs reconcile with deliveries", int(match_summary["match_total_runs"].sum()) == int(deliveries["total_runs"].sum()), int(match_summary["match_total_runs"].sum() - deliveries["total_runs"].sum()))
    add("Innings total runs reconcile with deliveries", int(innings["total_runs"].sum()) == int(deliveries["total_runs"].sum()), int(innings["total_runs"].sum() - deliveries["total_runs"].sum()))
    add("Innings batter runs reconcile with deliveries", int(innings["batsman_runs"].sum()) == int(deliveries["batsman_runs"].sum()), int(innings["batsman_runs"].sum() - deliveries["batsman_runs"].sum()))
    add("Innings extras reconcile with deliveries", int(innings["extra_runs"].sum()) == int(deliveries["extra_runs"].sum()), int(innings["extra_runs"].sum() - deliveries["extra_runs"].sum()))
    add("Innings recorded deliveries reconcile", int(innings["recorded_deliveries"].sum()) == len(deliveries), int(innings["recorded_deliveries"].sum() - len(deliveries)))
    add("Innings legal balls reconcile", int(innings["legal_balls"].sum()) == int(deliveries["legal_ball"].sum()), int(innings["legal_balls"].sum() - deliveries["legal_ball"].sum()))
    add("Innings delivery classes partition recorded deliveries", (innings["legal_balls"] + innings["illegal_deliveries"]).eq(innings["recorded_deliveries"]).all(), int((innings["legal_balls"] + innings["illegal_deliveries"] - innings["recorded_deliveries"]).abs().sum()))
    add("Innings run rate uses legal balls", rates_match(innings["run_rate"], _safe_rate(innings["total_runs"], innings["legal_balls"], 6)), 0)
    add("Batting runs reconcile with deliveries", int(batting["runs"].sum()) == int(deliveries["batsman_runs"].sum()), int(batting["runs"].sum() - deliveries["batsman_runs"].sum()))
    add("Batting boundary runs use fours and sixes", batting["boundary_runs"].eq(batting["fours"].mul(4).add(batting["sixes"].mul(6))).all(), int((batting["boundary_runs"] - batting["fours"].mul(4).add(batting["sixes"].mul(6))).abs().sum()))
    add("Team runs scored reconcile with deliveries", int(teams["total_runs_scored"].sum()) == int(deliveries["total_runs"].sum()), int(teams["total_runs_scored"].sum() - deliveries["total_runs"].sum()))
    add("Team runs conceded reconcile with deliveries", int(teams["total_runs_conceded"].sum()) == int(deliveries["total_runs"].sum()), int(teams["total_runs_conceded"].sum() - deliveries["total_runs"].sum()))
    expected_bowler_wickets = int(deliveries["dismissal_kind"].isin(BOWLER_WICKET_TYPES).sum())
    add("Bowling wickets reconcile with convention", int(bowling["wickets"].sum()) == expected_bowler_wickets, int(bowling["wickets"].sum() - expected_bowler_wickets))
    add("Team wickets taken reconcile with bowling wickets", int(teams["total_wickets_taken"].sum()) == int(bowling["wickets"].sum()), int(teams["total_wickets_taken"].sum() - bowling["wickets"].sum()))
    add("Team wickets lost reconcile with bowling wickets", int(teams["total_wickets_lost"].sum()) == int(bowling["wickets"].sum()), int(teams["total_wickets_lost"].sum() - bowling["wickets"].sum()))
    add("Bowling legal balls reconcile with deliveries", int(bowling["legal_balls"].sum()) == int(deliveries["legal_ball"].sum()), int(bowling["legal_balls"].sum() - deliveries["legal_ball"].sum()))
    expected_runs_conceded = int((deliveries["total_runs"] - deliveries["extra_runs"].where(deliveries["extras_type"].isin(["byes", "legbyes", "penalty"]), 0)).sum())
    add("Bowling runs conceded reconcile with convention", int(bowling["runs_conceded"].sum()) == expected_runs_conceded, int(bowling["runs_conceded"].sum() - expected_runs_conceded))
    add("Team match outcomes partition appearances", (teams["wins"] + teams["losses"] + teams["ties"] + teams["no_results"]).eq(teams["matches_played"]).all(), int((teams["wins"] + teams["losses"] + teams["ties"] + teams["no_results"] - teams["matches_played"]).abs().sum()))
    add("Win percentage denominator is decided matches", rates_match(teams["win_percentage"], _safe_rate(teams["wins"], teams["wins"] + teams["losses"], 100)), 0)
    add("Toss-to-match-win rate uses eligible toss wins", rates_match(teams["toss_to_match_win_percentage"], _safe_rate(teams["toss_match_wins"], teams["toss_decided_matches"], 100)), 0)
    add("Strike rate uses non-wide balls faced", rates_match(batting["strike_rate"], _safe_rate(batting["runs"], batting["balls_faced"], 100)), 0)
    add("Batting average uses supported dismissals", rates_match(batting["batting_average"], _safe_rate(batting["runs"], batting["dismissals"], 1)), 0)
    add("Boundary percentage uses batter runs", rates_match(batting["boundary_percentage"], _safe_rate(batting["boundary_runs"], batting["runs"], 100)), 0)
    add("Batting dot-ball percentage uses balls faced", rates_match(batting["dot_ball_percentage"], _safe_rate(batting["dot_balls"], batting["balls_faced"], 100)), 0)
    add("Economy rate uses legal balls", rates_match(bowling["economy_rate"], _safe_rate(bowling["runs_conceded"], bowling["legal_balls"], 6)), 0)
    add("Bowling dot-ball percentage uses legal balls", rates_match(bowling["dot_ball_percentage"], _safe_rate(bowling["dot_balls"], bowling["legal_balls"], 100)), 0)
    add("Match summary has no no-result winner/loser", match_summary.loc[match_summary["result"].eq("no result"), ["winning_team", "losing_team"]].isna().all().all(), int(match_summary.loc[match_summary["result"].eq("no result"), ["winning_team", "losing_team"]].notna().sum().sum()))
    add("Tie matches have no manufactured losing team", match_summary.loc[match_summary["result"].eq("tie"), "losing_team"].isna().all(), int(match_summary.loc[match_summary["result"].eq("tie"), "losing_team"].notna().sum()))

    results = pd.DataFrame(rows, columns=["check", "passed", "issue_count"])
    results["status"] = results["passed"].map({True: "PASS", False: "FAIL"})
    return results[["check", "status", "issue_count"]]


def save_feature_datasets(
    datasets: dict[str, pd.DataFrame], root: Path | None = None
) -> dict[str, Path]:
    """Write only the documented analytical outputs under data/processed."""
    root = Path(root) if root is not None else get_project_root()
    processed_dir = root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name, filename in FEATURE_OUTPUT_NAMES.items():
        path = processed_dir / filename
        datasets[name].to_csv(path, index=False, date_format="%Y-%m-%d")
        paths[name] = path
    return paths


def run_feature_engineering(
    root: Path | None = None, save: bool = True
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Build, validate, and optionally save all Phase 6 analytical datasets."""
    root = Path(root) if root is not None else get_project_root()
    matches, deliveries = load_clean_data(root)
    innings = build_innings_summary(matches, deliveries)
    datasets = {
        "innings_summary": innings,
        "match_summary": build_match_features(matches, innings),
        "team_season_summary": build_team_season_summary(matches, deliveries),
        "batting_summary": build_batting_summary(matches, deliveries),
        "bowling_summary": build_bowling_summary(matches, deliveries),
    }
    validation = validate_feature_datasets(matches, deliveries, datasets)
    failures = validation.loc[validation["status"].eq("FAIL")]
    if not failures.empty:
        raise ValueError(f"Feature validation failed:\n{failures.to_string(index=False)}")
    if save:
        save_feature_datasets(datasets, root)
    return datasets, validation


if __name__ == "__main__":
    generated, checks = run_feature_engineering()
    for dataset_name, frame in generated.items():
        print(f"{dataset_name}: {frame.shape[0]:,} rows x {frame.shape[1]} columns")
    print(f"Validation: {checks['status'].eq('PASS').sum()}/{len(checks)} PASS")
