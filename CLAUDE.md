# CLAUDE.md — Modelo de quiniela Mundial 2026

Modelo estadístico para predecir el Mundial FIFA 2026 (48 selecciones). Convierte cada selección en
un **nodo** con una fuerza compuesta y simula el torneo completo con **Monte Carlo** para estimar la
probabilidad de campeón. Pensado para una quiniela de oficina y para análisis **partido a partido**.

**Idioma:** todo el output, comentarios y reportes en **español**.

## Comandos

```powershell
# Instalar dependencias (una vez)
python -m pip install -r requirements.txt

# Correr la suite de tests (26 tests)
python -m pytest -q

# Pipeline completo: lee ratings.csv -> Monte Carlo -> outputs/
python -m src.run_pipeline

# Análisis de UN partido (lo que se usa cada jornada del torneo)
python -m src.predict --home "Mexico" --away "Korea Republic" --home-venue
#   --home-venue solo si el "local" juega en sede US/MX/CA
#   los nombres van EN INGLÉS, exactamente como en src/teams.py
```

## Arquitectura (flujo de datos)

`data/processed/ratings.csv` → `ratings.add_model_columns` → `simulate.run_monte_carlo`
(usa `match_model`) → `report` escribe `outputs/`.

| Módulo | Responsabilidad | Funciones clave |
|---|---|---|
| `src/teams.py` | Hechos fijos: 12 grupos, sedes, helpers | `GROUPS`, `HOSTS`, `team_list`, `group_of` |
| `src/ratings.py` | Fuerza compuesta `R` y unidades por línea | `composite_rating`, `unit_strengths_from_players`, `add_model_columns`, `zscore` |
| `src/match_model.py` | Modelo Poisson de partido | `expected_goals`, `wdl_probabilities`, `most_likely_score`, `effective_ratings` |
| `src/simulate.py` | Monte Carlo del torneo | `run_monte_carlo`, `simulate_tournament`, `group_standings`, `best_thirds`, `knockout_winner`, `build_r32` |
| `src/bracket_2026.py` | Cuadro R32: `SLOT_ORDER`, `THIRD_ASSIGNMENT` | (ver caveat abajo) |
| `src/predict.py` | CLI de análisis por-partido | `predict_match` |
| `src/network.py` | Grafo de fuerza (nodos) + visualización | `build_strength_graph` |
| `src/fetch_data.py` | Baja datos públicos (parcial) | `parse_elo_table`, `fetch_all` |
| `src/report.py` | Tablas y figuras | `write_champion_table`, `plot_top_champions` |
| `src/run_pipeline.py` | Orquestador del pipeline | `main` |

## Convenciones (IMPORTANTE)

- **Nombres canónicos de equipo** viven en `src/teams.py` y son en inglés (p.ej. `"Korea Republic"`,
  `"Turkiye"`, `"Congo DR"`, `"United States"`, `"Curacao"`). Todo el código y `predict.py` usan esos
  nombres exactos. No los cambies sin actualizar `teams.py`.
- **Contrato de `data/processed/ratings.csv`** (48 filas):
  `team, elo, fifa_points, player_overall, POR, DEF, MED, ATA, R`
  - `POR/DEF/MED/ATA/player_overall` en escala 0–100; `R` en escala tipo Elo (~1500–2150).
- **`R` se calcula** con `ratings.composite_rating(df, weights)` (z-score ponderado reescalado a Elo).
  Si editas un dato de entrada (elo/fifa/overall), **recalcula `R`**, no lo edites a mano.
- **Parámetros del modelo** están todos en `config.yaml` (pesos, `beta`, `home_boost`, `n_sims`, seed).
  Ajustar el modelo = editar `config.yaml`, no el código.
- **TDD**: cada módulo tiene su test en `tests/`. Mantén verde `python -m pytest -q` antes de commitear.
- **Git**: `data/processed/` y `outputs/` están en `.gitignore`; los archivos clave (ratings.csv,
  probabilidades, gráficas) se versionan con `git add -f`.

## Calibración y datos

- **`beta = 0.40`** en `config.yaml`. Con 0.85 (valor inicial) la distribución se concentraba de forma
  irreal (favorito 34%). Con 0.40 el favorito queda ~20–22%, coherente con casas de apuestas.
- **Verifica los datos antes de actualizarlos.** Precedente: la recolección automática trajo el Elo de
  Brasil mal (1763 en vez de 1988); se corrigió contra eloratings.net/Wikipedia. Antes de re-correr con
  datos nuevos, contrasta los Elo de los top contra una fuente autoritativa.
- Resultado base (jun 2026): France ~21% · Spain ~20% · England ~15% · Argentina ~12% · Portugal ~9% · Brazil ~8%.

## Caveat conocido

`src/bracket_2026.py` (`SLOT_ORDER` / `THIRD_ASSIGNMENT`) usa una **aproximación** de la asignación de
los 8 mejores terceros al cuadro de la Ronda de 32, no la tabla oficial FIFA. Afecta poco la
probabilidad de campeón, pero conviene refinarlo con la fuente oficial para precisión en eliminatorias.

## Docs

- Diseño: `docs/2026-06-02-diseno-modelo.md`
- Plan de implementación (TDD): `docs/superpowers/plans/2026-06-02-mundial-2026-modelo.md`
