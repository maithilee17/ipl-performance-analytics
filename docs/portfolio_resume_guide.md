# Portfolio, resume, and interview guide

## Portfolio description

**IPL Performance Analytics Dashboard** is an interactive analytics project combining reproducible Python/Pandas data preparation, SQLite and SQL analysis, and Tableau visualization. It examines match, team, batting, bowling, and season-level IPL performance from 2008 through 2024. The completed dashboard lets users select a season and dynamically review match and run totals, recorded wickets, team wins, and top batting and bowling performers.

## Verified portfolio highlights

- 1,095 matches and 260,920 recorded deliveries were processed without changing the raw files.
- Five validated analytical datasets support match, innings, team-season, batter-season, and bowler-season analysis.
- The SQLite layer contains five analytical tables and 30 named queries.
- The packaged Tableau workbook contains one dashboard, nine worksheets, three active extracts, and four season filter actions.
- Project totals reconcile to 347,756 match runs, 330,064 batter runs, 17,692 extras, 251,471 legal balls, and 11,815 bowler-credit wickets.

## Resume bullets

- Built an interactive IPL Performance Analytics Dashboard in Tableau to analyze 1,095 matches across team wins, season trends, batting performance, bowling performance, runs, and wickets.
- Implemented four season-selection actions that dynamically update season-sensitive KPI cards, team wins, and Top 10 batter and bowler views while preserving overall context KPIs.
- Prepared, validated, and analyzed 260,920 delivery records using Python/Pandas and SQLite SQL, producing five grain-safe analytical datasets and 30 reusable queries for Tableau reporting.

## Skills

Python, Pandas, SQL, SQLite, Tableau, data cleaning, data validation, data analysis, feature engineering, data visualization, dashboard development, and interactive data visualization.

## Interview answer: What did you do in this IPL project?

I wanted to turn detailed IPL match and ball-by-ball data into a portfolio project that answers clear performance questions rather than just displaying raw statistics. I worked with 1,095 matches and about 261,000 delivery records. I first inspected and cleaned the data, documented historical team and venue naming differences, preserved meaningful missing values, and validated cricket-specific rules such as legal deliveries and bowler-credit wickets. I then created match, innings, team-season, batting, and bowling summaries and used SQLite SQL to rank teams and players and analyze season and toss patterns. Finally, I connected the validated match, batting, and bowling summaries to Tableau and built an interactive dashboard with KPI cards, team wins, season trends, and Top 10 player views. Selecting a season updates the relevant metrics and rankings, making the results easier to compare and communicate.

## Interview questions and answers

### Why did you choose this project?

IPL data is familiar enough to explain quickly but detailed enough to demonstrate real analytical decisions. It includes two related grains—matches and deliveries—plus historical naming, conditional missing values, and domain-specific rules. That made it a good project for showing the complete path from raw data to a decision-oriented dashboard.

### What was your role?

I completed the full analyst workflow: repository setup, data inspection, EDA, cleaning, validation, feature engineering, SQL analysis, Tableau data preparation, dashboard implementation, verification, and documentation.

### How did you clean the data?

I preserved the raw CSVs and produced separate cleaned files. I parsed dates, retained the original season labels, mapped four documented team-name changes, standardized defensible venue and city aliases, and filled only the 51 missing Dubai/Sharjah cities supported unambiguously by venue. I kept meaningful nulls, such as dismissal fields when no wicket occurred. For delivery analysis, wides and no-balls were marked illegal while every recorded row—including ball numbers above six—was retained.

### Why Tableau?

Tableau made the validated results accessible through a compact visual interface. It was well suited to the dashboard's KPI cards, ranked bars, player tables, season trend, and click-based filtering, while Python and SQL remained responsible for reproducible preparation and analysis.

### How does the season filter work?

`Matches by Season` is the action source. Selecting a season triggers four filter actions that update Total Matches, Total Runs, Total Wickets, Wins by Team, Top 10 Batters, and Top 10 Bowlers. Total Teams and Total Seasons remain overall context KPIs. This interaction was manually tested in Tableau.

### What are the main dashboard KPIs?

The dashboard displays Total Matches, Total Runs, Total Teams, Total Seasons, and Total Wickets. The wicket KPI counts all recorded wicket events; the bowler ranking uses bowler-credit wickets and excludes run outs according to the documented convention.

### What challenges did you face?

The main challenges were preserving cricket meaning while cleaning the data, avoiding double counting across datasets with different grains, and keeping the Tableau interactions consistent across separate match, batting, and bowling sources. Historical team and venue names also required explicit, auditable mappings rather than broad fuzzy matching.

### What would you improve?

I would add a verified dashboard image and a Tableau Public link, then refine the dashboard's documented limitations in a future workbook version: its fixed 1000 × 800 layout, saved 2021 filter state, and the distinction between all recorded wickets on the KPI card and bowler-credit wickets in the bowling analysis. I would preserve the verified workbook as the baseline rather than silently changing it.

## GitHub publication checklist

1. Capture `screenshots/IPL_Performance_Analytics_Dashboard.png` from the completed Tableau dashboard.
2. Initialize Git in the project root or create a GitHub repository and connect it as the remote.
3. Review `git status` before the first commit. Raw CSVs, generated processed data, the virtual environment, and SQLite database are already excluded by `.gitignore`.
4. Confirm the Kaggle dataset's license and add the exact dataset link/attribution before publishing.
5. Commit the packaged workbook, documentation, notebooks, Python modules, SQL, tests, and screenshot.
6. Run `python -m pytest -q` and `python -m pip check`, then record the results in the release or repository notes.
7. Optionally publish the workbook on Tableau Public and add its verified URL to the root README.

## Accuracy notes

- No Tableau calculated fields or parameters were verified in the workbook, so none are claimed here.
- The dashboard has one completed view, not the five-dashboard architecture proposed during planning.
- Tableau's Total Wickets card totals 12,950 all-dismissal events; the 11,815 project anchor is the bowler-credit total.
- The screenshot and Tableau Public URL are future manual actions until they exist and are verified.
