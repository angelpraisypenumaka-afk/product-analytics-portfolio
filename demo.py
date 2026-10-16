"""Run all three local projects and write reproducible portfolio evidence."""
import argparse
from pathlib import Path

from ai_review.check import check
from analytics.export import export
from analytics.report import report
from pipeline.generate import generate
from pipeline.run import run


def demo(root=Path("data/demo"), figures=False):
    root = Path(root)
    source = generate(root)
    database = root / "data/analytics.db"
    output = root / "exports"
    first = run(source, database)
    replay = run(source, database)
    if replay["counts"]["inserted_events"] != 0:
        raise RuntimeError("Replay verification failed.")
    export(database, output)
    review = check(database, output)
    result = report(database, output, review)
    if figures:
        from analytics.plot import plot
        plot(output)
    print(f"Demo complete. Results: {result}")
    return {"first_load": first, "replay": replay, "report": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("data/demo"))
    parser.add_argument("--figures", action="store_true",
                        help="Requires the optional matplotlib dependency.")
    args = parser.parse_args()
    demo(args.output_dir, args.figures)
