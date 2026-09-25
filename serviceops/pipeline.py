"""Validate service requests, calculate SLA metrics, and prepare BI/flow outputs."""

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AS_OF = "2026-09-14T00:00:00Z"
SLA_HOURS = {"Critical": 4, "High": 8, "Medium": 24, "Low": 72}
OPEN_STATUSES = {"Open", "In Progress"}
INPUT_FIELDS = ["ticket_id", "department", "category", "priority", "status", "created_at", "resolved_at"]
CLEAN_FIELDS = INPUT_FIELDS + ["created_on", "sla_hours", "elapsed_hours", "resolution_hours", "sla_state", "is_open", "snapshot_at"]
REJECT_FIELDS = ["source_row", "ticket_id", "reason"]


def parse_time(value):
    """Require a timezone so the result is independent of the machine's timezone."""
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return result.astimezone(timezone.utc)


def iso(value):
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def validate_rows(rows, as_of):
    clean, rejected, seen = [], [], set()
    for number, raw in enumerate(rows, start=2):
        row = {field: str(raw.get(field) or "").strip() for field in INPUT_FIELDS}
        try:
            if None in raw:
                raise ValueError("unexpected extra CSV columns")
            if not re.fullmatch(r"INC-\d{4,}", row["ticket_id"]):
                raise ValueError("ticket_id must match INC- followed by at least four digits")
            if row["ticket_id"] in seen:
                raise ValueError("duplicate ticket_id; first valid row retained")
            if not row["department"] or not row["category"]:
                raise ValueError("department and category are required")
            if row["priority"] not in SLA_HOURS:
                raise ValueError("priority must be Critical, High, Medium or Low")
            if row["status"] not in OPEN_STATUSES | {"Resolved"}:
                raise ValueError("status must be Open, In Progress or Resolved")
            created = parse_time(row["created_at"])
            resolved = parse_time(row["resolved_at"]) if row["resolved_at"] else None
            if created > as_of:
                raise ValueError("created_at is after snapshot")
            if row["status"] == "Resolved" and resolved is None:
                raise ValueError("Resolved tickets require resolved_at")
            if row["status"] in OPEN_STATUSES and resolved is not None:
                raise ValueError("open tickets cannot have resolved_at")
            if resolved is not None and not created <= resolved <= as_of:
                raise ValueError("resolved_at must be between creation and snapshot")
            is_open = row["status"] in OPEN_STATUSES
            elapsed = ((as_of if is_open else resolved) - created).total_seconds() / 3600
            target = SLA_HOURS[row["priority"]]
            if is_open:
                state = "Overdue" if elapsed > target else "At risk" if elapsed >= .8 * target else "On track"
            else:
                state = "Met" if elapsed <= target else "Breached"
            # Classify before rounding, so a deadline crossed by one second is overdue.
            row.update(created_at=iso(created), resolved_at=iso(resolved) if resolved else "",
                       created_on=created.date().isoformat(), sla_hours=target,
                       elapsed_hours=round(elapsed, 4),
                       resolution_hours="" if is_open else round(elapsed, 4),
                       sla_state=state, is_open=int(is_open), snapshot_at=iso(as_of))
            clean.append(row)
            seen.add(row["ticket_id"])
        except (ValueError, TypeError) as exc:
            rejected.append({"source_row": number, "ticket_id": row["ticket_id"], "reason": str(exc)})
    return clean, rejected


