PRAGMA foreign_keys = ON;

CREATE TABLE match_summary (
    match_id INTEGER PRIMARY KEY,
    season_label TEXT NOT NULL,
    match_date TEXT NOT NULL,
    city TEXT NOT NULL,
    venue TEXT NOT NULL,
    team1 TEXT NOT NULL,
    team2 TEXT NOT NULL,
    toss_winner TEXT NOT NULL,
    toss_decision TEXT NOT NULL CHECK (toss_decision IN ('bat', 'field')),
    winning_team TEXT,
    result TEXT NOT NULL CHECK (result IN ('runs', 'wickets', 'tie', 'no result')),
    result_margin REAL,
    player_of_match TEXT,
    match_type TEXT NOT NULL,
    super_over TEXT NOT NULL CHECK (super_over IN ('Y', 'N')),
    method TEXT,
    match_decided INTEGER NOT NULL CHECK (match_decided IN (0, 1)),
    toss_winner_is_match_winner INTEGER CHECK (toss_winner_is_match_winner IN (0, 1)),
    losing_team TEXT,
    win_margin_type TEXT CHECK (win_margin_type IN ('runs', 'wickets')),
    match_stage TEXT NOT NULL CHECK (match_stage IN ('League', 'Playoffs', 'Final')),
    innings_count INTEGER NOT NULL CHECK (innings_count > 0),
    match_recorded_deliveries INTEGER NOT NULL CHECK (match_recorded_deliveries >= 0),
    match_legal_balls INTEGER NOT NULL CHECK (match_legal_balls >= 0),
    match_illegal_deliveries INTEGER NOT NULL CHECK (match_illegal_deliveries >= 0),
    match_total_runs INTEGER NOT NULL CHECK (match_total_runs >= 0),
    match_batsman_runs INTEGER NOT NULL CHECK (match_batsman_runs >= 0),
    match_extra_runs INTEGER NOT NULL CHECK (match_extra_runs >= 0),
    match_wickets INTEGER NOT NULL CHECK (match_wickets >= 0),
    match_bowler_wickets INTEGER NOT NULL CHECK (match_bowler_wickets >= 0),
    match_fours INTEGER NOT NULL CHECK (match_fours >= 0),
    match_sixes INTEGER NOT NULL CHECK (match_sixes >= 0),
    match_dot_balls INTEGER NOT NULL CHECK (match_dot_balls >= 0),
    CHECK (team1 <> team2),
    CHECK (toss_winner IN (team1, team2)),
    CHECK (match_recorded_deliveries = match_legal_balls + match_illegal_deliveries),
    CHECK (match_total_runs = match_batsman_runs + match_extra_runs)
);

CREATE TABLE innings_summary (
    match_id INTEGER NOT NULL,
    season TEXT NOT NULL,
    inning INTEGER NOT NULL CHECK (inning > 0),
    batting_team TEXT NOT NULL,
    bowling_team TEXT NOT NULL,
    recorded_deliveries INTEGER NOT NULL CHECK (recorded_deliveries >= 0),
    legal_balls INTEGER NOT NULL CHECK (legal_balls >= 0),
    illegal_deliveries INTEGER NOT NULL CHECK (illegal_deliveries >= 0),
    total_runs INTEGER NOT NULL CHECK (total_runs >= 0),
    batsman_runs INTEGER NOT NULL CHECK (batsman_runs >= 0),
    extra_runs INTEGER NOT NULL CHECK (extra_runs >= 0),
    wickets INTEGER NOT NULL CHECK (wickets >= 0),
    bowler_wickets INTEGER NOT NULL CHECK (bowler_wickets >= 0),
    fours INTEGER NOT NULL CHECK (fours >= 0),
    sixes INTEGER NOT NULL CHECK (sixes >= 0),
    dot_balls INTEGER NOT NULL CHECK (dot_balls >= 0),
    run_rate REAL NOT NULL CHECK (run_rate >= 0),
    PRIMARY KEY (match_id, inning),
    FOREIGN KEY (match_id) REFERENCES match_summary(match_id),
    CHECK (batting_team <> bowling_team),
    CHECK (recorded_deliveries = legal_balls + illegal_deliveries),
    CHECK (total_runs = batsman_runs + extra_runs)
) WITHOUT ROWID;

