# src/ratings.py
"""Construye la fuerza compuesta R y las fuerzas de unidad POR/DEF/MED/ATA."""
import numpy as np
import pandas as pd

# Atributos relevantes por línea (claves esperadas en el df de jugadores).
UNIT_ATTRS = {
    "POR": ["reflejos", "manos", "colocacion", "achique"],
    "DEF": ["defensa", "fisico", "aereo", "marca"],
    "MED": ["pase", "regate", "control", "vision"],
    "ATA": ["ritmo", "tiro", "regate", "definicion"],
}
# Qué posiciones aportan a cada línea (columna 'line' del df de jugadores).
LINE_OF_POSITION = {"GK": "POR", "DEF": "DEF", "MID": "MED", "FWD": "ATA"}


def zscore(series):
    """Normaliza una serie a media 0, desviación 1 (poblacional)."""
    mu = series.mean()
    sd = series.std(ddof=0)
    if sd == 0:
        return series * 0.0
    return (series - mu) / sd


def composite_rating(df, weights):
    """Combina elo, fifa_points y player_overall en R, reescalado a escala Elo.
    Devuelve una Serie indexada por team."""
    z = (
        weights["elo"] * zscore(df["elo"])
        + weights["fifa"] * zscore(df["fifa_points"])
        + weights["players"] * zscore(df["player_overall"])
    )
    # Reescalar a escala Elo usando media y dispersión del Elo observado.
    R = df["elo"].mean() + z * df["elo"].std(ddof=0)
    R.index = df["team"]
    return R


def unit_strengths_from_players(players, top_n=4):
    """Para cada equipo, agrega la fuerza de cada línea (POR/DEF/MED/ATA)
    como el promedio de los atributos relevantes de sus mejores `top_n` jugadores
    de esa línea. Devuelve un DataFrame indexado por team con columnas de unidad."""
    rows = {}
    for team, tdf in players.groupby("team"):
        unit_vals = {}
        for line, attrs in UNIT_ATTRS.items():
            sub = tdf[tdf["line"] == [k for k, v in LINE_OF_POSITION.items() if v == line][0]]
            if sub.empty:
                unit_vals[line] = np.nan
                continue
            # Puntaje por jugador = promedio de sus atributos de línea.
            scores = sub[attrs].mean(axis=1).sort_values(ascending=False)
            unit_vals[line] = scores.head(top_n).mean()
        rows[team] = unit_vals
    out = pd.DataFrame.from_dict(rows, orient="index")
    out.index.name = "team"
    return out
