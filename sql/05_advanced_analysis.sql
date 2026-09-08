-- Window-function examples retain ties with RANK and select deterministic single
-- rows with ROW_NUMBER where one result per season is required.

-- name: team_rank_within_season
SELECT
    season, team, matches_played, wins, win_percentage,
    RANK() OVER (
        PARTITION BY season
        ORDER BY wins DESC, win_percentage DESC
    ) AS season_team_rank
FROM team_season_summary
ORDER BY season, season_team_rank, team;

-- name: batter_rank_within_season
SELECT
    season, batter, runs, strike_rate,
    RANK() OVER (PARTITION BY season ORDER BY runs DESC) AS season_run_rank
FROM batting_summary
ORDER BY season, season_run_rank, batter;

-- name: bowler_rank_within_season
SELECT
    season, bowler, wickets, economy_rate,
    RANK() OVER (PARTITION BY season ORDER BY wickets DESC) AS season_wicket_rank
FROM bowling_summary
ORDER BY season, season_wicket_rank, bowler;

-- name: top_batter_each_season
WITH ranked AS (
    SELECT
        season, batter, runs, strike_rate,
        ROW_NUMBER() OVER (
            PARTITION BY season
            ORDER BY runs DESC, strike_rate DESC, batter
        ) AS row_number_in_season
    FROM batting_summary
)
SELECT season, batter, runs, ROUND(strike_rate, 2) AS strike_rate
FROM ranked
WHERE row_number_in_season = 1
ORDER BY season;

-- name: team_vs_season_average
WITH compared AS (
    SELECT
        season, team, wins, win_percentage,
        ROUND(AVG(win_percentage) OVER (PARTITION BY season), 2) AS season_average_win_percentage
    FROM team_season_summary
)
SELECT *,
    ROUND(win_percentage - season_average_win_percentage, 2) AS percentage_points_vs_season_average,
    CASE
        WHEN win_percentage > season_average_win_percentage THEN 'Above season average'
        WHEN win_percentage < season_average_win_percentage THEN 'Below season average'
        ELSE 'At season average'
    END AS comparison
FROM compared
ORDER BY season, percentage_points_vs_season_average DESC, team;

-- name: team_wins_year_over_year
WITH sequenced AS (
    SELECT
        season, team, wins,
        LAG(wins) OVER (
            PARTITION BY team
            ORDER BY CAST(SUBSTR(season, 1, 4) AS INTEGER), season
        ) AS previous_season_wins
    FROM team_season_summary
)
SELECT
    season, team, wins, previous_season_wins,
    wins - previous_season_wins AS change_in_wins
FROM sequenced
ORDER BY team, CAST(SUBSTR(season, 1, 4) AS INTEGER), season;
