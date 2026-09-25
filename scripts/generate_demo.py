"""Generate reproducible fictional data; no customer or employer data is used."""
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["ticket_id", "department", "category", "priority", "status", "created_at", "resolved_at"]


def generate():
    rng = random.Random(181)
    snapshot = datetime(2026, 9, 14, tzinfo=timezone.utc)
    rows = []
    for i in range(1, 241):
        priority = rng.choices(["Critical", "High", "Medium", "Low"], weights=[8, 22, 45, 25])[0]
        sla = {"Critical": 4, "High": 8, "Medium": 24, "Low": 72}[priority]
        resolved = rng.random() < .73
        duration = round(sla * rng.uniform(.12, 1.8), 2)
        age = duration + rng.uniform(1, 550) if resolved else sla * rng.uniform(.1, 2.4)
        created = snapshot - timedelta(hours=age)
        closed = created + timedelta(hours=duration) if resolved else None
        rows.append(dict(ticket_id=f"INC-{i:04d}",
                         department=rng.choice(["Finance", "Operations", "Sales", "People & Culture", "ICT"]),
                         category=rng.choice(["Access", "Business application", "Device", "Network", "Reporting"]),
                         priority=priority, status="Resolved" if resolved else rng.choice(["Open", "In Progress"]),
                         created_at=created.isoformat(timespec="seconds").replace("+00:00", "Z"),
                         resolved_at=closed.isoformat(timespec="seconds").replace("+00:00", "Z") if closed else ""))
    rows.extend([dict(rows[0]), dict(rows[1], ticket_id="INC-9001", priority="Urgent"),
                 dict(rows[2], ticket_id="INC-9002", created_at="not-a-date")])
    target = ROOT / "data" / "tickets_demo.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created {len(rows)} synthetic rows: 240 valid and 3 intentional rejects.")


if __name__ == "__main__":
    generate()
