-- Career rates are calculated from summed runs/balls or runs/dismissals.
-- Qualification filters prevent tiny samples from leading rate rankings.

-- name: top_15_run_scorers
SELECT batter, runs, balls_faced, dismissals, strike_rate, batting_average
FROM v_batting_career
ORDER BY runs DESC, strike_rate DESC, batter
LIMIT 15;

-- name: qualified_strike_rate_leaders
SELECT batter, runs, balls_faced, strike_rate, boundary_percentage
FROM v_batting_career
WHERE balls_faced >= 1000
ORDER BY strike_rate DESC, runs DESC, batter
LIMIT 15;

-- name: most_fours
SELECT batter, runs, fours, boundary_percentage
FROM v_batting_career
ORDER BY fours DESC, runs DESC, batter
LIMIT 15;

-- name: most_sixes
SELECT batter, runs, sixes, boundary_percentage
FROM v_batting_career
ORDER BY sixes DESC, runs DESC, batter
LIMIT 15;

-- name: qualified_batting_average_leaders
SELECT batter, runs, dismissals, batting_average, strike_rate
FROM v_batting_career
WHERE dismissals >= 50
ORDER BY batting_average DESC, runs DESC, batter
LIMIT 15;

-- name: top_run_scorers_by_season
WITH ranked AS (
    SELECT
        season, batter, runs, balls_faced, strike_rate,
        RANK() OVER (PARTITION BY season ORDER BY runs DESC) AS season_run_rank
    FROM batting_summary
)
SELECT season, season_run_rank, batter, runs, balls_faced, ROUND(strike_rate, 2) AS strike_rate
FROM ranked
WHERE season_run_rank <= 3
ORDER BY season, season_run_rank, batter;

-- name: high_volume_high_strike_rate_batters
WITH qualified AS (
    SELECT *
    FROM v_batting_career
    WHERE runs >= 2000 AND balls_faced >= 1000
), ranked AS (
    SELECT *,
        RANK() OVER (ORDER BY runs DESC) AS run_rank,
        RANK() OVER (ORDER BY strike_rate DESC) AS strike_rate_rank
    FROM qualified
)
SELECT
    batter, runs, balls_faced, strike_rate, batting_average,
    run_rank, strike_rate_rank,
    ROUND((run_rank + strike_rate_rank) / 2.0, 2) AS combined_rank_score
FROM ranked
ORDER BY combined_rank_score, runs DESC, batter
LIMIT 20;
