"""Phase 8 validation for Tableau source readiness."""

from src.tableau_validation import TABLEAU_SOURCE_RULES, validate_tableau_sources


def test_all_tableau_readiness_checks_pass():
    results = validate_tableau_sources()
    assert results["status"].eq("PASS").all(), results.loc[
        results["status"].eq("FAIL")
    ].to_string(index=False)


def test_tableau_source_grains_and_expected_rows_are_declared():
    assert {name: rules["rows"] for name, rules in TABLEAU_SOURCE_RULES.items()} == {
        "match_summary": 1095,
        "innings_summary": 2217,
        "team_season_summary": 146,
        "batting_summary": 2617,
        "bowling_summary": 1948,
    }
    assert TABLEAU_SOURCE_RULES["match_summary"]["key"] == ["match_id"]
    assert TABLEAU_SOURCE_RULES["innings_summary"]["key"] == ["match_id", "inning"]
    assert TABLEAU_SOURCE_RULES["team_season_summary"]["key"] == ["season", "team"]
    assert TABLEAU_SOURCE_RULES["batting_summary"]["key"] == ["season", "batter"]
    assert TABLEAU_SOURCE_RULES["bowling_summary"]["key"] == ["season", "bowler"]
