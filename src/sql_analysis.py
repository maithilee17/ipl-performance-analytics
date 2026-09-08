"""Build, query, and validate the Phase 7 SQLite analytical layer."""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path

import pandas as pd

from src.data_loader import get_project_root


DATABASE_NAME = "ipl_analysis.db"
TABLE_FILES = {
    "match_summary": "match_summary.csv",
    "innings_summary": "innings_summary.csv",
    "team_season_summary": "team_season_summary.csv",
    "batting_summary": "batting_summary.csv",
    "bowling_summary": "bowling_summary.csv",
}
EXPECTED_ROWS = {
    "match_summary": 1095,
    "innings_summary": 2217,
    "team_season_summary": 146,
    "batting_summary": 2617,
    "bowling_summary": 1948,
}
RECONCILIATION_ANCHORS = {
    "matches": 1095,
    "total_runs": 347756,
    "batter_runs": 330064,
    "extras": 17692,
    "legal_balls": 251471,
    "bowler_credit_wickets": 11815,
}
ANALYSIS_FILES = [
    "01_team_performance.sql",
    "02_batting_analysis.sql",
    "03_bowling_analysis.sql",
    "04_toss_analysis.sql",
    "05_advanced_analysis.sql",
]
EXPECTED_DATABASE_OBJECTS = set(TABLE_FILES) | {
    "idx_batting_runs",
    "idx_bowling_wickets",
    "idx_innings_batting_team",
    "idx_innings_bowling_team",
    "idx_match_summary_season",
    "idx_match_summary_teams",
    "v_team_overall",
    "v_batting_career",
    "v_bowling_career",
    "v_toss_by_season",
}


def get_sql_paths(root: Path | None = None) -> dict[str, Path]:
    """Return portable paths used by the SQL pipeline."""
    root = Path(root) if root is not None else get_project_root()
    return {
        "root": root,
        "processed": root / "data" / "processed",
        "database": root / "data" / "processed" / DATABASE_NAME,
        "schema": root / "sql" / "schema.sql",
        "views": root / "sql" / "views.sql",
        "reconciliation": root / "sql" / "analysis_queries.sql",
        "sql_dir": root / "sql",
    }


def inspect_source_csvs(root: Path | None = None) -> pd.DataFrame:
    """Inspect the five Phase 6 CSVs without changing them."""
    paths = get_sql_paths(root)
    rows = []
    for table, filename in TABLE_FILES.items():
        frame = pd.read_csv(paths["processed"] / filename, low_memory=False)
        rows.append({
            "table_name": table,
            "rows": len(frame),
            "columns": len(frame.columns),
            "null_cells": int(frame.isna().sum().sum()),
            "column_names": ", ".join(frame.columns),
        })
    return pd.DataFrame(rows)


def parse_named_queries(path: Path) -> dict[str, str]:
    """Parse SQL blocks introduced by a ``-- name: identifier`` comment."""
    text = Path(path).read_text(encoding="utf-8")
    matches = list(re.finditer(r"^-- name:\s*([a-z0-9_]+)\s*$", text, re.MULTILINE))
    queries: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        query = text[match.end():end].strip()
        if query.endswith(";"):
            query = query[:-1].rstrip()
        if query:
            queries[match.group(1)] = query
    return queries


def load_analysis_queries(root: Path | None = None) -> dict[str, dict[str, str]]:
    """Load every named query from the five topic files."""
    paths = get_sql_paths(root)
    return {
        filename: parse_named_queries(paths["sql_dir"] / filename)
        for filename in ANALYSIS_FILES
    }


