# tests/test_fetch_data.py
from src.fetch_data import parse_elo_table

def test_parse_elo_table_extracts_team_and_rating():
    html = """
    <table><tr><td>1</td><td><a>Spain</a></td><td>2150</td></tr>
    <tr><td>2</td><td><a>France</a></td><td>2100</td></tr></table>
    """
    df = parse_elo_table(html)
    assert {"team", "elo"} <= set(df.columns)
    assert df.loc[df["team"] == "Spain", "elo"].iloc[0] == 2150
