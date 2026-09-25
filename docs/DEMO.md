# Two-minute ServiceOps walkthrough

1. Run `python3 -m serviceops.pipeline`.
2. Open `build/dashboard.html`: 240 valid requests and 3 rejected source rows.
3. Filter to ICT: 46 total requests, 15 open and 9 overdue. Reset the filters.
4. Explain that SLA compliance uses resolved requests only, and open tickets generate separate escalation records.
5. Show `build/rejected_rows.csv` and `build/alerts.json`.
6. Explain that Power BI/Power Automate files are setup assets, not verified cloud integrations.

All records are synthetic; no messages are sent.
