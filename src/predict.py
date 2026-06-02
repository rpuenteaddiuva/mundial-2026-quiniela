# src/predict.py
"""Análisis por-partido reutilizable durante la quiniela.
Uso: python -m src.predict --home "Mexico" --away "Korea Republic" --home-venue"""
import argparse, yaml
import pandas as pd
from src.match_model import effective_ratings, expected_goals, wdl_probabilities, most_likely_score
from src.ratings import add_model_columns

def predict_match(home_team, away, ratings, cfg, home_venue=False, home=None):
    # Acepta también el alias `home=` para indicar ventaja de localía.
    if home is not None:
        home_venue = home
    ai, di = effective_ratings(ratings.loc[home_team], cfg["unit_weight"])
    aj, dj = effective_ratings(ratings.loc[away], cfg["unit_weight"])
    li, lj = expected_goals(ai, di, aj, dj, home_venue, cfg)
    wdl = wdl_probabilities(li, lj, cfg["max_goals"])
    # Renormaliza por la masa truncada en max_goals para que sumen 1 exacto.
    total = wdl["win"] + wdl["draw"] + wdl["loss"]
    if total > 0:
        wdl = {k: v / total for k, v in wdl.items()}
    return {**wdl, "xg_home": li, "xg_away": lj, "score": most_likely_score(li, lj, cfg["max_goals"])}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--home", required=True); ap.add_argument("--away", required=True)
    ap.add_argument("--home-venue", action="store_true")
    args = ap.parse_args()
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))["goals"]
    ratings = add_model_columns(pd.read_csv("data/processed/ratings.csv")).set_index("team")
    r = predict_match(args.home, args.away, ratings, cfg, args.home_venue)
    print(f"{args.home} vs {args.away}")
    print(f"  P(victoria {args.home}): {r['win']:.1%}")
    print(f"  P(empate):              {r['draw']:.1%}")
    print(f"  P(victoria {args.away}): {r['loss']:.1%}")
    print(f"  Goles esperados: {r['xg_home']:.2f} - {r['xg_away']:.2f}")
    print(f"  Marcador más probable: {r['score'][0]}-{r['score'][1]}")

if __name__ == "__main__":
    main()
