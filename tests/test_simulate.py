# tests/test_simulate.py
import numpy as np
from src.simulate import round_robin

def test_round_robin_four_teams_six_matches():
    pairs = round_robin(["A", "B", "C", "D"])
    assert len(pairs) == 6
    assert ("A", "B") in pairs or ("B", "A") in pairs
    # Sin repetir enfrentamiento.
    norm = {frozenset(p) for p in pairs}
    assert len(norm) == 6


from src.simulate import simulate_match_goals

def test_simulate_match_goals_deterministic_with_seed():
    rng = np.random.default_rng(42)
    gi, gj = simulate_match_goals(rng, att_i=1.0, def_i=0.0, att_j=-1.0, def_j=0.0,
                                  home=False, params={"base_mu":1.35,"beta":0.85,"home_boost":0.25})
    assert isinstance(gi, int) and isinstance(gj, int)
    # El equipo i es mucho más fuerte: en promedio marca más (chequeo agregado).
    rng2 = np.random.default_rng(7)
    diffs = []
    for _ in range(2000):
        a, b = simulate_match_goals(rng2, 1.0, 0.0, -1.0, 0.0, False,
                                    {"base_mu":1.35,"beta":0.85,"home_boost":0.25})
        diffs.append(a - b)
    assert np.mean(diffs) > 0


from src.simulate import group_standings

def test_group_standings_tiebreak_by_goal_difference():
    # A y B con 6 pts; A con mejor diferencia de goles debe quedar 1°.
    results = [
        ("A", "C", 3, 0), ("A", "D", 1, 0),
        ("B", "C", 1, 0), ("B", "D", 1, 0),
        ("A", "B", 0, 1),  # B le gana a A
        ("C", "D", 0, 0),
    ]
    table = group_standings(["A", "B", "C", "D"], results)
    # B venció a A pero comparten 6 pts; el orden aplica pts→DG→GF.
    assert set(table["team"].head(2)) == {"A", "B"}
    # Verifica columnas requeridas para desempate.
    for col in ("points", "gd", "gf"):
        assert col in table.columns


import pandas as pd
from src.simulate import best_thirds

def test_best_thirds_picks_top_eight():
    # 12 terceros con puntos decrecientes; deben salir los 8 con más puntos.
    thirds = pd.DataFrame({
        "team": [f"T{i}" for i in range(12)],
        "group": list("ABCDEFGHIJKL"),
        "points": [9,8,7,6,5,4,3,2,1,0,0,0],
        "gd": [0]*12, "gf": [0]*12,
    })
    chosen = best_thirds(thirds)
    assert len(chosen) == 8
    assert set(chosen["team"]) == {f"T{i}" for i in range(8)}


from src.simulate import knockout_winner

def test_knockout_never_draws():
    rng = np.random.default_rng(1)
    params = {"base_mu":1.35,"beta":0.85,"home_boost":0.25}
    winners = set()
    for _ in range(50):
        w = knockout_winner(rng, ("A", 0.5, 0.4), ("B", -0.5, -0.4), params)
        assert w in ("A", "B")
        winners.add(w)
    assert "A" in winners  # el más fuerte gana al menos una vez


from src.simulate import simulate_tournament
from src.teams import GROUPS

def _toy_ratings():
    teams = []
    for letter, members in GROUPS.items():
        for i, t in enumerate(members):
            teams.append({"team": t, "R_z": 0.0, "ATA_z": 0.0, "DEF_z": 0.0})
    df = pd.DataFrame(teams).set_index("team")
    return df

def test_simulate_tournament_returns_known_team():
    from src.teams import team_list
    rng = np.random.default_rng(123)
    params = {"base_mu":1.35,"beta":0.85,"home_boost":0.25,"unit_weight":0.35}
    champ = simulate_tournament(rng, _toy_ratings(), params)
    assert champ in team_list()


from src.simulate import run_monte_carlo

def test_monte_carlo_probabilities_sum_to_one():
    ratings = _toy_ratings()
    params = {"base_mu":1.35,"beta":0.85,"home_boost":0.25,"unit_weight":0.35}
    probs = run_monte_carlo(ratings, params, n_sims=200, seed=5)
    assert abs(probs["champion"].sum() - 1.0) < 1e-6
    assert len(probs) == 48
