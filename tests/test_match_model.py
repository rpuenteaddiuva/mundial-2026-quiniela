# tests/test_match_model.py
import numpy as np
from src.match_model import expected_goals, wdl_probabilities, most_likely_score

PARAMS = {"base_mu": 1.35, "beta": 0.85, "home_boost": 0.25, "unit_weight": 0.35}

def test_symmetric_teams_equal_lambdas():
    li, lj = expected_goals(att_i=0.0, def_i=0.0, att_j=0.0, def_j=0.0, home=False, params=PARAMS)
    assert abs(li - lj) < 1e-9

def test_stronger_attack_more_goals():
    strong = expected_goals(att_i=1.0, def_i=0.0, att_j=0.0, def_j=0.0, home=False, params=PARAMS)[0]
    weak = expected_goals(att_i=0.0, def_i=0.0, att_j=0.0, def_j=0.0, home=False, params=PARAMS)[0]
    assert strong > weak

def test_home_boost_increases_home_lambda():
    home = expected_goals(0.0, 0.0, 0.0, 0.0, home=True, params=PARAMS)[0]
    neutral = expected_goals(0.0, 0.0, 0.0, 0.0, home=False, params=PARAMS)[0]
    assert home > neutral

def test_wdl_probabilities_sum_to_one():
    p = wdl_probabilities(1.5, 1.2, max_goals=10)
    assert abs(p["win"] + p["draw"] + p["loss"] - 1.0) < 1e-6

def test_wdl_favors_higher_lambda():
    p = wdl_probabilities(2.5, 0.8, max_goals=10)
    assert p["win"] > p["loss"]

def test_most_likely_score_returns_tuple():
    s = most_likely_score(1.6, 1.1, max_goals=10)
    assert isinstance(s, tuple) and len(s) == 2

from src.match_model import effective_ratings
import pandas as pd

def test_effective_ratings_blend_overall_and_units():
    row = pd.Series({"R": 1900.0, "ATA": 85.0, "DEF": 80.0,
                     "R_z": 1.0, "ATA_z": 1.2, "DEF_z": 0.5})
    att, dfn = effective_ratings(row, unit_weight=0.35)
    # El ataque efectivo mezcla R_z (global) y ATA_z (unidad).
    assert abs(att - ((1 - 0.35) * 1.0 + 0.35 * 1.2)) < 1e-9
    assert abs(dfn - ((1 - 0.35) * 1.0 + 0.35 * 0.5)) < 1e-9
