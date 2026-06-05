# src/run_pipeline.py
"""Corre el pipeline completo: carga ratings → Monte Carlo → reporte."""
import yaml, pathlib, pandas as pd
from src.ratings import add_model_columns
from src.simulate import run_monte_carlo
from src.report import write_champion_table, plot_top_champions

def main():
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    ratings = pd.read_csv("data/processed/ratings.csv").set_index("team")
    ratings = add_model_columns(ratings.reset_index()).set_index("team")
    probs = run_monte_carlo(ratings, cfg["goals"] | {"unit_weight": cfg["goals"]["unit_weight"]},
                            n_sims=cfg["simulation"]["n_sims"], seed=cfg["simulation"]["seed"])
    out = pathlib.Path("outputs"); out.mkdir(exist_ok=True)
    write_champion_table(probs, out / "probabilidades_campeon.csv")
    plot_top_champions(probs, out / "favoritos.png")
    print(probs.head(20).to_string(index=False))

if __name__ == "__main__":
    main()
