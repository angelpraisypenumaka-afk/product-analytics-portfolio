"""Render static PNG evidence from exported synthetic analytics CSVs."""
import csv
from datetime import datetime
from pathlib import Path


def read_rows(directory, name):
    with (directory / f"{name}.csv").open(newline="") as handle:
        return list(csv.DictReader(handle))


def plot(directory=Path("exports")):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.ticker import PercentFormatter
        from matplotlib.dates import DateFormatter
    except ImportError as exc:
        raise RuntimeError("Install optional figures: python -m pip install -r requirements-viz.txt") from exc
    directory = Path(directory)
    dau = read_rows(directory, "daily_active_users")
    activation = read_rows(directory, "activation")
    funnel = read_rows(directory, "funnel")[0]
    retention = read_rows(directory, "cohort_retention")
    if not dau or not activation or not retention:
        raise ValueError("The synthetic demo must contain nonempty metrics before plotting.")
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.labelcolor": "#334155", "text.color": "#0f172a",
        "xtick.color": "#475569", "ytick.color": "#475569",
        "axes.edgecolor": "#cbd5e1", "figure.facecolor": "#ffffff",
    })
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), layout="constrained")
    fig.suptitle("Product Analytics | Synthetic Data", fontsize=19, fontweight="bold")
    ax = axes[0, 0]
    ax.plot([datetime.fromisoformat(row["activity_date"]) for row in dau],
            [int(row["daily_active_users"]) for row in dau], color="#0f766e", linewidth=2)
    ax.set(title="Daily active users", ylabel="Distinct active users")
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_formatter(DateFormatter("%b %d"))
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", alpha=0.18)
    ax = axes[0, 1]
    ax.plot([datetime.fromisoformat(row["signup_date"]) for row in activation],
            [float(row["activation_rate"]) for row in activation],
            color="#0f766e", marker="o", linewidth=2)
    ax.set(title="Activation within 24 hours", ylabel="Eligible signup cohort activation", ylim=(0, 1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.xaxis.set_major_formatter(DateFormatter("%b %d"))
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", alpha=0.18)
    ax = axes[1, 0]
    values = [int(funnel[key]) for key in ("sessions_viewed", "sessions_carted", "sessions_purchased")]
    bars = ax.barh(["Viewed", "Added to cart", "Purchased"], values,
                   color=["#0f766e", "#2c938b", "#72b9b1"])
    ax.invert_yaxis()
    ax.bar_label(bars, padding=5, fmt="%d")
    ax.set(title="Ordered session conversion funnel", xlabel="Qualifying sessions")
    ax.set_xlim(0, max(values) * 1.2)
    ax.grid(axis="x", alpha=0.18)
    ax = axes[1, 1]
    cohorts = sorted({row["cohort_date"] for row in retention})
    offsets = [1, 7, 14]
    lookup = {(row["cohort_date"], int(row["day_offset"])): float(row["retention_rate"])
              for row in retention}
    matrix = [[lookup.get((cohort, offset), float("nan")) for offset in offsets]
              for cohort in cohorts]
    ax.imshow(matrix, cmap="GnBu", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(3), [f"D{offset}" for offset in offsets])
    ax.set_yticks(range(len(cohorts)), [date[5:] for date in cohorts])
    ax.set(title="Exact-day cohort retention", ylabel="Signup cohort (UTC)")
    for y, row in enumerate(matrix):
        for x, value in enumerate(row):
            if value == value:
                ax.text(x, y, f"{value:.0%}", ha="center", va="center",
                        color="white" if value > 0.55 else "#0f172a", fontsize=9)
    path = directory / "product_analytics.png"
    fig.savefig(path, dpi=150, facecolor="white")
    plt.close(fig)
    print(f"Static charts: {path}")
    return path


if __name__ == "__main__":
    plot()
