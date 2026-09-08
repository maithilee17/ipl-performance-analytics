-- Team analysis uses standardized Phase 4 names. Career percentages are recomputed
-- from additive numerators and denominators rather than averaging season rates.

-- name: teams_by_total_wins
SELECT team, matches_played, wins, losses, ties, no_results, win_percentage
FROM v_team_overall
ORDER BY wins DESC, win_percentage DESC, team
LIMIT 15;

-- name: qualified_teams_by_win_percentage
SELECT team, decided_matches, wins, losses, win_percentage
FROM v_team_overall
WHERE decided_matches >= 50
ORDER BY win_percentage DESC, wins DESC, team;

-- name: team_matches_played
SELECT team, matches_played, decided_matches, ties, no_results
FROM v_team_overall
ORDER BY matches_played DESC, team;

-- name: team_season_performance
SELECT
    season, team, matches_played, wins, losses, ties, no_results,
    ROUND(win_percentage, 2) AS win_percentage,
    total_runs_scored, total_runs_conceded, total_wickets_taken
FROM team_season_summary
ORDER BY season, wins DESC, win_percentage DESC, team;

-- name: qualified_teams_by_scoring_rate
WITH team_scoring AS (
    SELECT
        batting_team AS team,
        SUM(total_runs) AS runs,
        SUM(legal_balls) AS legal_balls
    FROM innings_summary
    GROUP BY batting_team
)
SELECT
    team,
    runs,
    legal_balls,
    ROUND(6.0 * runs / NULLIF(legal_balls, 0), 2) AS scoring_rate
FROM team_scoring
WHERE legal_balls >= 3000
ORDER BY scoring_rate DESC, runs DESC, team;

-- name: strongest_overall_team_profiles
WITH scoring AS (
    SELECT batting_team AS team, SUM(total_runs) AS runs, SUM(legal_balls) AS legal_balls
    FROM innings_summary
    GROUP BY batting_team
), eligible AS (
    SELECT
        t.team, t.seasons_played, t.matches_played, t.wins, t.decided_matches,
        t.win_percentage, t.total_wickets_taken,
        ROUND(6.0 * s.runs / NULLIF(s.legal_balls, 0), 2) AS scoring_rate
    FROM v_team_overall AS t
    JOIN scoring AS s ON s.team = t.team
    WHERE t.decided_matches >= 50
), ranked AS (
    SELECT *,
        RANK() OVER (ORDER BY wins DESC) AS wins_rank,
        RANK() OVER (ORDER BY win_percentage DESC) AS win_rate_rank,
        RANK() OVER (ORDER BY scoring_rate DESC) AS scoring_rank,
        RANK() OVER (ORDER BY total_wickets_taken DESC) AS wickets_rank
    FROM eligible
)
SELECT *,
    ROUND((wins_rank + win_rate_rank + scoring_rank + wickets_rank) / 4.0, 2)
        AS composite_rank_score
FROM ranked
ORDER BY composite_rank_score, win_rate_rank, wins_rank, team;
