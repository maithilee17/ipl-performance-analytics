-- Reconciliation and inventory queries shared by the Phase 7 build.

-- name: table_row_counts
SELECT 'match_summary' AS table_name, COUNT(*) AS row_count FROM match_summary
UNION ALL SELECT 'innings_summary', COUNT(*) FROM innings_summary
UNION ALL SELECT 'team_season_summary', COUNT(*) FROM team_season_summary
UNION ALL SELECT 'batting_summary', COUNT(*) FROM batting_summary
UNION ALL SELECT 'bowling_summary', COUNT(*) FROM bowling_summary;

-- name: reconciliation_totals
SELECT
    (SELECT COUNT(*) FROM match_summary) AS matches,
    (SELECT SUM(total_runs) FROM innings_summary) AS total_runs,
    (SELECT SUM(batsman_runs) FROM innings_summary) AS batter_runs,
    (SELECT SUM(extra_runs) FROM innings_summary) AS extras,
    (SELECT SUM(legal_balls) FROM innings_summary) AS legal_balls,
    (SELECT SUM(wickets) FROM bowling_summary) AS bowler_credit_wickets;
