# Current experiment versions

Use v14 sensitivity outputs for current measurement claims. V13 outputs remain historical and are superseded in the following respects:

- Sampling: the earlier field labelled four-hour lag used a one-hour row offset. V14 uses physical 1 h and 4 h lags and complete intervening bins.
- Matching: v14 restores the original greedy tie rule, reproduces all baseline event pairs, and uses zero-reward dummy assignments for the maximum-total-IoU comparator. Site metrics pool labels within configuration pairs before averaging.
- Weather: v14 encodes event occurrence as integer 1 and obtains covariates strictly before the three-hour exposure interval. The complete-case crude and adjusted contrasts use the same records.
- Transfer: v14 compares frozen and adapted copies of the same TCN on the same Greek pair list and reports multiple aggregation units separately.

Two reviewer-author cycles were requested. Round one is complete. The second independent reviewer delivered findings and the controller applied them; the independent second author response is pending a model-capacity recovery. This is a working research release, not a completed submission-readiness audit.
