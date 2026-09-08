-- Toss analysis is descriptive. Eligible matches have an ordinary runs/wickets
-- result; ties and no-results are excluded from normal win comparisons.

-- name: overall_toss_winner_match_win_rate
SELECT
    COUNT(*) AS eligible_matches,
    SUM(CASE WHEN toss_winner = winning_team THEN 1 ELSE 0 END) AS toss_winner_match_wins,
    ROUND(100.0 * SUM(CASE WHEN toss_winner = winning_team THEN 1 ELSE 0 END) / COUNT(*), 2)
        AS toss_winner_match_win_percentage
FROM match_summary
WHERE result IN ('runs', 'wickets');

-- name: qualified_team_toss_win_percentage
SELECT
    team, matches_played, toss_wins,
    ROUND(100.0 * toss_wins / NULLIF(matches_played, 0), 2) AS toss_win_percentage
FROM v_team_overall
WHERE matches_played >= 50
ORDER BY toss_win_percentage DESC, toss_wins DESC, team;

-- name: qualified_team_toss_to_match_win_percentage
SELECT
    team, toss_decided_matches, toss_match_wins, toss_to_match_win_percentage
FROM v_team_overall
WHERE toss_decided_matches >= 25
ORDER BY toss_to_match_win_percentage DESC, toss_match_wins DESC, team;

-- name: toss_relationship_by_season
SELECT season, eligible_matches, toss_winner_match_wins, toss_winner_match_win_percentage
FROM v_toss_by_season
ORDER BY season;

-- name: team_toss_win_rate_difference
WITH participation AS (
    SELECT match_id, team1 AS team, toss_winner, winning_team
    FROM match_summary WHERE result IN ('runs', 'wickets')
    UNION ALL
    SELECT match_id, team2 AS team, toss_winner, winning_team
    FROM match_summary WHERE result IN ('runs', 'wickets')
), team_split AS (
    SELECT
        team,
        SUM(CASE WHEN team = toss_winner THEN 1 ELSE 0 END) AS toss_won_matches,
        SUM(CASE WHEN team = toss_winner AND team = winning_team THEN 1 ELSE 0 END) AS wins_after_toss_win,
        SUM(CASE WHEN team <> toss_winner THEN 1 ELSE 0 END) AS toss_lost_matches,
        SUM(CASE WHEN team <> toss_winner AND team = winning_team THEN 1 ELSE 0 END) AS wins_after_toss_loss
    FROM participation
    GROUP BY team
)
SELECT
    team, toss_won_matches, wins_after_toss_win,
    ROUND(100.0 * wins_after_toss_win / NULLIF(toss_won_matches, 0), 2) AS win_rate_after_toss_win,
    toss_lost_matches, wins_after_toss_loss,
    ROUND(100.0 * wins_after_toss_loss / NULLIF(toss_lost_matches, 0), 2) AS win_rate_after_toss_loss,
    ROUND(
        100.0 * wins_after_toss_win / NULLIF(toss_won_matches, 0)
        - 100.0 * wins_after_toss_loss / NULLIF(toss_lost_matches, 0), 2
    ) AS descriptive_percentage_point_difference
FROM team_split
WHERE toss_won_matches >= 20 AND toss_lost_matches >= 20
ORDER BY descriptive_percentage_point_difference DESC, team;
