# Build the Power BI report

This folder supplies Power Query M, DAX definitions and a report theme. It is not a PBIX/PBIT export. The queries have been reviewed against Microsoft's documentation, but have not been executed in Power BI Desktop in this environment. Complete the checks below before describing this new report as deployed.

## 1. Load the data

Power BI Desktop requires Windows. On a Mac, use the local HTML demo immediately; use an available Windows PC or an existing Windows environment for the Power BI steps. No purchase is needed to run the Python project.

1. Run `python3 -m serviceops.pipeline` from the repository root (on Windows, use `py -m serviceops.pipeline`).
2. Open Power BI Desktop and create a blank report.
3. Choose **Transform data > New source > Blank query**. Rename the query **Tickets**.
4. Open **Advanced Editor**, replace its contents with `Tickets.m`, and change `CsvPath` to the full Windows path of `build/tickets_clean.csv`.
5. Confirm the query preview shows 240 rows and no column errors. **Close & Apply**.
6. In **Modeling > New measure**, add each definition in `Measures.dax` separately. Do not paste the whole file as one measure.
7. Format `SLA Compliance` as Percentage with one decimal place, `Average Resolution Hours` as a decimal with two places, and `Snapshot UTC` as date/time. Use whole numbers for count measures.

## 2. Arrange a single report page

Use a 16:9 page, a clear title and a note saying **Synthetic demo / snapshot in UTC**. Import `Theme.json` through the theme menu if desired.

| Visual | Fields / settings |
| --- | --- |
| Five cards across the top | Total Requests; Open Backlog; Overdue Requests; SLA Compliance; Average Resolution Hours |
| Department slicer | `Tickets[department]` |
| Priority slicer | `Tickets[priority]` |
| Bar chart: demand by department | Department on category axis; Total Requests as value |
| Bar chart: backlog health | SLA state on category axis; Open Backlog as value; visual filter `is_open = 1` |
| Line chart: requests created | `created_on` on continuous date axis; Total Requests as value; use the date field rather than an automatic hierarchy |
| Detail table | Ticket ID, department, category, priority, SLA state, elapsed hours, SLA hours |
| Detail table filters | `is_open = 1`; SLA state is Overdue or At risk |
| Snapshot card | Snapshot UTC |

The line chart counts requests by creation date; it is **not** historical backlog. Reconstructing historical backlog would need event history or a snapshot fact table. Filters on department/priority should change all cards and visuals. The detail table's filters should be visual-level only.

## 3. Verify and save

With no slicers selected, compare against `build/summary.json`:

| Metric | Expected |
| --- | ---: |
| Total requests | 240 |
| Open backlog | 72 |
| Resolved requests | 168 |
| Overdue | 42 |
| At risk | 8 |
| Resolved within SLA | 88 |
| SLA compliance | 52.4% |
| Average resolution time | 32.99 hours |

Select Finance: verify 54 total, 18 open, and 8 overdue. Clear the slicer. Check that open tickets have blank resolution hours, not zero. Save as `ServiceOps_Insights.pbix` locally. Capture your actual report as `docs/powerbi-report.png` for the repository. A screenshot of the HTML dashboard must not be labelled as a Power BI screenshot.

Refreshing the Power BI report reads the last CSV output. It does not run the Python pipeline. To update the snapshot, rerun Python with the appropriate `--as-of`, then refresh. This mini-project does not configure Power BI Service refresh, gateway connections or workspace publishing.

## References

- [Microsoft: Power BI Desktop requirements](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop)
- [Microsoft: Csv.Document](https://learn.microsoft.com/en-us/powerquery-m/csv-document)
- [Microsoft: Table.TransformColumnTypes](https://learn.microsoft.com/en-us/powerquery-m/table-transformcolumntypes)
- [Microsoft: CALCULATE and filter context](https://learn.microsoft.com/en-us/dax/calculate-function-dax)
- [Microsoft: DIVIDE and empty denominators](https://learn.microsoft.com/en-us/dax/divide-function-dax)
