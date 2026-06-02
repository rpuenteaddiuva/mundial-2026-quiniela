# tests/test_report.py
import pandas as pd, pathlib
from src.report import write_champion_table

def test_write_champion_table(tmp_path):
    probs = pd.DataFrame({"team": ["Spain", "France"], "champion": [0.18, 0.15]})
    out = tmp_path / "probabilidades_campeon.csv"
    write_champion_table(probs, out)
    assert out.exists()
    loaded = pd.read_csv(out)
    assert loaded.iloc[0]["team"] == "Spain"
