"""Generate repeatable synthetic inputs, including intentional bad records."""
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

AS_OF = datetime(2026, 1, 31, 23, 59, tzinfo=timezone.utc)
START = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)


def generate(root=Path(".")):
    rng = random.Random(42)
    records = []
    for index in range(120):
        user = f"synthetic_user_{index:04d}"
        signup = START + timedelta(days=index % 10)
        variant = "control" if index % 2 == 0 else "treatment"
        sequence = 0

        def add(name, when, session, properties=None):
            nonlocal sequence
            sequence += 1
            records.append({
                "event_id": f"{user}_{sequence:04d}",
                "user_id": user,
                "session_id": session,
                "event_name": name,
                "event_timestamp": when.isoformat(),
                "schema_version": 1,
                "properties": properties or {},
            })

        first_session = f"{user}_session_00"
        add("signup", signup, first_session)
        add("experiment_assigned", signup, first_session,
            {"experiment_id": "onboarding_v1", "variant": variant})
        for day in range(22):
            when = signup + timedelta(days=day)
            if when > AS_OF:
                continue
            if day != 0 and rng.random() >= max(0.15, 0.75 - day * 0.025):
                continue
            session = f"{user}_session_{day:02d}"
            add("app_open", when + timedelta(minutes=1), session)
            if day == 0:
                add("experiment_exposed", when + timedelta(minutes=2), session,
                    {"experiment_id": "onboarding_v1"})
            if rng.random() < 0.68:
                add("view_item", when + timedelta(minutes=3), session)
                if rng.random() < 0.52:
                    add("add_to_cart", when + timedelta(minutes=4), session)
                    if rng.random() < 0.45:
                        add("purchase", when + timedelta(minutes=5), session)

    rng.shuffle(records)  # Arrival order intentionally differs from event time.
    records.append(dict(records[0]))  # Exact replay.
    invalid = dict(records[0])
    invalid["event_id"] = "invalid_missing_user"
    invalid.pop("user_id")
    records.append(invalid)
    invalid = dict(records[1])
    invalid["event_id"] = "invalid_event_name"
    invalid["event_name"] = "unknown_event"
    records.append(invalid)

    directory = root / "data"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "events.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in records))
    print(f"Generated {len(records)} input records at {path}")
    print(f"Synthetic as-of clock: {AS_OF.isoformat()}")
    return path


if __name__ == "__main__":
    generate()
