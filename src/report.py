# src/report.py
"""Genera tablas y figuras de salida en outputs/."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def write_champion_table(probs, path):
    """Escribe la tabla de probabilidades de campeón ordenada."""
    probs.sort_values("champion", ascending=False).to_csv(path, index=False)

def plot_top_champions(probs, path, top=15):
    """Gráfico de barras con los `top` favoritos."""
    d = probs.sort_values("champion", ascending=False).head(top)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(d["team"][::-1], d["champion"][::-1])
    ax.set_xlabel("Probabilidad de campeón")
    ax.set_title("Mundial 2026 — Favoritos (modelo Monte Carlo)")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
