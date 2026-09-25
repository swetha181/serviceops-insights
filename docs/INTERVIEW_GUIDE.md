# Understand and demonstrate the project

## A 60-second explanation

“ServiceOps Insights is a small portfolio prototype for reviewing IT service requests. It validates a CSV extract, calculates elapsed time against priority-based SLA targets, and uses SQL to aggregate backlog and resolution metrics. A local dashboard lets a reviewer filter by department and priority. I also prepared Power Query and DAX definitions for Power BI and a Power Automate workflow design for reviewing escalation alerts. The dataset is synthetic. The Python implementation is tested; the Microsoft integrations require setup and validation in my account.”

Use this wording only after you have run the demo and understand it. Once you build the Microsoft pieces, replace the final sentence with the specific steps you completed, supported by your screenshots and run history.

## Three-minute walkthrough

1. Open `examples/dashboard.html`. Explain the 240 accepted requests and the fixed reporting snapshot.
2. Point to 72 open requests and 42 overdue requests. Explain why overdue resolved tickets are excluded from open escalation alerts.
3. Select Finance. The numbers become 54 total, 18 open and 8 overdue. This shows how a business owner can narrow the work.
4. Reset, then search `INC-0001`. Clear it. Demonstrate a no-match search and explain that an empty compliance denominator is displayed as a dash.
5. Open `examples/rejected_rows.csv`: one duplicate ID, one invalid priority and one bad timestamp.
6. Open `examples/alerts.json` and point to the snapshot ID, 50 alerts and typed fields. Explain how Power Automate would parse and filter it.
7. Run `python3 -m unittest discover -s tests -v`. Show the deadline boundary tests.

## Questions you should be able to answer

**Why did you choose this project for an ICT internship?**

It connects software development to a business decision: identifying service requests that need attention. It brings together data quality, business intelligence and process automation, which are central to the advertised role.

**Where is SQL used?**

The Python pipeline loads accepted records into an in-memory SQLite table using parameterised inserts. The SQL queries in `sql/queries.json` calculate overall metrics, department totals and daily request volumes. SQLite keeps the demo easy to run; this is not a deployed PostgreSQL service.

**What is the difference between Power Query and DAX here?**

Power Query reads the CSV and converts column types during refresh. DAX defines measures that recalculate under the report's filters. The supplied M query normalises UTC timestamps and preserves null resolution times. DAX compliance uses `DIVIDE` so an empty denominator stays blank.

**Why not divide SLA successes by every request?**

Some open requests have not reached their deadline. Counting all open requests in resolved compliance would mix different populations. This project separates completed compliance from open backlog risk.

**What happens exactly at the deadline?**

A request resolved exactly at its target is Met. An open request exactly at its deadline is At risk; one second later it becomes Overdue. Classification happens before rounding. Tests lock down these boundaries.

**What does the Power Automate component actually do today?**

The repository contains a JSON payload, schema and step-by-step flow specification. The local pipeline generates the payload but does not run a cloud flow or send mail. In the Microsoft designer, the planned flow parses the JSON, filters actionable states, checks whether rows remain, creates a table and optionally sends a test digest. State clearly whether you have completed this setup.

**How would you avoid duplicate notifications?**

The payload has a stable ID derived from the data and snapshot timestamp. A production consumer would store successfully processed IDs and check before sending. This prototype does not implement that persistent store. Even with it, failures between sending and recording success require an idempotency/retry strategy.

**Where is AI used?**

The SLA rules do not use AI. AI assistance helped prepare the project, but the running program performs deterministic calculations. For AI experience, discuss the Claude API validation and asset-tagging work already on your résumé. An LLM could later draft summaries of aggregate metrics, with review and data minimisation.

**What would you improve next?**

Add a real service-desk connector, model first-response and resolution targets separately, account for business hours and holidays, keep request status history, and deploy/test the Microsoft workflow. Measure an actual before/after reporting process before claiming efficiency savings.

## Your strongest existing example: Rently Power BI dashboard

Prepare a separate explanation of the professional dashboard you described: pass/fail status, test reports, workflow screenshots, covered and uncovered use cases, affected modules, and nine repositories. Explain what you personally built and how a reviewer used it.

Before interviewing, recall the real details: the source of test data, refresh method, model/relationships, any DAX you wrote, screenshot linking method, and who used the report. These details were not supplied and should not be invented.

## Why this internship after professional experience?

Suggested answer, if it reflects your motivation:

“I'm completing a Master of Information Technology at Flinders and looking for practical experience in an Australian enterprise ICT environment. My background means I can contribute to automation, reporting and software delivery, while the internship gives me a structured opportunity to broaden my Power Platform skills and learn from the team. I can relocate to Sydney and commit to three days per week for the full 12 months.”

## Make one change yourself before publishing

Change an SLA target in `SLA_HOURS`, update the matching test expectations and explanatory text, regenerate the outputs, and describe how the alert counts change. Alternatively add a category filter to the dashboard. A small change you can explain is more useful interview preparation than memorising the README.
