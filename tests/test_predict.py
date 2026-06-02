# tests/test_predict.py
import pandas as pd
from src.predict import predict_match

def _ratings():
    df = pd.DataFrame({
        "team": ["Mexico", "Korea Republic"],
        "R": [1800.0, 1750.0], "ATA": [80.0, 78.0], "DEF": [78.0, 77.0],
    })
    from src.ratings import add_model_columns
    return add_model_columns(df).set_index("team")

def test_predict_match_returns_wdl_and_score():
    cfg = {"base_mu":1.35,"beta":0.85,"home_boost":0.25,"unit_weight":0.35,"max_goals":10}
    res = predict_match("Mexico", "Korea Republic", _ratings(), cfg, home=True)
    assert abs(res["win"] + res["draw"] + res["loss"] - 1.0) < 1e-6
    assert "score" in res and len(res["score"]) == 2
