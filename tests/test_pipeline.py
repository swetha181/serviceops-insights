import csv
import json
import tempfile
import unittest
from pathlib import Path
from serviceops.pipeline import (ROOT, DEFAULT_AS_OF, INPUT_FIELDS, parse_time,
                                 validate_rows, aggregate, build_payload, run)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.now = parse_time(DEFAULT_AS_OF)
        self.base = dict(ticket_id="INC-0001", department="ICT", category="Access",
                         priority="Critical", status="Open", created_at="2026-09-13T20:00:00Z", resolved_at="")

    def row(self, **changes):
        valid, invalid = validate_rows([dict(self.base, **changes)], self.now)
        self.assertFalse(invalid)
        return valid[0]

    def test_deadline_exactly_is_at_risk(self):
        self.assertEqual(self.row()["sla_state"], "At risk")

    def test_one_second_after_deadline_is_overdue(self):
        self.assertEqual(self.row(created_at="2026-09-13T19:59:59Z")["sla_state"], "Overdue")

    def test_eighty_percent_threshold(self):
        self.assertEqual(self.row(created_at="2026-09-13T20:48:00Z")["sla_state"], "At risk")
        self.assertEqual(self.row(created_at="2026-09-13T20:48:01Z")["sla_state"], "On track")

    def test_resolved_at_deadline_met(self):
        row = self.row(status="Resolved", resolved_at=DEFAULT_AS_OF)
        self.assertEqual(row["sla_state"], "Met")
        self.assertEqual(row["resolution_hours"], 4)

    def test_resolved_after_target_is_not_open_alert(self):
        row = self.row(status="Resolved", created_at="2026-09-13T19:00:00Z", resolved_at=DEFAULT_AS_OF)
        self.assertEqual(row["sla_state"], "Breached")
        self.assertEqual(build_payload([row], self.now)["alert_count"], 0)

    def test_duplicate_first_valid_wins(self):
        good, bad = validate_rows([self.base, self.base], self.now)
        self.assertEqual((len(good), len(bad)), (1, 1))

    def test_invalid_rows_are_quarantined(self):
        for changes in [{"created_at": "bad"}, {"priority": "Urgent"}, {"status": "Closed"},
                        {"created_at": "2026-09-15T00:00:00Z"}, {"department": ""},
                        {"resolved_at": DEFAULT_AS_OF}, {"status": "Resolved"},
                        {"status": "Resolved", "resolved_at": "2026-09-12T00:00:00Z"},
                        {"status": "Resolved", "resolved_at": "2026-09-15T00:00:00Z"}]:
            with self.subTest(changes=changes):
                good, bad = validate_rows([dict(self.base, **changes)], self.now)
                self.assertEqual((len(good), len(bad)), (0, 1))

    def test_timezones_normalised_and_naive_rejected(self):
        self.assertEqual(parse_time("2026-09-14T09:30:00+09:30"), self.now)
        with self.assertRaises(ValueError):
            parse_time("2026-09-14T00:00:00")

    def test_sql_denominator_only_resolved(self):
        rows = [self.row(), self.row(ticket_id="INC-0002", status="Resolved", resolved_at=DEFAULT_AS_OF),
                self.row(ticket_id="INC-0003", status="Resolved", created_at="2026-09-13T19:00:00Z", resolved_at=DEFAULT_AS_OF)]
        result = aggregate(rows)["metrics"]
        self.assertEqual(result["sla_met_pct"], 50)
        self.assertEqual(result["avg_resolution_hours"], 4.5)
        self.assertEqual(result["open"], 1)

    def test_empty_dataset_has_no_misleading_rate(self):
        result = aggregate([])["metrics"]
        self.assertEqual(result["total"], 0)
        self.assertIsNone(result["sla_met_pct"])
        self.assertIsNone(result["avg_resolution_hours"])

    def test_alerts_only_actionable_open_tickets(self):
        rows = [self.row(), self.row(ticket_id="INC-0002", created_at="2026-09-13T23:00:00Z")]
        result = build_payload(rows, self.now)
        self.assertEqual(result["alert_count"], 1)
        self.assertEqual(result["alerts"][0]["ticket_id"], "INC-0001")

    def test_snapshot_id_is_order_independent(self):
        rows = [self.row(), self.row(ticket_id="INC-0002")]
        self.assertEqual(build_payload(rows, self.now)["snapshot_id"], build_payload(rows[::-1], self.now)["snapshot_id"])
        self.assertNotEqual(build_payload(rows, self.now)["snapshot_id"], build_payload(rows[:1], self.now)["snapshot_id"])

    def test_end_to_end_and_repeatable_output(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run(ROOT / "data" / "tickets_demo.csv", temp)
            self.assertEqual((result["accepted_rows"], result["rejected_rows"]), (240, 3))
            first = {p.name: p.read_bytes() for p in Path(temp).iterdir()}
            run(ROOT / "data" / "tickets_demo.csv", temp)
            self.assertEqual(first, {p.name: p.read_bytes() for p in Path(temp).iterdir()})
            payload = json.loads((Path(temp) / "alerts.json").read_text())
            self.assertEqual(payload["alert_count"], result["metrics"]["overdue"] + result["metrics"]["at_risk"])
            self.assertNotIn("__REPORT_DATA__", (Path(temp) / "dashboard.html").read_text())

    def test_missing_header_fails_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "input.csv"
            source.write_text("ticket_id\nINC-0001\n")
            with self.assertRaises(ValueError):
                run(source, Path(temp) / "result")
            self.assertFalse((Path(temp) / "result").exists())

    def test_html_data_is_escaped(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "input.csv"
            with source.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=INPUT_FIELDS)
                writer.writeheader()
                writer.writerow(dict(self.base, category="</script><script>alert(1)</script>"))
            run(source, Path(temp) / "report")
            html = (Path(temp) / "report" / "dashboard.html").read_text()
            self.assertNotIn("</script><script>alert(1)</script>", html)


if __name__ == "__main__":
    unittest.main()
