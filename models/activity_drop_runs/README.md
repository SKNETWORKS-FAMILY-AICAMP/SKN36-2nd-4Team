# Invalid activity-drop audits — do not deploy

Both folders are retained only to document a failed feasibility check.
The database keeps at most the last 30 matches per user. Historical seven-day
activity-drop labels built from this one snapshot suffer selection bias:
whether a user has a complete-looking earlier window depends on later matches.
The `uncapped_v2` restriction also conditions on the user's full-window match
count, which includes activity after the historical prediction point.

Do not load the checkpoint files, interpret their metrics as forecast quality,
or display their scores in Streamlit. No valid 7-day activity-drop model was
produced from this snapshot. The training script was removed to prevent
accidental reruns; each folder keeps its audit metrics and warning file.
