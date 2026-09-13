"""
Lightweight exploratory data analysis script (kept as a plain script rather
than a .ipynb so it can be run and reviewed without a Jupyter dependency).

Run:
    python notebooks/eda.py

Outputs class balance and feature-correlation plots to assets/.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.config import ASSETS_DIR, RAW_DATA_PATH, TARGET_COLUMN, URL_ONLY_FEATURES


def main():
    df = pd.read_csv(RAW_DATA_PATH)
    print("Shape:", df.shape)
    print("\nClass balance:\n", df[TARGET_COLUMN].value_counts())
    print("\nMissing values:\n", df.isnull().sum().sum())
    print("\nURL-only feature summary:\n", df[URL_ONLY_FEATURES].describe().T)

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    # Class balance
    fig, ax = plt.subplots(figsize=(4, 4))
    df[TARGET_COLUMN].value_counts().rename({0: "Legitimate", 1: "Phishing"}).plot(
        kind="bar", ax=ax, color=["#22c55e", "#ef4444"]
    )
    ax.set_title("Class Balance")
    ax.set_xlabel("")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(ASSETS_DIR / "class_balance.png", dpi=140)
    plt.close(fig)

    # Correlation heatmap of the 26 URL-only features
    corr = df[URL_ONLY_FEATURES + [TARGET_COLUMN]].corr()
    fig, ax = plt.subplots(figsize=(10, 9))
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=90, fontsize=7)
    ax.set_yticklabels(corr.columns, fontsize=7)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("Feature Correlation Matrix")
    fig.tight_layout()
    fig.savefig(ASSETS_DIR / "correlation_matrix.png", dpi=140)
    plt.close(fig)

    print("\nSaved class_balance.png and correlation_matrix.png to assets/")


if __name__ == "__main__":
    main()