def _sqlite_ready(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert CSV nulls and booleans to sqlite3-compatible Python values."""
    ready = frame.copy()
    for column in ready.select_dtypes(include="bool").columns:
        ready[column] = ready[column].astype(int)
    if "toss_winner_is_match_winner" in ready:
        ready["toss_winner_is_match_winner"] = ready[
            "toss_winner_is_match_winner"
        ].map({True: 1, False: 0})
    return ready.astype(object).where(pd.notna(ready), None)


def inspect_database(database_path: Path) -> pd.DataFrame:
    """Return the tables and views in an existing SQLite database."""
    with sqlite3.connect(database_path) as connection:
        return pd.read_sql_query(
            "SELECT type, name FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name",
            connection,
        )


def create_database(root: Path | None = None) -> tuple[Path, pd.DataFrame]:
    """Atomically build SQLite from the five immutable Phase 6 CSVs."""
    paths = get_sql_paths(root)
    paths["processed"].mkdir(parents=True, exist_ok=True)
    database_path = paths["database"]
    if database_path.exists():
        existing = inspect_database(database_path)
        if not set(existing["name"]).issubset(EXPECTED_DATABASE_OBJECTS):
            raise ValueError("Existing database contains unexpected objects; refusing replacement")

    temporary_path = paths["processed"] / f".{DATABASE_NAME}.tmp"
    if temporary_path.exists():
        temporary_path.unlink()

    schema_sql = paths["schema"].read_text(encoding="utf-8")
    views_sql = paths["views"].read_text(encoding="utf-8")
    connection = sqlite3.connect(temporary_path)
    try:
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(schema_sql)
            for table, filename in TABLE_FILES.items():
                frame = pd.read_csv(paths["processed"] / filename, low_memory=False)
                _sqlite_ready(frame).to_sql(table, connection, if_exists="append", index=False)
            connection.executescript(views_sql)
            connection.commit()
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            foreign_key_issues = connection.execute("PRAGMA foreign_key_check").fetchall()
            if integrity != "ok" or foreign_key_issues:
                raise ValueError(
                    f"SQLite integrity failure: integrity={integrity}, foreign_keys={foreign_key_issues}"
                )
        finally:
            connection.close()
        os.replace(temporary_path, database_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    validation = validate_database(database_path)
    failures = validation.loc[validation["status"].eq("FAIL")]
    if not failures.empty:
        raise ValueError(f"Database validation failed:\n{failures.to_string(index=False)}")
    return database_path, validation


def connect_database(root: Path | None = None) -> sqlite3.Connection:
    """Open the generated database with foreign-key enforcement enabled."""
    path = get_sql_paths(root)["database"]
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def query_dataframe(connection: sqlite3.Connection, query: str) -> pd.DataFrame:
    """Execute one analytical query and return a DataFrame."""
    return pd.read_sql_query(query, connection)


def execute_query_file(
    connection: sqlite3.Connection, path: Path
) -> dict[str, pd.DataFrame]:
    """Execute every named SELECT statement in a SQL file."""
    return {
        name: query_dataframe(connection, query)
        for name, query in parse_named_queries(path).items()
    }


def validate_database(database_path: Path) -> pd.DataFrame:
    """Validate SQLite structure, integrity, row counts, and Phase 6 anchors."""
    checks: list[tuple[str, str, str]] = []

    def add(check: str, passed: bool, actual: object) -> None:
        checks.append((check, "PASS" if passed else "FAIL", str(actual)))

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        fk_issues = connection.execute("PRAGMA foreign_key_check").fetchall()
        add("SQLite integrity check", integrity == "ok", integrity)
        add("Foreign-key check", not fk_issues, len(fk_issues))

        for table, expected in EXPECTED_ROWS.items():
            actual = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            add(f"{table} row count", actual == expected, actual)

        actual_totals = {
            "matches": connection.execute("SELECT COUNT(*) FROM match_summary").fetchone()[0],
            "total_runs": connection.execute("SELECT SUM(total_runs) FROM innings_summary").fetchone()[0],
            "batter_runs": connection.execute("SELECT SUM(batsman_runs) FROM innings_summary").fetchone()[0],
            "extras": connection.execute("SELECT SUM(extra_runs) FROM innings_summary").fetchone()[0],
            "legal_balls": connection.execute("SELECT SUM(legal_balls) FROM innings_summary").fetchone()[0],
            "bowler_credit_wickets": connection.execute("SELECT SUM(wickets) FROM bowling_summary").fetchone()[0],
        }
        for metric, expected in RECONCILIATION_ANCHORS.items():
            actual = actual_totals[metric]
            add(f"{metric} reconciliation", actual == expected, actual)

        cross_table_checks = {
            "Team runs scored reconcile with innings": (
                "SELECT (SELECT SUM(total_runs_scored) FROM team_season_summary) "
                "= (SELECT SUM(total_runs) FROM innings_summary)"
            ),
            "Team runs conceded reconcile with innings": (
                "SELECT (SELECT SUM(total_runs_conceded) FROM team_season_summary) "
                "= (SELECT SUM(total_runs) FROM innings_summary)"
            ),
            "Batting runs reconcile with innings": (
                "SELECT (SELECT SUM(runs) FROM batting_summary) "
                "= (SELECT SUM(batsman_runs) FROM innings_summary)"
            ),
            "Bowling legal balls reconcile with innings": (
                "SELECT (SELECT SUM(legal_balls) FROM bowling_summary) "
                "= (SELECT SUM(legal_balls) FROM innings_summary)"
            ),
            "Team wickets reconcile with bowlers": (
                "SELECT (SELECT SUM(total_wickets_taken) FROM team_season_summary) "
                "= (SELECT SUM(wickets) FROM bowling_summary)"
            ),
        }
        for check, sql in cross_table_checks.items():
            passed = connection.execute(sql).fetchone()[0] == 1
            add(check, passed, "equal" if passed else "different")

        queries = load_analysis_queries(database_path.parents[2])
        query_count = 0
        for filename, named_queries in queries.items():
            for name, query in named_queries.items():
                query_count += 1
                try:
                    connection.execute(query).fetchmany(1)
                    add(f"SQL executes: {filename}/{name}", True, "executed")
                except sqlite3.Error as error:
                    add(f"SQL executes: {filename}/{name}", False, error)
        add("Analysis query inventory", query_count >= 25, query_count)

    return pd.DataFrame(checks, columns=["check", "status", "actual"])


def run_sql_analysis(root: Path | None = None) -> tuple[Path, pd.DataFrame]:
    """Build and validate the complete Phase 7 database."""
    return create_database(root)


if __name__ == "__main__":
    database, results = run_sql_analysis()
    print(f"Database: {database.relative_to(get_project_root())}")
    print(f"Validation: {results['status'].eq('PASS').sum()}/{len(results)} PASS")