CREATE TABLE team_season_summary (
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    matches_played INTEGER NOT NULL CHECK (matches_played >= 0),
    decided_matches INTEGER NOT NULL CHECK (decided_matches >= 0),
    wins INTEGER NOT NULL CHECK (wins >= 0),
    losses INTEGER NOT NULL CHECK (losses >= 0),
    ties INTEGER NOT NULL CHECK (ties >= 0),
    no_results INTEGER NOT NULL CHECK (no_results >= 0),
    win_percentage REAL NOT NULL CHECK (win_percentage BETWEEN 0 AND 100),
    total_runs_scored INTEGER NOT NULL CHECK (total_runs_scored >= 0),
    total_runs_conceded INTEGER NOT NULL CHECK (total_runs_conceded >= 0),
    average_runs_scored REAL NOT NULL CHECK (average_runs_scored >= 0),
    average_runs_conceded REAL NOT NULL CHECK (average_runs_conceded >= 0),
    total_wickets_taken INTEGER NOT NULL CHECK (total_wickets_taken >= 0),
    total_wickets_lost INTEGER NOT NULL CHECK (total_wickets_lost >= 0),
    toss_wins INTEGER NOT NULL CHECK (toss_wins >= 0),
    toss_decided_matches INTEGER NOT NULL CHECK (toss_decided_matches >= 0),
    toss_match_wins INTEGER NOT NULL CHECK (toss_match_wins >= 0),
    toss_to_match_win_percentage REAL NOT NULL CHECK (toss_to_match_win_percentage BETWEEN 0 AND 100),
    PRIMARY KEY (season, team),
    CHECK (decided_matches = wins + losses),
    CHECK (matches_played = wins + losses + ties + no_results)
) WITHOUT ROWID;

CREATE TABLE batting_summary (
    season TEXT NOT NULL,
    batter TEXT NOT NULL,
    matches INTEGER NOT NULL CHECK (matches >= 0),
    runs INTEGER NOT NULL CHECK (runs >= 0),
    balls_faced INTEGER NOT NULL CHECK (balls_faced >= 0),
    fours INTEGER NOT NULL CHECK (fours >= 0),
    sixes INTEGER NOT NULL CHECK (sixes >= 0),
    boundary_runs INTEGER NOT NULL CHECK (boundary_runs >= 0),
    dot_balls INTEGER NOT NULL CHECK (dot_balls >= 0),
    dismissals INTEGER NOT NULL CHECK (dismissals >= 0),
    strike_rate REAL NOT NULL CHECK (strike_rate >= 0),
    batting_average REAL,
    boundary_percentage REAL,
    dot_ball_percentage REAL NOT NULL CHECK (dot_ball_percentage BETWEEN 0 AND 100),
    PRIMARY KEY (season, batter),
    CHECK (boundary_runs = fours * 4 + sixes * 6)
) WITHOUT ROWID;

CREATE TABLE bowling_summary (
    season TEXT NOT NULL,
    bowler TEXT NOT NULL,
    matches INTEGER NOT NULL CHECK (matches >= 0),
    legal_balls INTEGER NOT NULL CHECK (legal_balls >= 0),
    overs_bowled REAL NOT NULL CHECK (overs_bowled >= 0),
    runs_conceded INTEGER NOT NULL CHECK (runs_conceded >= 0),
    wickets INTEGER NOT NULL CHECK (wickets >= 0),
    economy_rate REAL NOT NULL CHECK (economy_rate >= 0),
    dot_balls INTEGER NOT NULL CHECK (dot_balls >= 0),
    dot_ball_percentage REAL NOT NULL CHECK (dot_ball_percentage BETWEEN 0 AND 100),
    wides INTEGER NOT NULL CHECK (wides >= 0),
    no_balls INTEGER NOT NULL CHECK (no_balls >= 0),
    PRIMARY KEY (season, bowler)
) WITHOUT ROWID;

CREATE INDEX idx_match_summary_season ON match_summary(season_label);
CREATE INDEX idx_match_summary_teams ON match_summary(team1, team2);
CREATE INDEX idx_innings_batting_team ON innings_summary(season, batting_team);
CREATE INDEX idx_innings_bowling_team ON innings_summary(season, bowling_team);
CREATE INDEX idx_batting_runs ON batting_summary(batter, runs);
CREATE INDEX idx_bowling_wickets ON bowling_summary(bowler, wickets);
