# src/fetch_data.py
"""Baja datos públicos (Elo, ranking FIFA, atributos de jugadores) y ensambla
data/processed/ratings.csv. Guarda snapshots crudos fechados en data/raw/."""
import pandas as pd
from bs4 import BeautifulSoup

def parse_elo_table(html):
    """Extrae (team, elo) de una tabla HTML de eloratings.net."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) >= 3:
            team = cells[1].get_text(strip=True)
            try:
                elo = int(cells[2].get_text(strip=True))
            except ValueError:
                continue
            rows.append({"team": team, "elo": elo})
    return pd.DataFrame(rows)


import requests, datetime, pathlib
from src.teams import team_list

RAW = pathlib.Path("data/raw")
PROCESSED = pathlib.Path("data/processed")

# Mapa de nombres de fuente → nombres canónicos de src.teams (rellenar al ver datos).
NAME_MAP = {
    "South Korea": "Korea Republic", "Turkey": "Turkiye",
    "DR Congo": "Congo DR", "Ivory Coast": "Ivory Coast", "USA": "United States",
    # ... completar según las fuentes
}

def _canon(name):
    return NAME_MAP.get(name, name)

def fetch_all(stamp=None):
    """Orquesta el fetch y produce data/processed/ratings.csv.
    Guarda snapshots crudos con fecha. Si el componente de jugadores falla,
    rellena POR/DEF/MED/ATA con NaN y documenta el fallback."""
    stamp = stamp or datetime.date.today().isoformat()
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    # 1) Elo
    elo_html = requests.get("https://www.eloratings.net/", timeout=30).text
    (RAW / f"elo_{stamp}.html").write_text(elo_html, encoding="utf-8")
    elo = parse_elo_table(elo_html)
    elo["team"] = elo["team"].map(_canon)
    # 2) FIFA y 3) jugadores: análogo (parsers dedicados); ver README para fuentes.
    # ... fetch_fifa(), fetch_players() con sus parsers y snapshots ...
    raise NotImplementedError("Completar fetch_fifa y fetch_players con sus fuentes")
