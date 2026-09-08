-- Career team results; ties/no-results are outside the win-rate denominator.
CREATE VIEW v_team_overall AS
SELECT
    team,
    COUNT(*) AS seasons_played,
    SUM(matches_played) AS matches_played,
    SUM(decided_matches) AS decided_matches,
    SUM(wins) AS wins,
    SUM(losses) AS losses,
    SUM(ties) AS ties,
    SUM(no_results) AS no_results,
    ROUND(100.0 * SUM(wins) / NULLIF(SUM(decided_matches), 0), 2) AS win_percentage,
    SUM(total_runs_scored) AS total_runs_scored,
    SUM(total_runs_conceded) AS total_runs_conceded,
    SUM(total_wickets_taken) AS total_wickets_taken,
    SUM(toss_wins) AS toss_wins,
    SUM(toss_decided_matches) AS toss_decided_matches,
    SUM(toss_match_wins) AS toss_match_wins,
    ROUND(100.0 * SUM(toss_match_wins) / NULLIF(SUM(toss_decided_matches), 0), 2)
        AS toss_to_match_win_percentage
FROM team_season_summary
GROUP BY team;

CREATE VIEW v_batting_career AS
SELECT
    batter,
    COUNT(*) AS seasons_played,
    SUM(matches) AS season_match_appearances,
    SUM(runs) AS runs,
    SUM(balls_faced) AS balls_faced,
    SUM(fours) AS fours,
    SUM(sixes) AS sixes,
    SUM(boundary_runs) AS boundary_runs,
    SUM(dot_balls) AS dot_balls,
    SUM(dismissals) AS dismissals,
    ROUND(100.0 * SUM(runs) / NULLIF(SUM(balls_faced), 0), 2) AS strike_rate,
    ROUND(1.0 * SUM(runs) / NULLIF(SUM(dismissals), 0), 2) AS batting_average,
    ROUND(100.0 * SUM(boundary_runs) / NULLIF(SUM(runs), 0), 2) AS boundary_percentage,
    ROUND(100.0 * SUM(dot_balls) / NULLIF(SUM(balls_faced), 0), 2) AS dot_ball_percentage
FROM batting_summary
GROUP BY batter;

CREATE VIEW v_bowling_career AS
SELECT
    bowler,
    COUNT(*) AS seasons_played,
    SUM(matches) AS season_match_appearances,
    SUM(legal_balls) AS legal_balls,
    ROUND(SUM(legal_balls) / 6.0, 2) AS overs_bowled,
    SUM(runs_conceded) AS runs_conceded,
    SUM(wickets) AS wickets,
    ROUND(6.0 * SUM(runs_conceded) / NULLIF(SUM(legal_balls), 0), 2) AS economy_rate,
    SUM(dot_balls) AS dot_balls,
    ROUND(100.0 * SUM(dot_balls) / NULLIF(SUM(legal_balls), 0), 2) AS dot_ball_percentage,
    SUM(wides) AS wides,
    SUM(no_balls) AS no_balls
FROM bowling_summary
GROUP BY bowler;

CREATE VIEW v_toss_by_season AS
SELECT
    season_label AS season,
    COUNT(*) AS eligible_matches,
    SUM(CASE WHEN toss_winner = winning_team THEN 1 ELSE 0 END) AS toss_winner_match_wins,
    ROUND(100.0 * SUM(CASE WHEN toss_winner = winning_team THEN 1 ELSE 0 END) / COUNT(*), 2)
        AS toss_winner_match_win_percentage
FROM match_summary
WHERE result IN ('runs', 'wickets')
GROUP BY season_label;
