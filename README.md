# IPL Performance Analytics Dashboard

An end-to-end data analytics portfolio project that uses Python, Pandas, SQLite, SQL, and Tableau to examine IPL team, player, match, and season performance from 2008 through 2024.

## Overview

The project turns ball-by-ball and match-level IPL data into a validated analytical layer and an interactive Tableau dashboard. It covers data inspection, exploratory analysis, cleaning, validation, feature engineering, SQL analysis, visualization design, and dashboard delivery.

The completed Tableau dashboard lets a user select a season from the match trend and explore season-sensitive match, run, wicket, team-win, batting, and bowling views. Overall team and season cards remain contextual totals where appropriate.

## Objectives

- Build a reproducible pipeline without changing the source CSV files.
- Standardize documented team, venue, city, season, and date fields while retaining raw values for auditability.
- Produce grain-safe match, innings, team-season, batter-season, and bowler-season datasets.
- Answer practical performance questions with SQL and validated minimum-sample rules.
- Present the main results in a focused, interactive Tableau dashboard.

## Dataset

The source data consists of two Kaggle CSV files:

- `matches.csv`: 1,095 matches and 20 raw columns
- `deliveries.csv`: 260,920 recorded deliveries and 17 raw columns

The data spans 17 IPL season labels and includes match details, teams, venues, results, delivery outcomes, batters, bowlers, extras, and dismissals. The raw files are excluded from version control and remain unchanged throughout the project.

## Dataset attribution

This project uses the **IPL Complete Dataset (2008–2024)** published on Kaggle by **Prateek Bhardwaj**.

