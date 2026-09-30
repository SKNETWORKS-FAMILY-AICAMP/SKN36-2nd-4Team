# Do not use this run

Although the retained sequence count matched `actual_history_matches`, that
eligibility condition itself was determined using the entire data window.
Selecting users with at most 30 matches depends on their later activity, so
historical 7-day activity-drop validation is selection-biased. A near-perfect
top-decile baseline result confirms that this score should not be trusted.

The saved checkpoints are audit artifacts, not deployable models. The current
project instead tests next-observed-match behavior, whose labels are drawn
from consecutive recorded events without inferring missing future activity.
