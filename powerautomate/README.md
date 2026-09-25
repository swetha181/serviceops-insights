# Build and test the Power Automate flow

This is a build guide, JSON schema and machine-readable flow specification. `flow-blueprint.json` is **not an importable Power Automate package**. Connector authentication and execution require your own Microsoft tenant; no cloud flow was deployed and no messages were sent while preparing this project.

## First run: manually triggered demo

You need access to Power Automate and, for the final send step, an allowed Outlook connection. Account/tenant policies determine available connectors. You can validate through the HTML table step without adding an email action.

1. Run the Python pipeline; open `build/alerts.json`.
2. In Power Automate, create an **Instant cloud flow** using **Manually trigger a flow**.
3. Add **Data Operation > Compose**, rename it **Payload**, and paste the full JSON output into Inputs.
4. Add **Parse JSON**, named **Parse_JSON**. For Content choose the Outputs token from Payload. Paste `alerts.schema.json` into Schema.
5. Add **Filter array**, named **Filter_array**. For From use this expression:

   ```text
   body('Parse_JSON')?['alerts']
   ```

   In advanced mode use:

   ```text
   @or(equals(item()?['sla_state'], 'Overdue'), equals(item()?['sla_state'], 'At risk'))
   ```

6. Add **Condition**: expression `length(body('Filter_array'))` **is greater than** `0` (the number zero).
7. In the **Yes** branch, add **Create HTML table**. From = Filter array Body. Choose Custom columns and add these mappings:

   | Header | Expression |
   | --- | --- |
   | Request | `item()?['ticket_id']` |
   | Department | `item()?['department']` |
   | Priority | `item()?['priority']` |
   | SLA state | `item()?['sla_state']` |
   | Elapsed hours | `item()?['elapsed_hours']` |
   | Target hours | `item()?['sla_hours']` |

8. Save and test. The output table should have **50 rows**: 42 overdue and 8 at risk. Capture this run as evidence. This proves parsing and branching without sending email.
9. For the email demo, add **Office 365 Outlook > Send an email (V2)** after the table. Choose your own test inbox. Use subject `[DEMO] ServiceOps SLA review`, with the `snapshot_id` dynamic token appended. In the body, add the snapshot time, the HTML table output token and: `Synthetic data. Review ownership and next action before escalating.` Save and manually test once.
10. In the **No** branch use a Compose action saying `No actionable requests; no email sent`.

Expression names must match the actual action names in your flow. Rename actions before inserting expressions; if the designer changes an internal name, use its dynamic-content picker to reference the right output. The `@` prefix above is for Filter array's advanced condition; ordinary Expression inputs take the function without that prefix.

## Test cases and evidence

| Test | Change | Expected |
| --- | --- | --- |
| Normal | Paste the generated payload | 50 rows; Yes branch |
| Empty | Set `alerts` to `[]` and `alert_count` to `0` | No branch; no email |
| Invalid shape | Replace `alerts` with a string | Parse JSON fails; no downstream send |
| Defensive filtering | Set one alert's state to `Met` | That row is excluded |
| Repeat | Manually run the same payload twice | Same snapshot ID; manual demo can resend |

Save a screenshot of the successful run and no-alert run under `docs/`. Do not upload recipient details, tenant identifiers or connection exports. Update the root README's validation status only after you have actually performed these tests.

## Optional scheduled extension

After the manual flow works, replace the trigger with **Recurrence** and replace the Payload step with **OneDrive for Business > Get file content using path** pointing to your uploaded `alerts.json`. Use its File Content dynamic token as Parse JSON's Content. Some connector outputs expose a binary wrapper; inspect the run output and, if needed, decode its `$content` with `base64ToString` before parsing.

The Python pipeline runs separately: it is not executed by this cloud flow. Regenerate the JSON with the current reporting snapshot and upload/sync it before the scheduled flow runs. This is deliberately a small integration exercise, not a production ingestion service.

Before enabling a schedule:

- Reject a snapshot older than your accepted freshness window; do not schedule the fixed historical sample as if it were current.
- Store each sent `snapshot_id` in a persistent store such as a SharePoint list; check it before sending and record it after a successful send. Limit trigger concurrency to one. This limits duplicates but does not guarantee exactly-once delivery if a send succeeds and writing state fails.
- Use a failure branch to surface parsing or connector errors to the flow owner.
- Decide whether repeated alerts for a still-open ticket are wanted. Snapshot deduplication prevents identical batches; it does not suppress the same ticket in a later snapshot.

## References

- [Microsoft: Power Automate data operations](https://learn.microsoft.com/en-us/power-automate/data-operations)
- [Microsoft: Run a cloud flow on a schedule](https://learn.microsoft.com/en-us/power-automate/run-scheduled-tasks)

The implemented Python rules are deterministic SLA rules, not AI. A future AI summary could help draft explanations, but should not decide urgency or send messages without review.