- Kaggle: [IPL Complete Dataset (2008–2024)](https://www.kaggle.com/datasets/patrickb1912/ipl-complete-dataset-20082020)
- Data source acknowledged by the dataset: **Cricsheet**
- License listed on Kaggle: **Open Database, Open Database Contents**

The raw and processed dataset files are intentionally excluded from this repository in accordance with the project's data-handling policy. The project code, analysis, SQL, notebooks, Tableau workbook, and dashboard screenshot are included.

## Data preparation

The Python workflow:

- parses match dates without failures and preserves original season labels;
- applies four documented historical team-name mappings, reducing 19 raw labels to 15 standardized labels;
- standardizes documented venue and city aliases and fills 51 unambiguous Dubai/Sharjah city values;
- preserves meaningful conditional nulls in dismissal, result, and method fields;
- treats wides and no-balls as illegal deliveries while retaining every recorded delivery; and
- validates keys, run arithmetic, wicket logic, team consistency, and cross-table referential integrity.

Detailed rules and definitions are in [`docs/cleaning_rules.md`](docs/cleaning_rules.md), [`docs/data_dictionary.md`](docs/data_dictionary.md), and [`docs/feature_definitions.md`](docs/feature_definitions.md).

## Tools and technologies

- Python 3.11
- Pandas and NumPy
- Matplotlib and Seaborn
- Jupyter Notebook
- SQLite via Python's standard-library `sqlite3` module
- SQL
- pytest
- Tableau Public/Desktop

## Analysis

Five reusable analytical datasets support the SQL and Tableau layers:

| Dataset | Grain | Rows |
|---|---|---:|
| `match_summary.csv` | One row per match | 1,095 |
| `innings_summary.csv` | One row per match and innings | 2,217 |
| `team_season_summary.csv` | One row per season and standardized team | 146 |
| `batting_summary.csv` | One row per season and batter | 2,617 |
| `bowling_summary.csv` | One row per season and bowler | 1,948 |

The SQLite layer contains these five tables, natural keys, an innings-to-match foreign key, four reusable views, and 30 named queries covering team, batting, bowling, toss, and window-function analysis. See [`docs/sql_analysis.md`](docs/sql_analysis.md) for methodology, qualification thresholds, and reconciliation evidence.

Important formulas include:

- strike rate = runs / balls faced × 100;
- economy rate and innings run rate = runs / legal balls × 6; and
- win percentage = wins / (wins + losses) × 100, excluding ties and no-results.

## Tableau dashboard

The packaged workbook is [`tableau/IPL_Performance_Analytics.twbx`](tableau/IPL_Performance_Analytics.twbx). It contains one dashboard, `IPL Performance Dashboard`, with the visible title **IPL Performance Analytics Dashboard**.

The dashboard includes:

- KPI cards: Total Matches, Total Runs, Total Teams, Total Seasons, and Total Wickets
- ranked views: Wins by Team, Top 10 Batters, and Top 10 Bowlers
- time view: Matches by Season

Selecting a season in `Matches by Season` filters Total Matches, Total Runs, Total Wickets, Wins by Team, Top 10 Batters, and Top 10 Bowlers. Total Teams and Total Seasons remain overall context cards. Four filter actions implement this workflow, which was manually tested in Tableau.

The wicket card uses all recorded wicket events (`match_wickets`, 12,950 overall). Bowler rankings use bowler-credit wickets (11,815), which exclude run outs and follow the documented project convention. This distinction is intentional documentation of the existing workbook; the workbook was not altered during portfolio packaging.

Read [`docs/tableau_workbook_validation.md`](docs/tableau_workbook_validation.md) for the package checksum, worksheet inventory, data-source inspection, saved 2021 filter state, and validation limitations.

## Key insights

The following findings were recalculated from the validated analytical datasets:

- The 2013 season contains the most matches in the data, with 76.
- The 2024 season has the highest aggregate match runs, with 25,971.
- Mumbai Indians lead the standardized franchise table with 142 match wins.
- Chennai Super Kings have a 58.47% win rate across 236 decided matches, the highest in the Phase 7 qualified team comparison.
- Virat Kohli is the leading batter by aggregate runs with 8,014.
- YS Chahal is the leading bowler under the bowler-credit convention with 205 wickets.
- Toss winners also won 548 of 1,076 eligible matches (50.93%); this is descriptive association, not evidence that the toss caused the result.

## Project workflow

1. Acquire and preserve the source data.
2. Inspect structure, missingness, values, and table relationships.
3. Perform reproducible exploratory analysis.
4. Clean documented fields without overwriting raw data.
5. Validate schema, keys, cricket logic, and cross-table integrity.
6. Engineer match, innings, team, batting, and bowling features.
7. Build and reconcile a SQLite analytical layer.
8. Design the Tableau data model and dashboard architecture.
9. Build and verify the packaged Tableau workbook.
10. Package the project for portfolio, GitHub, resume, and interview use.

## Repository structure

```text
ipl_performance_analysis/
├── data/
│   ├── raw/                 # Original CSVs; ignored by Git
│   └── processed/           # Generated cleaned and analytical artifacts
├── docs/                    # Methodology, validation, and portfolio notes
├── notebooks/               # EDA, cleaning, validation, features, and SQL
├── screenshots/             # Dashboard image guidance / future capture
├── sql/                     # Schema, views, and 30 analytical queries
├── src/                     # Reusable Python pipeline modules
├── tableau/                 # Packaged workbook and Tableau notes
├── tests/                   # Data, SQL, and Tableau-readiness tests
├── requirements.txt
└── README.md
```

## How to use

Create the environment from the project root in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
```

Because raw and generated data are intentionally ignored by Git, place the original `matches.csv` and `deliveries.csv` files in `data/raw/` before reproducing the pipeline. Execute the notebooks in phase order or use the reusable modules documented in each phase. Regenerate the SQLite layer with:

```powershell
python -m src.sql_analysis
```

Open `tableau/IPL_Performance_Analytics.twbx` in Tableau Public/Desktop to explore the packaged dashboard. The embedded extracts allow the saved views to render; refreshing original CSV connections on another computer may require relinking them.

## Skills demonstrated

Python, Pandas, SQL, SQLite, Tableau, data cleaning, data validation, exploratory data analysis, feature engineering, data visualization, dashboard development, and interactive analytical storytelling.

## Future improvements

- Capture and add a final dashboard screenshot for the GitHub landing page.
- Publish the workbook to a Tableau Public profile and add the verified public link.
- Add a license-appropriate sample or documented dataset acquisition link to simplify reproduction without committing the full data.

These items are future work and are not presented as completed features.
