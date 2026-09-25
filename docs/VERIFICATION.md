# Verification record

Prepared on 14 September 2026.

## Executed locally

- Python 3.12: all 15 unit/integration tests passed.
- Pipeline run: 243 inputs, 240 accepted, 3 quarantined.
- Repeat-run test: generated files are byte-identical for the same input and snapshot.
- Expected totals: 72 open, 168 resolved, 42 overdue, 8 at risk, 88 resolved within SLA, 52.4% compliance, 32.99 mean resolution hours.
- Browser check: dashboard rendered; Finance filter showed 54 total / 18 open / 8 overdue.
- Browser check: no-match search showed zero counts, undefined-rate dashes and the empty-state message.
- Browser check: reset cleared prior filters; Critical selection showed 17 total / 7 open / 3 overdue.
- Desktop visual review: chart labels, controls, cards and colours inspected at a 1280-pixel browser width.

## Still requires your environment

- Execute Power Query and DAX in Power BI Desktop, reconcile totals and save the report.
- Create the Power Automate cloud flow, configure permitted connections and execute the documented test cases.
- Run GitHub Actions after publishing the repository. The workflow file alone is not evidence of a passing remote run.

No Microsoft cloud deployment, production ingestion, employer-data access, scheduled notification delivery, LLM integration or production performance benchmark is claimed.
