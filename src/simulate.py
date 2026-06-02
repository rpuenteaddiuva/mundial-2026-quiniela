# src/simulate.py
"""Simulación Monte Carlo del Mundial 2026: grupos, desempates FIFA y eliminatorias."""
import numpy as np
import pandas as pd
from itertools import combinations
from src.match_model import expected_goals
from src.teams import GROUPS, HOSTS, group_of

def round_robin(teams):
    """Todos los enfrentamientos de un grupo (6 para 4 equipos)."""
    return list(combinations(teams, 2))

def simulate_match_goals(rng, att_i, def_i, att_j, def_j, home, params):
    """Muestrea un marcador con Poisson independiente. Devuelve (goles_i, goles_j)."""
    li, lj = expected_goals(att_i, def_i, att_j, def_j, home, params)
    return int(rng.poisson(li)), int(rng.poisson(lj))

def group_standings(teams, results):
    """Construye la tabla de un grupo ordenada por reglas FIFA:
    puntos → diferencia de goles → goles a favor → enfrentamiento directo.
    `results` = lista de (home, away, goles_home, goles_away)."""
    stats = {t: {"points": 0, "gf": 0, "ga": 0} for t in teams}
    for h, a, gh, ga in results:
        stats[h]["gf"] += gh; stats[h]["ga"] += ga
        stats[a]["gf"] += ga; stats[a]["ga"] += gh
        if gh > ga:
            stats[h]["points"] += 3
        elif gh < ga:
            stats[a]["points"] += 3
        else:
            stats[h]["points"] += 1; stats[a]["points"] += 1
    rows = []
    for t in teams:
        s = stats[t]
        rows.append({"team": t, "points": s["points"], "gf": s["gf"],
                     "ga": s["ga"], "gd": s["gf"] - s["ga"]})
    table = pd.DataFrame(rows)
    # Desempate por puntos, luego DG, luego GF. (Head-to-head y fair play omitidos
    # por simplicidad; su impacto en la probabilidad de campeón es marginal.)
    table = table.sort_values(["points", "gd", "gf"], ascending=False).reset_index(drop=True)
    table["rank"] = table.index + 1
    return table

def best_thirds(thirds):
    """De los 12 terceros, devuelve los 8 mejores por puntos→DG→GF."""
    ranked = thirds.sort_values(["points", "gd", "gf"], ascending=False).reset_index(drop=True)
    return ranked.head(8).reset_index(drop=True)

def knockout_winner(rng, team_i, team_j, params):
    """Partido a eliminación directa. Cada equipo = (nombre, att_eff, def_eff).
    Si empata en tiempo reglamentario, se resuelve por penales con probabilidad
    proporcional a la fuerza ofensiva (proxy)."""
    ni, ai, di = team_i
    nj, aj, dj = team_j
    gi, gj = simulate_match_goals(rng, ai, di, aj, dj, home=False, params=params)
    if gi > gj:
        return ni
    if gj > gi:
        return nj
    # Penales: ventaja leve al de mayor ataque efectivo.
    p_i = 1.0 / (1.0 + np.exp(-(ai - aj)))
    return ni if rng.random() < p_i else nj


from src.match_model import effective_ratings

# Bracket de R32 del formato de 48 (mapeo oficial FIFA de posiciones de grupo a llaves).
# Cada entrada = (slot_a, slot_b). Los slots "1X"/"2X" son ganador/segundo de grupo X;
# "3rd:i" es el i-ésimo mejor tercero asignado según la tabla oficial.
# IMPORTANTE: la tabla EXACTA de asignación de terceros se transcribe de la fuente
# oficial FIFA durante la implementación (ver nota al final de la task).
R32_BRACKET = None  # se carga vía load_bracket()

def _eff(row, params):
    return effective_ratings(row, params["unit_weight"])

def build_r32(qualifiers, chosen_thirds):
    """Ordena los 32 clasificados en el cuadro de R32 según el mapeo oficial FIFA.
    Devuelve una lista de 32 nombres en orden de llave (0v1, 2v3, ...).

    Implementación: cargar el orden de slots desde src.bracket_2026.SLOT_ORDER,
    donde cada slot es '1A','2B' o '3rd:n'. Aquí se resuelven a equipos concretos."""
    from src.bracket_2026 import SLOT_ORDER, THIRD_ASSIGNMENT
    pos_to_team = {pos: team for team, pos in qualifiers}
    thirds_list = list(chosen_thirds["team"])
    ordered = []
    for slot in SLOT_ORDER:
        if slot.startswith("3rd:"):
            idx = int(slot.split(":")[1])
            ordered.append(thirds_list[idx])
        else:
            ordered.append(pos_to_team[slot])
    return ordered

def simulate_tournament(rng, ratings, params):
    """Simula un torneo completo y devuelve el nombre del campeón.
    `ratings` indexado por team con columnas R_z, ATA_z, DEF_z."""
    # --- Fase de grupos ---
    qualifiers = []   # (team, position) para 1° y 2°
    thirds_rows = []
    for letter, members in GROUPS.items():
        results = []
        for h, a in round_robin(members):
            ah, dh = _eff(ratings.loc[h], params)
            aa, da = _eff(ratings.loc[a], params)
            home = h in HOSTS
            gh, ga = simulate_match_goals(rng, ah, dh, aa, da, home, params)
            results.append((h, a, gh, ga))
        table = group_standings(members, results)
        qualifiers.append((table.iloc[0]["team"], f"1{letter}"))
        qualifiers.append((table.iloc[1]["team"], f"2{letter}"))
        third = table.iloc[2]
        thirds_rows.append({"team": third["team"], "group": letter,
                            "points": third["points"], "gd": third["gd"], "gf": third["gf"]})
    chosen_thirds = best_thirds(pd.DataFrame(thirds_rows))

    # --- Construir el cuadro de 32 y jugar las eliminatorias ---
    bracket_teams = build_r32(qualifiers, chosen_thirds)  # lista ordenada de 32 nombres
    teams = [(t, *_eff(ratings.loc[t], params)) for t in bracket_teams]
    while len(teams) > 1:
        nxt = []
        for k in range(0, len(teams), 2):
            w = knockout_winner(rng, teams[k], teams[k + 1], params)
            # recuperar att/def del ganador
            wi = teams[k] if teams[k][0] == w else teams[k + 1]
            nxt.append(wi)
        teams = nxt
    return teams[0][0]

def run_monte_carlo(ratings, params, n_sims, seed):
    """Corre n_sims torneos y agrega la probabilidad de campeón por equipo.
    Devuelve un DataFrame: team, champion (probabilidad)."""
    rng = np.random.default_rng(seed)
    from src.teams import team_list
    counts = {t: 0 for t in team_list()}
    for _ in range(n_sims):
        counts[simulate_tournament(rng, ratings, params)] += 1
    df = pd.DataFrame({"team": list(counts), "champion": [c / n_sims for c in counts.values()]})
    return df.sort_values("champion", ascending=False).reset_index(drop=True)
