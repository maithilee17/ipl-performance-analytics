# Methodology

## Data acquisition and preservation

The project uses Kaggle IPL match-level and ball-by-ball CSV files stored under `data/raw/`. Raw files are treated as immutable source data. Processing functions load them through project-relative paths and write outputs only under `data/processed/`.

## Exploration

The executed `notebooks/01_data_exploration.ipynb` profiles schema, missingness, keys, categorical values, teams, tosses, batting, bowling, players, venues, and outcomes. It reports raw labels without normalization and distinguishes conditional nulls from possible quality issues.

## Cleaning

The executed `notebooks/02_data_cleaning.ipynb` calls reusable functions in `src/data_cleaning.py`. Cleaning preserves row-level granularity and retains `_raw` audit columns alongside standardized fields. Dates use explicit parsing; season identity is preserved; franchise mappings are conservative; venue mappings are explicit; and city fills occur only when venue evidence is unambiguous.

A recorded delivery is considered legal unless `extras_type` is `wides` or `noballs`. This rule supports later balls-faced and bowling-over calculations without interpreting the recorded `ball` label as legality.

Detailed mappings, affected counts, null decisions, and limitations are in `docs/cleaning_rules.md`.

## Validation

Phase 5 validates the serialized cleaned CSVs rather than only in-memory cleaning results. Checks cover exact schemas, CSV-compatible data types, row grain, keys, referential integrity, documented mappings, date/season consistency, scoring arithmetic, conditional wicket fields, legal deliveries, match outcomes, toss reconciliation, data loss, and raw SHA-256 hashes. Results are returned as PASS/WARN/FAIL records by `src/validation.py` and walked through in `notebooks/03_data_validation.ipynb`.

WARN is reserved for explainable source limitations that do not invalidate analysis. The current data has two: Dr DY Patil Sports Academy is associated with both Mumbai and Navi Mumbai source city labels, and 181 run-out rows lack a named fielder. Neither value is guessed or overwritten. Full evidence is recorded in `docs/data_validation_report.md`.

## Feature engineering

Phase 6 consumes only the serialized cleaned CSVs. Vectorized Pandas groupby and merge operations create match, innings, team-season, batter-season, and bowler-season analytical layers. Team win percentage excludes ties and no-results from its denominator. Batting balls faced exclude wides, while bowling overs and economy use the Phase 4 legal-ball indicator. Bowler wickets and runs conceded use explicitly documented cricket conventions.

## SQL analysis

Phase 7 loads only the five validated Phase 6 summaries into SQLite. Tables use natural primary keys, innings rows reference their match through an enforced foreign key, and reusable views recompute career rates from additive totals. Analytical rate rankings apply documented minimum samples, ordinary toss comparisons exclude ties and no-results, and composite rankings are presented as transparent descriptive summaries rather than official ratings. Database generation uses a validated temporary file followed by atomic replacement so a failed build cannot publish a partial analytical database.

All five outputs are reconciled against cleaned delivery totals before export. Full formulas, grains, null behavior, and limitations are documented in `docs/feature_definitions.md`.
