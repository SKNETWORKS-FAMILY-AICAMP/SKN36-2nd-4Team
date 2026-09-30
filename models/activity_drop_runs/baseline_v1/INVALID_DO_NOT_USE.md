# Do not use this run

This exploratory run included users whose match histories were truncated to
the last 30 matches. Requiring an observed match before each 7-day window then
selected examples partly based on *future* activity: sufficiently many later
matches push earlier ones out of that last-30 tail. The unusually high
top-10% baseline result is therefore not a trustworthy forecast score.

The run is retained only as an audit trail. Use the `uncapped_v2` experiment,
which requires `sequence_events` count to equal `ml_features.actual_history_matches`.
