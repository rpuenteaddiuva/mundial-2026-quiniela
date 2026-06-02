# tests/test_ratings.py
import numpy as np
import pandas as pd
from src.ratings import zscore, unit_strengths_from_players, composite_rating

def test_zscore_mean_zero_std_one():
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    z = zscore(s)
    assert abs(z.mean()) < 1e-9
    assert abs(z.std(ddof=0) - 1.0) < 1e-9

def test_composite_rating_blend_is_weighted_sum_on_elo_scale():
    # Dos equipos: A claramente superior en las tres señales.
    df = pd.DataFrame({
        "team": ["A", "B"],
        "elo": [2000.0, 1600.0],
        "fifa_points": [1800.0, 1400.0],
        "player_overall": [85.0, 75.0],
    })
    weights = {"elo": 0.5, "fifa": 0.2, "players": 0.3}
    R = composite_rating(df, weights)
    assert R["A"] > R["B"]
    # R se reescala a escala Elo: el promedio debe acercarse al promedio de elo.
    assert 1500 < R.mean() < 2100

from src.ratings import add_model_columns

def test_add_model_columns_creates_z_scores():
    df = pd.DataFrame({
        "team": ["A", "B", "C"],
        "R": [2000.0, 1800.0, 1600.0],
        "ATA": [88.0, 80.0, 70.0],
        "DEF": [85.0, 78.0, 72.0],
    })
    out = add_model_columns(df)
    for col in ("R_z", "ATA_z", "DEF_z"):
        assert col in out.columns
        assert abs(out[col].mean()) < 1e-9

def test_unit_strengths_aggregate_top_players_per_line():
    # Equipo A: dos delanteros fuertes; equipo B: dos delanteros flojos.
    players = pd.DataFrame([
        {"team": "A", "line": "FWD", "ritmo": 90, "tiro": 90, "regate": 90, "definicion": 90},
        {"team": "A", "line": "FWD", "ritmo": 88, "tiro": 88, "regate": 88, "definicion": 88},
        {"team": "B", "line": "FWD", "ritmo": 60, "tiro": 60, "regate": 60, "definicion": 60},
        {"team": "B", "line": "FWD", "ritmo": 62, "tiro": 62, "regate": 62, "definicion": 62},
    ])
    units = unit_strengths_from_players(players)
    assert units.loc["A", "ATA"] > units.loc["B", "ATA"]
    assert 0 <= units.loc["A", "ATA"] <= 100
