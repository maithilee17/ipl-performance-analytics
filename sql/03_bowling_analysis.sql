-- Wickets follow the Phase 6 bowler-credit convention. Economy is calculated
-- from bowler-chargeable runs per six legal balls.

-- name: top_15_wicket_takers
SELECT bowler, wickets, legal_balls, economy_rate, dot_ball_percentage
FROM v_bowling_career
ORDER BY wickets DESC, economy_rate, bowler
LIMIT 15;

-- name: qualified_economy_leaders
SELECT bowler, legal_balls, wickets, economy_rate, dot_ball_percentage
FROM v_bowling_career
WHERE legal_balls >= 1200
ORDER BY economy_rate, wickets DESC, bowler
LIMIT 15;

-- name: top_wicket_takers_by_season
WITH ranked AS (
    SELECT
        season, bowler, wickets, legal_balls, economy_rate,
        RANK() OVER (PARTITION BY season ORDER BY wickets DESC) AS season_wicket_rank
    FROM bowling_summary
)
SELECT season, season_wicket_rank, bowler, wickets, legal_balls, ROUND(economy_rate, 2) AS economy_rate
FROM ranked
WHERE season_wicket_rank <= 3
ORDER BY season, season_wicket_rank, bowler;

-- name: high_wicket_good_economy_bowlers
SELECT bowler, wickets, legal_balls, economy_rate, dot_ball_percentage
FROM v_bowling_career
WHERE wickets >= 100
ORDER BY economy_rate, wickets DESC, bowler;

-- name: most_legal_balls_bowled
SELECT bowler, legal_balls, overs_bowled, wickets, economy_rate
FROM v_bowling_career
ORDER BY legal_balls DESC, wickets DESC, bowler
LIMIT 15;

-- name: strongest_overall_bowling_profiles
WITH qualified AS (
    SELECT * FROM v_bowling_career WHERE legal_balls >= 1200
), ranked AS (
    SELECT *,
        RANK() OVER (ORDER BY wickets DESC) AS wicket_rank,
        RANK() OVER (ORDER BY economy_rate) AS economy_rank,
        RANK() OVER (ORDER BY dot_ball_percentage DESC) AS dot_rank
    FROM qualified
)
SELECT
    bowler, wickets, legal_balls, economy_rate, dot_ball_percentage,
    wicket_rank, economy_rank, dot_rank,
    ROUND((wicket_rank + economy_rank + dot_rank) / 3.0, 2) AS composite_rank_score
FROM ranked
ORDER BY composite_rank_score, wicket_rank, bowler
LIMIT 20;
