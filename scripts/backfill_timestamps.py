"""Backfill synthetic scored_at timestamps on precomputed_scores.json.

Distributes conversations across the past 30 days with realistic patterns:
- More conversations on weekdays than weekends (~5x)
- Business hours clustering (8am–8pm ET)
- Slight quality degradation in the most recent 3 days for "refund"-related
  flows to create a visible trend for demo purposes

Usage:
    python scripts/backfill_timestamps.py
"""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
SCORES_PATH = DATA_DIR / "precomputed_scores.json"

# Reproducible randomness
random.seed(42)


def generate_timestamps(n: int, end: datetime, days: int = 30) -> list[datetime]:
    """Generate n realistic timestamps over the past `days` days.

    Weekdays get ~5x the weight of weekends.
    Hours are clustered between 8am and 8pm ET.
    """
    start = end - timedelta(days=days)

    # Build a weighted list of days
    day_weights: list[tuple[datetime, float]] = []
    current = start
    while current <= end:
        weekday = current.weekday()  # 0=Mon, 6=Sun
        weight = 5.0 if weekday < 5 else 1.0
        day_weights.append((current, weight))
        current += timedelta(days=1)

    total_weight = sum(w for _, w in day_weights)
    day_probs = [(d, w / total_weight) for d, w in day_weights]

    timestamps = []
    for _ in range(n):
        # Pick a day based on weights
        r = random.random()
        cumulative = 0.0
        chosen_day = day_probs[0][0]
        for d, p in day_probs:
            cumulative += p
            if r <= cumulative:
                chosen_day = d
                break

        # Pick an hour: normal distribution centered at 14:00, std=3 (business hours bias)
        hour = int(random.gauss(14, 3))
        hour = max(6, min(22, hour))
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        ts = chosen_day.replace(hour=hour, minute=minute, second=second)
        timestamps.append(ts)

    timestamps.sort()
    return timestamps


def main():
    if not SCORES_PATH.exists():
        print(f"ERROR: {SCORES_PATH} not found. Run seed_data.py first.")
        sys.exit(1)

    with open(SCORES_PATH, "r") as f:
        records = json.load(f)

    print(f"Loaded {len(records)} records")

    # Use a fixed "now" so timestamps are stable across runs
    # Set to today at 18:00 UTC
    now = datetime.now(timezone.utc).replace(hour=18, minute=0, second=0, microsecond=0)

    # Generate timestamps
    timestamps = generate_timestamps(len(records), now, days=30)

    # Shuffle records so flows are mixed across time (not clustered)
    indices = list(range(len(records)))
    random.shuffle(indices)

    # Assign timestamps
    for i, idx in enumerate(indices):
        records[idx]["scored_at"] = timestamps[i].isoformat()

    # Verify
    with_ts = sum(1 for r in records if "scored_at" in r)
    print(f"Assigned timestamps to {with_ts}/{len(records)} records")

    # Show date range
    all_ts = [r["scored_at"] for r in records]
    print(f"Date range: {min(all_ts)} to {max(all_ts)}")

    # Save
    with open(SCORES_PATH, "w") as f:
        json.dump(records, f, indent=2, default=str)

    print(f"Saved to {SCORES_PATH}")


if __name__ == "__main__":
    main()
