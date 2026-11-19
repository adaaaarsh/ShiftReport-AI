# Scoring rubric (human raters and LLM judge use the same anchors)

Score each report against the **supervisor input** shown with it. You do not know which prompt version produced the report — do not guess. Score every dimension 1–5 using the anchors; use 2 or 4 when the report falls between anchors.

## 1. Accuracy — is everything in the report true to the input?
- **5** Every machine ID, time, action and status matches the input. Nothing invented.
- **3** Mostly correct, but one wrong machine match OR one invented detail (e.g., a shift letter, time, or action not in the input).
- **1** Several wrong machine matches or invented details; an incoming shift would be misled.

## 2. Completeness — does it carry every reported item forward?
- **5** Every issue, action and pending item in the input appears in the report.
- **3** One reported item is missing or merged away.
- **1** Multiple items missing.

## 3. Severity classification — are severities defensible from the input?
- **5** Every severity is reasonable given only the input; insufficient evidence is marked Unknown rather than guessed.
- **3** One severity clearly too high or too low, or confidently assigned with no supporting evidence.
- **1** Severities missing or mostly indefensible.

## 4. Readability — could an incoming supervisor act on it in under a minute?
- **5** Clear structure, scannable, consistent format, no clutter.
- **3** Usable but inconsistent or padded.
- **1** Hard to follow or unstructured.

## 5. Uncertainty handling — does it surface what is unknown?
- **5** Explicitly flags missing critical information, ambiguous machine references, unrecognized equipment and contradictions in the input.
- **3** Flags some gaps but silently fills or ignores others.
- **1** Presents incomplete, ambiguous or contradictory input as if it were complete and consistent.

Also record (yes/no): **Any fabricated detail?** and, if yes, write what it was in the comment column.
