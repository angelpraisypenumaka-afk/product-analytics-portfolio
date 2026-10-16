"""Export SQL marts to CSV; no dashboard server required."""
import csv
import sqlite3
from contextlib import closing
from pathlib import Path


def export(db_path=Path("data/analytics.db"), output=Path("exports")):
    if not db_path.exists():
        raise FileNotFoundError("Run python -m pipeline.run first.")
    output.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)) as db:
        for path in sorted(Path(__file__).parent.joinpath("sql").glob("*.sql")):
            cursor = db.execute(path.read_text())
            rows = cursor.fetchall()
            target = output / f"{path.stem}.csv"
            with target.open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow([column[0] for column in cursor.description])
                writer.writerows(rows)
            print(f"{target}: {len(rows)} rows")


if __name__ == "__main__":
    export()