def aggregate(rows):
    """Use a real SQL reporting layer, with parameterised inserts."""
    with closing(sqlite3.connect(":memory:")) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE tickets (ticket_id TEXT PRIMARY KEY, department TEXT, category TEXT, priority TEXT, status TEXT, created_on TEXT, sla_state TEXT, is_open INTEGER, resolution_hours REAL)")
        conn.executemany("INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         [(r["ticket_id"], r["department"], r["category"], r["priority"], r["status"], r["created_on"], r["sla_state"], r["is_open"], r["resolution_hours"] if r["resolution_hours"] != "" else None) for r in rows])
        queries = json.loads((ROOT / "sql" / "queries.json").read_text(encoding="utf-8"))
        metrics = dict(conn.execute(queries["metrics"]).fetchone())
        metrics["sla_met_pct"] = round(100 * metrics["met"] / metrics["resolved"], 1) if metrics["resolved"] else None
        metrics["avg_resolution_hours"] = round(metrics["avg_resolution_hours"], 2) if metrics["avg_resolution_hours"] is not None else None
        return {"metrics": metrics,
                "by_department": [dict(r) for r in conn.execute(queries["by_department"])],
                "by_day": [dict(r) for r in conn.execute(queries["by_day"])]}


def build_payload(rows, as_of):
    """A stable snapshot ID supports duplicate detection in downstream consumers."""
    canonical = json.dumps(sorted(rows, key=lambda r: r["ticket_id"]), sort_keys=True, separators=(",", ":"))
    snapshot_id = hashlib.sha256((iso(as_of) + canonical).encode()).hexdigest()[:20]
    alerts = [{"ticket_id": r["ticket_id"], "department": r["department"], "priority": r["priority"],
               "sla_state": r["sla_state"], "elapsed_hours": r["elapsed_hours"], "sla_hours": r["sla_hours"],
               "suggested_action": "Assign an owner and review the next action; do not auto-close the request."}
              for r in rows if r["is_open"] and r["sla_state"] in {"Overdue", "At risk"}]
    alerts.sort(key=lambda r: (r["sla_state"] != "Overdue", SLA_HOURS[r["priority"]], -r["elapsed_hours"]))
    return {"schema_version": "1.0", "snapshot_id": snapshot_id, "snapshot_at": iso(as_of),
            "dataset": "synthetic-demo", "alert_count": len(alerts), "alerts": alerts}


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        # Treat exported strings as data if someone opens the file in a spreadsheet.
        writer.writerows({k: "'" + v if isinstance(v, str) and v[:1] in ("=", "+", "-", "@") else v
                          for k, v in row.items()} for row in rows)


def run(input_path, output_dir, as_of_text=DEFAULT_AS_OF):
    as_of = parse_time(as_of_text)
    with Path(input_path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or set(reader.fieldnames) != set(INPUT_FIELDS) or len(reader.fieldnames) != len(INPUT_FIELDS):
            raise ValueError("CSV header must contain exactly: " + ", ".join(INPUT_FIELDS))
        rows, rejected = validate_rows(reader, as_of)
    summary = aggregate(rows)
    summary.update(snapshot_at=iso(as_of), dataset="synthetic-demo", accepted_rows=len(rows), rejected_rows=len(rejected))
    payload = build_payload(rows, as_of)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "tickets_clean.csv", CLEAN_FIELDS, rows)
    write_csv(output / "rejected_rows.csv", REJECT_FIELDS, rejected)
    for name, data in [("summary.json", summary), ("alerts.json", payload)]:
        (output / name).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    dashboard_data = json.dumps({"summary": summary, "tickets": rows}, allow_nan=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    template = (ROOT / "serviceops" / "dashboard.html").read_text(encoding="utf-8")
    (output / "dashboard.html").write_text(template.replace("__REPORT_DATA__", dashboard_data), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "tickets_demo.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "build")
    parser.add_argument("--as-of", default=DEFAULT_AS_OF, help="Timezone-aware reporting snapshot, e.g. 2026-09-14T00:00:00Z")
    args = parser.parse_args()
    try:
        summary = run(args.input, args.output, args.as_of)
    except (ValueError, OSError, csv.Error) as exc:
        parser.exit(2, f"Pipeline failed: {exc}\n")
    print(json.dumps(summary, indent=2))
    print(f"Report ready: {args.output / 'dashboard.html'}")


if __name__ == "__main__":
    main()
