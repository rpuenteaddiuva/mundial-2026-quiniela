# src/network.py
"""Grafo de fuerza de selecciones (nodos) y visualización."""
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.teams import GROUPS

def build_strength_graph(ratings):
    """Nodos = selecciones con atributo 'strength'=R; aristas dentro de cada grupo."""
    g = nx.Graph()
    for team, row in ratings.iterrows():
        g.add_node(team, strength=float(row["R"]))
    for members in GROUPS.values():
        present = [t for t in members if t in g]
        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                g.add_edge(present[i], present[j])
    return g

def plot_strength_graph(g, path):
    """Dibuja el grafo con tamaño de nodo proporcional a la fuerza."""
    sizes = [g.nodes[n]["strength"] for n in g]
    smin = min(sizes)
    fig, ax = plt.subplots(figsize=(12, 10))
    pos = nx.spring_layout(g, seed=42)
    nx.draw_networkx(g, pos, ax=ax, node_size=[(s - smin + 50) for s in sizes],
                     font_size=7, node_color="#4C72B0", edge_color="#cccccc")
    ax.set_title("Mundial 2026 — Red de fuerza por grupos")
    ax.axis("off")
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
