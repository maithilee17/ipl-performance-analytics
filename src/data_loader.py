"""Path and CSV loading utilities for the IPL analytics project."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def get_project_root() -> Path:
    """Derive the repository root without a computer-specific absolute path."""
    return Path(__file__).resolve().parents[1]


def get_data_paths(root: Path | None = None) -> dict[str, Path]:
    """Return the project data paths used by the reproducible pipeline."""
    root = Path(root) if root is not None else get_project_root()
    return {
        "matches_raw": root / "data" / "raw" / "matches.csv",
        "deliveries_raw": root / "data" / "raw" / "deliveries.csv",
        "matches_clean": root / "data" / "processed" / "matches_clean.csv",
        "deliveries_clean": root / "data" / "processed" / "deliveries_clean.csv",
        "match_summary": root / "data" / "processed" / "match_summary.csv",
        "innings_summary": root / "data" / "processed" / "innings_summary.csv",
        "team_season_summary": root / "data" / "processed" / "team_season_summary.csv",
        "batting_summary": root / "data" / "processed" / "batting_summary.csv",
        "bowling_summary": root / "data" / "processed" / "bowling_summary.csv",
        "ipl_analysis_db": root / "data" / "processed" / "ipl_analysis.db",
    }


def load_raw_data(root: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load both raw CSV files without mutating or writing either source."""
    paths = get_data_paths(root)
    matches = pd.read_csv(paths["matches_raw"], low_memory=False)
    deliveries = pd.read_csv(paths["deliveries_raw"], low_memory=False)
    return matches, deliveries


def load_clean_data(root: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the Phase 4 CSVs with the date field restored for validation."""
    paths = get_data_paths(root)
    matches = pd.read_csv(
        paths["matches_clean"], parse_dates=["match_date"], low_memory=False
    )
    deliveries = pd.read_csv(paths["deliveries_clean"], low_memory=False)
    return matches, deliveries


def load_feature_data(root: Path | None = None) -> dict[str, pd.DataFrame]:
    """Load all Phase 6 analytical CSVs using their documented schemas."""
    paths = get_data_paths(root)
    return {
        "match_summary": pd.read_csv(
            paths["match_summary"], parse_dates=["match_date"], low_memory=False
        ),
        "innings_summary": pd.read_csv(paths["innings_summary"], low_memory=False),
        "team_season_summary": pd.read_csv(paths["team_season_summary"], low_memory=False),
        "batting_summary": pd.read_csv(paths["batting_summary"], low_memory=False),
        "bowling_summary": pd.read_csv(paths["bowling_summary"], low_memory=False),
    }
