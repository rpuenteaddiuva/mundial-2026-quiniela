# tests/test_network.py
import pandas as pd
from src.network import build_strength_graph

def test_graph_has_node_per_team_with_strength():
    ratings = pd.DataFrame({"team": ["Spain", "France"], "R": [2100.0, 2080.0]}).set_index("team")
    g = build_strength_graph(ratings)
    assert g.number_of_nodes() == 2
    assert g.nodes["Spain"]["strength"] == 2100.0
