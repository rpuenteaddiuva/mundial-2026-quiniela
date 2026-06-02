# src/match_model.py
"""Modelo de partido Poisson basado en ataque vs defensa efectivos."""
import numpy as np
from scipy.stats import poisson

def expected_goals(att_i, def_i, att_j, def_j, home, params):
    """Devuelve (lambda_i, lambda_j): goles esperados de cada equipo.
    att_*/def_* son ratings efectivos estandarizados (z-score). El ataque de i
    se enfrenta a la defensa de j."""
    mu = params["base_mu"]
    beta = params["beta"]
    li = mu * np.exp(beta * (att_i - def_j))
    lj = mu * np.exp(beta * (att_j - def_i))
    if home:
        li += params["home_boost"]
    return li, lj

def score_matrix(li, lj, max_goals=10):
    """Matriz P[a,b] = P(equipo i marca a, equipo j marca b) bajo Poisson independiente."""
    gi = poisson.pmf(np.arange(max_goals + 1), li)
    gj = poisson.pmf(np.arange(max_goals + 1), lj)
    return np.outer(gi, gj)

def wdl_probabilities(li, lj, max_goals=10):
    """Probabilidades de victoria/empate/derrota del equipo i."""
    m = score_matrix(li, lj, max_goals)
    win = np.tril(m, -1).sum()    # i > j (filas > columnas)
    draw = np.trace(m)
    loss = np.triu(m, 1).sum()    # i < j
    return {"win": float(win), "draw": float(draw), "loss": float(loss)}

def most_likely_score(li, lj, max_goals=10):
    """Marcador (a, b) de mayor probabilidad conjunta."""
    m = score_matrix(li, lj, max_goals)
    a, b = np.unravel_index(np.argmax(m), m.shape)
    return (int(a), int(b))

def effective_ratings(team_row, unit_weight):
    """Combina la fuerza global estandarizada (R_z) con la unidad estandarizada
    (ATA_z para ataque, DEF_z para defensa). Devuelve (att_eff, def_eff)."""
    att = (1 - unit_weight) * team_row["R_z"] + unit_weight * team_row["ATA_z"]
    dfn = (1 - unit_weight) * team_row["R_z"] + unit_weight * team_row["DEF_z"]
    return att, dfn
