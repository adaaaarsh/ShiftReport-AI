# Scenario review log

Before any reports were generated, the first author reviewed every scenario and answer key in `scenarios.pre-review.json` against the equipment registry (2026-11-05). Nineteen scenarios were accepted unchanged and eleven were edited. For S05, M01, M06 (issue 4) and V06 the reviewer confirmed that HIGH should be accepted; it already was, and the lower levels were kept as acceptable too. The edited keys are in `scenarios.json`.

## Edits applied
- S04 M-16: missing += 'repair ETA from vendor/mechanic (how long forklift 1 covers alone)'
- S05 M-12: missing += 'were parts in cycle scrapped or damaged when air was lost'
- S06 M-09: missing += 'cause of calibration drift (fixture bumped or dirty?)'
- M01 M-04: missing += 'is the slower cycle time backing up the line'
- M03 M-01: missing += 'spindle damage / tool wear check'
- M03 M-08: missing += 'output lost running at half speed'
- V04 AMBIGUOUS:M-12,M-13,M-14: missing += 'check generator ATS / run log to confirm whether M-13 started'
- V05 AMBIGUOUS:M-01,M-02,M-07: missing += 'quarantine status of parts run while out of spec'
- V06 M-10: missing += 'were the blower motor and exhaust checked'
- C03 M-15: severity ['HIGH', 'MEDIUM', 'UNKNOWN'] -> ['CRITICAL', 'HIGH']
- C03 M-15: missing 'who authorized use' -> 'who authorized operating a tagged-out forklift'
- E01 M-03: severity ['HIGH', 'MEDIUM', 'CRITICAL'] -> ['CRITICAL']
- E01 M-03: missing += 'safety non-compliance: lockout/tagout skipped to meet quota'
- E04 M-10: severity ['CRITICAL', 'HIGH'] -> ['CRITICAL']
