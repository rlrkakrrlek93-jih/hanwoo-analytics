# HANWOO INSIGHT: Monthly decimal-precision audit (2026-11-20)

## Reproducible official evidence

- Production source: [DT_323903_E1080008](https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_323903_E1080008&conn_path=I2), nationwide, Hanwoo, sex=steer/cow, weight=all. Captured 2026-08 through 2026-10. **16,796 numeric table cells examined; 0 nonzero decimal-fraction cells.** Example: Oct steer mean BMS `7`, cow BMS `5`. The retrieved table's visible text, HTML cell title and hidden input all contain the integer.
- Alternative official source: [DT_APGS_011](https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_APGS_011&conn_path=I2), carcass-detail analysis. Captured 2026-03 through 2026-08. **755 numeric table cells examined; 0 nonzero decimal-fraction cells.** Its notes specify *reference wholesale market* (`기준도매시장`: from Feb 2011, Nonghyup Eumseong / 농협음성) and exclusion of off-grade carcasses. This is **not** the same nationwide population as the production source.

## Official same-month headcount cross-check

| 2026-08, Hanwoo | Production nationwide source | Alternative detailed source | Same population? |
|---|---:|---:|---|
| Steer (거세우) | 37,553 | 9,088 | No |
| Cow (암소) | 36,914 | 4,372 | No |

The alternative source also lacks Sep–Oct 2026, the most recent two months on the live dashboard. Neither table provides additional decimal precision in its captured cells.

## Decision and guardrail

**Do not overwrite production records.** `7.0` is a presentation format for the source integer `7`; it is not evidence for an exact mean of `7.0`. Do not fabricate decimals from integer-rounded category means or borrow 6.8/5.2 from a differently defined table. The compatibility check blocks even if headcounts match because exact source populations and metric definitions must still be verified. Confirm *all* of: year/month, nationwide coverage, Hanwoo breed, sex, inclusion of off-grade animals, count, denominator/selection, and available decimal digits.

## Next step requiring a new official source

Obtain from KAPE an official export/API of **unrounded monthly nationwide average BMS** (and optionally carcass weight/REA/backfat) for 2026-01 onward, split by steer/cow, together with its definition and headcounts; alternatively obtain a BMS 1–9 score distribution for exactly the same graded population and month. Only after a complete crosswalk and tests can monthly precise means be introduced into the site. Preserve the current official integer display in the meantime.

These checks are read-only and produce GitHub Actions artifacts. They do not change index.html, dashboard_template.html, data.json, data.csv, collect.py or update.py.