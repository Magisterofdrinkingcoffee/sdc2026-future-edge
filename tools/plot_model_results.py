"""Charts of Model 1's results for the slides, PRD and video.

    pip install -r tools/requirements-train.txt
    python -m tools.plot_model_results

Reads the metrics saved inside src/backend/models/exposure_model.json (run tools.train_exposure first)
and writes PNGs to docs/images/.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.backend.exposure_model import load, predict  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "images"

# Validated categorical palette (colorblind-safe): E0 green, E1 violet, E2 amber
C = {"E0": "#1F9A5E", "E1": "#6C4CF1", "E2": "#E0961A"}
NAMES = {"E0": "AI can't speed it up", "E1": "Chatbot alone can halve the time", "E2": "AI with extra tools can do it"}
INK, MUTED, GRID, SURFACE = "#1F2A44", "#66708A", "#E3E6EF", "#FFFFFF"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11, "text.color": INK, "axes.labelcolor": MUTED,
    "axes.edgecolor": GRID, "xtick.color": MUTED, "ytick.color": INK, "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "axes.spines.top": False, "axes.spines.right": False,
})


def title(fig, main, sub):
    fig.text(0.02, 0.97, main, fontsize=16, fontweight="bold", va="top")
    fig.text(0.02, 0.905, sub, fontsize=10.5, color=MUTED, va="top")


def accuracy_chart(m):
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1, 1.2]})
    fig.subplots_adjust(top=0.74, bottom=0.14, left=0.14, right=0.97, wspace=0.55)
    title(fig, "Model 1 beats a simple guess on jobs it has never seen",
          f"5-fold cross-validation, every test fold holds out whole occupations ({m['n_occupations']} occupations, {m['n_tasks']:,} human-rated tasks)")
    vals = [m["baseline_accuracy"], m["accuracy"]]
    a.barh(["Simple guess\n(always \"E0\")", "Model 1"], vals, color=[GRID, C["E1"]], height=0.55)
    for i, v in enumerate(vals):
        pad = m["accuracy_std"] + 0.02 if i == 1 else 0.01
        a.text(v + pad, i, f"{v:.1%}", va="center", fontweight="bold")
    a.errorbar(m["accuracy"], 1, xerr=m["accuracy_std"], color=INK, capsize=4, lw=1.2)
    a.set_xlim(0, 1); a.set_title("Accuracy", loc="left", fontsize=12, fontweight="bold")
    a.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}"); a.grid(axis="x", color=GRID, lw=0.8); a.set_axisbelow(True)

    rec = m["recall_per_class"]
    labels = [f"{k}  {NAMES[k]}" for k in ["E0", "E1", "E2"]]
    b.barh(labels, [rec[k] for k in ["E0", "E1", "E2"]], color=[C[k] for k in ["E0", "E1", "E2"]], height=0.55)
    for i, k in enumerate(["E0", "E1", "E2"]):
        b.text(rec[k] + 0.01, i, f"{rec[k]:.0%}", va="center", fontweight="bold")
    b.set_xlim(0, 1); b.invert_yaxis()
    b.set_title("Share of each label it gets right (recall)", loc="left", fontsize=12, fontweight="bold")
    b.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}"); b.grid(axis="x", color=GRID, lw=0.8); b.set_axisbelow(True)
    fig.savefig(OUT / "model1_accuracy.png", dpi=200)


def confusion_chart(m):
    labels = m["confusion_matrix"]["labels"]
    cm = m["confusion_matrix"]["rows_true_cols_pred"]
    pct = [[v / sum(row) for v in row] for row in cm]
    fig, ax = plt.subplots(figsize=(7.5, 6))
    fig.subplots_adjust(top=0.8, left=0.3, right=0.97, bottom=0.12)
    title(fig, "Where Model 1 is right and where it confuses labels",
          "Rows = what people said · columns = what the model predicted · % of each row")
    ax.imshow(pct, cmap="Purples", vmin=0, vmax=1)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{pct[i][j]:.0%}\n({cm[i][j]:,})", ha="center", va="center", fontsize=11,
                    color="white" if pct[i][j] > 0.55 else INK, fontweight="bold" if i == j else "normal")
    ticks = [f"{k}\n{NAMES[k]}" for k in labels]
    ax.set_xticks(range(3), [k for k in labels]); ax.set_yticks(range(3), ticks, fontsize=9.5)
    ax.set_xlabel("Model predicted"); ax.set_ylabel("Human label")
    for s in ax.spines.values():
        s.set_visible(False)
    fig.savefig(OUT / "model1_confusion_matrix.png", dpi=200)


EXAMPLES = [
    "Write Python scripts to automate weekly reports",
    "Enter data from shipping documents into the computer system",
    "Prepare charts and dashboards that present sales data to managers",
    "Answer customer questions by telephone and resolve complaints",
    "Design solar photovoltaic systems for residential buildings",
    "Lead a team of technicians during plant shutdowns",
    "Inspect workplaces for safety hazards and investigate accidents",
    "Repair hydraulic machinery on the factory floor",
]


def examples_chart():
    rows = [(t, predict(t)) for t in EXAMPLES]
    fig, ax = plt.subplots(figsize=(13, 6))
    fig.subplots_adjust(top=0.74, left=0.4, right=0.97, bottom=0.07)
    title(fig, "What Model 1 says about real tasks",
          "Probability of each label for one task description (each bar adds to 100%)")
    for i, (t, p) in enumerate(rows):
        left = 0
        for k in ["E0", "E1", "E2"]:
            ax.barh(i, p[k], left=left, color=C[k], height=0.6, edgecolor=SURFACE, linewidth=2)
            if p[k] >= 0.1:
                ax.text(left + p[k] / 2, i, f"{p[k]:.0%}", ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
            left += p[k]
    ax.set_yticks(range(len(rows)), [t for t, _ in rows], fontsize=10)
    ax.invert_yaxis(); ax.set_xlim(0, 1); ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    for s in ("left", "bottom"):
        ax.spines[s].set_visible(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=C[k]) for k in ["E0", "E1", "E2"]]
    fig.legend(handles, [f"{k}: {NAMES[k]}" for k in ["E0", "E1", "E2"]], loc="upper left",
               bbox_to_anchor=(0.015, 0.87), ncol=3, frameon=False, fontsize=10)
    fig.savefig(OUT / "model1_examples.png", dpi=200)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    m = load()["metrics"]
    accuracy_chart(m)
    confusion_chart(m)
    examples_chart()
    for f in sorted(OUT.glob("model1_*.png")):
        print("wrote", f)


if __name__ == "__main__":
    main()
