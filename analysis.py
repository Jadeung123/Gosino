# Reads the CSV files from /stats/ and generates:
# - 1 statistics summary table (printed + saved)
# - 4 graphs as required by the proposal
#
# Run with: python analysis.py

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os

matplotlib.rcParams["figure.facecolor"] = "#1a1a2e"
matplotlib.rcParams["axes.facecolor"]   = "#16213e"
matplotlib.rcParams["axes.labelcolor"]  = "white"
matplotlib.rcParams["xtick.color"]      = "white"
matplotlib.rcParams["ytick.color"]      = "white"
matplotlib.rcParams["text.color"]       = "white"
matplotlib.rcParams["axes.titlecolor"]  = "#FFD700"

STATS_DIR    = "stats"
OUTPUTS_DIR  = "stats/graphs"
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# ── Load all CSVs ─────────────────────────────────────────────────────

def load(name):
    path = os.path.join(STATS_DIR, f"{name}.csv")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        print(f"No data found for {name} — skipping.")
        return None
    return pd.read_csv(path)

gambling    = load("gambling")
detection   = load("detection")
money       = load("money")
shop        = load("shop")
day_summary = load("day_summary")

# ── TABLE: Statistical Values ─────────────────────────────────────────

print("\n" + "="*60)
print("STATISTICAL VALUES TABLE")
print("="*60)

if gambling is not None:
    g = gambling["payout"]
    print(f"\nGambling Payout — Mean: ${g.mean():.0f}  Median: ${g.median():.0f}"
          f"  Std: ${g.std():.0f}  Min: ${g.min()}  Max: ${g.max()}")

if detection is not None:
    d = detection["suspicion_level"]
    print(f"Guard Suspicion  — Mean: {d.mean():.1f}  Median: {d.median():.1f}"
          f"  Std: {d.std():.1f}  Min: {d.min():.1f}  Max: {d.max():.1f}")

if money is not None:
    m = money["player_money"]
    print(f"Player Money     — Mean: ${m.mean():.0f}  Median: ${m.median():.0f}"
          f"  Std: ${m.std():.0f}  Min: ${m.min()}  Max: ${m.max()}")

if shop is not None:
    s = shop["item_cost"]
    print(f"Shop Cost        — Mean: ${s.mean():.0f}  Median: ${s.median():.0f}"
          f"  Std: ${s.std():.0f}  Min: ${s.min()}  Max: ${s.max()}")

if day_summary is not None:
    ds = day_summary["day_number"]
    print(f"Days Survived    — Mean: {ds.mean():.1f}  Median: {ds.median():.1f}"
          f"  Std: {ds.std():.1f}  Min: {ds.min()}  Max: {ds.max()}")

print("="*60)

# ── GRAPH 1: Histogram — Payout Distribution ─────────────────────────

if gambling is not None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(gambling["payout"], bins=20,
            color="#FFD700", edgecolor="#333", alpha=0.85)
    ax.set_title("Graph 1 — Payout Amount Distribution", fontsize=14)
    ax.set_xlabel("Payout Amount ($)")
    ax.set_ylabel("Frequency (number of events)")
    fig.tight_layout()
    path = os.path.join(OUTPUTS_DIR, "graph1_payout_histogram.png")
    fig.savefig(path, dpi=150)
    print(f"\nSaved: {path}")
    plt.close(fig)

# ── GRAPH 2: Scatter Plot — Guard Detection Heatmap ──────────────────

if detection is not None:
    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(
        detection["player_x"], detection["player_y"],
        c=detection["suspicion_level"],
        cmap="hot", alpha=0.7, s=30, edgecolors="none"
    )
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Suspicion Level", color="white")
    cbar.ax.yaxis.set_tick_params(color="white")

    # Flip Y so it matches the game's coordinate system (y=0 at top)
    ax.set_ylim(558, 0)
    ax.set_xlim(0, 800)
    ax.set_title("Graph 2 — Guard Detection Positions (Danger Heatmap)",
                 fontsize=14)
    ax.set_xlabel("Player X Position (pixels)")
    ax.set_ylabel("Player Y Position (pixels)")
    fig.tight_layout()
    path = os.path.join(OUTPUTS_DIR, "graph2_detection_scatter.png")
    fig.savefig(path, dpi=150)
    print(f"Saved: {path}")
    plt.close(fig)

# ── GRAPH 3: Bar Chart — Shop Purchase Frequency ─────────────────────

if shop is not None:
    counts = shop["item_name"].value_counts()
    colors = ["#FF6B6B", "#FFD700", "#4ECDC4",
              "#45B7D1", "#96CEB4", "#FFEAA7"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(counts.index, counts.values,
                  color=colors[:len(counts)], edgecolor="#333", alpha=0.9)

    # Value label on each bar
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.3,
                str(int(bar.get_height())),
                ha="center", va="bottom", fontsize=10)

    ax.set_title("Graph 3 — Shop Item Purchase Frequency", fontsize=14)
    ax.set_xlabel("Item Name")
    ax.set_ylabel("Purchase Count")
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    path = os.path.join(OUTPUTS_DIR, "graph3_shop_bar.png")
    fig.savefig(path, dpi=150)
    print(f"Saved: {path}")
    plt.close(fig)

# ── GRAPH 4: Line Graph — Player Money Over Time ─────────────────────

if money is not None:
    fig, ax = plt.subplots(figsize=(9, 5))

    for day_num, group in money.groupby("day"):
        group = group.reset_index(drop=True)
        ax.plot(group.index * 10,          # x = seconds elapsed
                group["player_money"],
                label=f"Day {day_num}",
                linewidth=1.8, alpha=0.85)

    ax.axhline(0, color="#FF6B6B", linewidth=1,
               linestyle="--", alpha=0.5, label="Bankruptcy")
    ax.set_title("Graph 4 — Player Balance Over Time Per Day", fontsize=14)
    ax.set_xlabel("Time Elapsed (seconds)")
    ax.set_ylabel("Player Money Balance ($)")
    ax.legend(fontsize=9, framealpha=0.3)
    fig.tight_layout()
    path = os.path.join(OUTPUTS_DIR, "graph4_money_line.png")
    fig.savefig(path, dpi=150)
    print(f"Saved: {path}")
    plt.close(fig)

print("\nAll done! Check stats/graphs/ for your output files.")