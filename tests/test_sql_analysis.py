"""Phase 7 tests for the generated SQLite analytical layer."""

import hashlib
import sqlite3

import pytest

from src.data_loader import get_data_paths, get_project_root
from src.sql_analysis import (
    ANALYSIS_FILES,
    EXPECTED_ROWS,
    TABLE_FILES,
    create_database,
    get_sql_paths,
    load_analysis_queries,
)


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def sql_artifacts():
    root = get_project_root()
    data_paths = get_data_paths(root)
    protected = [
        data_paths["matches_raw"],
        data_paths["deliveries_raw"],
        data_paths["matches_clean"],
        data_paths["deliveries_clean"],
        *[root / "data" / "processed" / filename for filename in TABLE_FILES.values()],
    ]
    hashes_before = {path: _hash(path) for path in protected}
    database, validation = create_database(root)
    hashes_after = {path: _hash(path) for path in protected}
    return database, validation, hashes_before, hashes_after


def test_database_build_preserves_all_source_csvs(sql_artifacts):
    database, _, before, after = sql_artifacts
    assert database.is_file()
    assert before == after


def test_database_tables_have_expected_row_counts(sql_artifacts):
    database, validation, _, _ = sql_artifacts
    assert validation["status"].eq("PASS").all(), validation.to_string(index=False)
    with sqlite3.connect(database) as connection:
        for table, expected in EXPECTED_ROWS.items():
            actual = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            assert actual == expected


def test_database_natural_keys_and_foreign_keys(sql_artifacts):
    database, _, _, _ = sql_artifacts
    expected_primary_key_columns = {
        "match_summary": ["match_id"],
        "innings_summary": ["match_id", "inning"],
        "team_season_summary": ["season", "team"],
        "batting_summary": ["season", "batter"],
        "bowling_summary": ["season", "bowler"],
    }
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        for table, expected_columns in expected_primary_key_columns.items():
            info = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
            primary_key = [row[1] for row in sorted(info, key=lambda row: row[5]) if row[5]]
            assert primary_key == expected_columns


def test_all_named_analysis_queries_execute(sql_artifacts):
    database, _, _, _ = sql_artifacts
    query_files = load_analysis_queries()
    assert list(query_files) == ANALYSIS_FILES
    assert sum(len(queries) for queries in query_files.values()) == 30
    with sqlite3.connect(database) as connection:
        for filename, queries in query_files.items():
            for name, query in queries.items():
                try:
                    connection.execute(query).fetchmany(1)
                except sqlite3.Error as error:
                    pytest.fail(f"{filename}/{name} failed: {error}")


def test_advanced_sql_uses_window_functions_meaningfully():
    sql_path = get_sql_paths()["sql_dir"] / "05_advanced_analysis.sql"
    sql = sql_path.read_text(encoding="utf-8").upper()
    assert sql.count("OVER (") >= 6
    assert "RANK()" in sql
    assert "ROW_NUMBER()" in sql
    assert "PARTITION BY" in sql
    assert "LAG(" in sql
