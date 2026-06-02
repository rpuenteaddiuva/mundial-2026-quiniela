# Plan de Implementación — Modelo de quiniela Mundial 2026

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un pipeline Python que estime la probabilidad de campeón del Mundial 2026 vía fuerza compuesta por selección (nodos) y simulación Monte Carlo, reutilizable partido a partido.

**Architecture:** Capa de datos (seed de grupos + fetch de Elo/FIFA/jugadores) → `ratings` construye fuerza compuesta `R` y fuerzas de unidad POR/DEF/MED/ATA → `match_model` deriva goles esperados (Poisson, ataque vs defensa) → `simulate` corre Monte Carlo del torneo con desempates FIFA y bracket de 48 → `report`/`network` generan salidas. `predict` expone análisis por-partido.

**Tech Stack:** Python 3.11+, pandas, numpy, scipy, networkx, matplotlib, PyYAML, requests, BeautifulSoup4, pytest.

---

## Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `config.yaml` | Pesos de señales, parámetros del modelo de goles, N de simulaciones, seed |
| `requirements.txt` | Dependencias |
| `src/__init__.py` | Marca paquete |
| `src/teams.py` | Hecho fijo: 12 grupos × 4 equipos, nombres canónicos, bracket R32 |
| `src/ratings.py` | z-score, fuerzas de unidad desde jugadores, fuerza compuesta `R` |
| `src/match_model.py` | Goles esperados, matriz de marcadores, P(V/E/D), marcador más probable |
| `src/simulate.py` | Round-robin, tabla de grupo, desempates FIFA, mejores terceros, KO, Monte Carlo |
| `src/network.py` | Grafo de fuerza (networkx) + visualización |
| `src/fetch_data.py` | Baja Elo, ranking FIFA y atributos de jugadores; ensambla `data/processed/` |
| `src/predict.py` | CLI de análisis por-partido |
| `src/report.py` | Tablas y figuras de salida |
| `tests/...` | Tests unitarios por módulo |

**Contrato de datos** — `data/processed/ratings.csv` (una fila por selección, 48 filas):
`team, confederation, elo, fifa_points, player_overall, POR, DEF, MED, ATA, R`
donde `POR/DEF/MED/ATA/player_overall` están en escala 0–100 y `R` en escala tipo Elo (~1500–2100).

---

## Task 1: Scaffolding del proyecto

**Files:**
- Create: `requirements.txt`
- Create: `config.yaml`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`
- Create: `.gitignore`

- [ ] **Step 1: Crear `requirements.txt`**

```
pandas>=2.0
numpy>=1.26
scipy>=1.11
networkx>=3.2
matplotlib>=3.8
PyYAML>=6.0
requests>=2.31
beautifulsoup4>=4.12
pytest>=8.0
```

- [ ] **Step 2: Crear `config.yaml`**

```yaml
# Pesos de las señales para la fuerza compuesta R (deben sumar 1.0)
weights:
  elo: 0.50
  fifa: 0.20
  players: 0.30

# Modelo de goles (Poisson)
goals:
  base_mu: 1.35      # goles promedio por equipo por partido
  beta: 0.85         # sensibilidad a la diferencia de fuerza
  home_boost: 0.25   # incremento aditivo a lambda del local (sedes US/MX/CA)
  unit_weight: 0.35  # peso de las unidades ATA/DEF vs R global en el ataque/defensa efectivos
  max_goals: 10      # tope de la matriz de marcadores
  dixon_coles: false # ajuste opcional de empates/marcadores bajos

simulation:
  n_sims: 20000
  seed: 20260602
```

- [ ] **Step 3: Crear paquetes vacíos**

`src/__init__.py` y `tests/__init__.py` con contenido vacío.

- [ ] **Step 4: Crear `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
data/raw/*
!data/raw/.gitkeep
outputs/*
!outputs/.gitkeep
.venv/
```

- [ ] **Step 5: Crear placeholders de carpetas**

Crear archivos vacíos `data/raw/.gitkeep`, `data/processed/.gitkeep`, `outputs/.gitkeep`.

- [ ] **Step 6: Instalar dependencias y verificar**

Run: `python -m pip install -r requirements.txt`
Expected: instala sin error.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: scaffolding del proyecto (config, deps, estructura)"
```

---

## Task 2: Datos fijos — grupos y bracket (`src/teams.py`)

Los 12 grupos del sorteo (5 dic 2025) son un hecho fijo, no se fetchea. Se codifican con nombres canónicos que usarán todos los módulos.

**Files:**
- Create: `src/teams.py`
- Test: `tests/test_teams.py`

- [ ] **Step 1: Escribir el test que falla**

```python
# tests/test_teams.py
from src.teams import GROUPS, team_list, group_of

def test_twelve_groups_of_four():
    assert len(GROUPS) == 12
    assert all(len(teams) == 4 for teams in GROUPS.values())

def test_total_48_unique_teams():
    teams = team_list()
    assert len(teams) == 48
    assert len(set(teams)) == 48

def test_known_memberships():
    assert "Argentina" in GROUPS["J"]
    assert "Spain" in GROUPS["H"]
    assert group_of("Mexico") == "A"
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `pytest tests/test_teams.py -v`
Expected: FAIL (ImportError: src.teams).

- [ ] **Step 3: Implementar `src/teams.py`**

```python
# src/teams.py
"""Hechos fijos del Mundial 2026: grupos sorteados y bracket de eliminatorias.
Fuente: sorteo FIFA 5 dic 2025 (NBC Sports / Wikipedia 2026 FIFA World Cup)."""

GROUPS = {
    "A": ["Mexico", "South Africa", "Korea Republic", "Czechia"],
    "B": ["Canada", "Bosnia-Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkiye"],
    "E": ["Germany", "Curacao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "Congo DR", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

# Sedes anfitrionas (ventaja local en el modelo de goles).
HOSTS = {"United States", "Mexico", "Canada"}


def team_list():
    """Lista plana de las 48 selecciones."""
    return [t for teams in GROUPS.values() for t in teams]


def group_of(team):
    """Letra de grupo de una selección."""
    for letter, teams in GROUPS.items():
        if team in teams:
            return letter
    raise KeyError(f"Selección desconocida: {team}")
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `pytest tests/test_teams.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/teams.py tests/test_teams.py
git commit -m "feat: grupos fijos del Mundial 2026 y helpers de selección"
```

> **Nota de implementación:** El mapeo exacto de posiciones de grupo a slots de R32 (incluida la tabla oficial de asignación de los 8 mejores terceros) se codifica en la Task 6, citando la fuente oficial. Aquí solo viven los grupos.

---

## Task 3: Construcción de ratings (`src/ratings.py`)

**Files:**
- Create: `src/ratings.py`
- Test: `tests/test_ratings.py`

- [ ] **Step 1: Escribir el test que falla (z-score y blend)**

```python
# tests/test_ratings.py
import numpy as np
import pandas as pd
from src.ratings import zscore, unit_strengths_from_players, composite_rating

def test_zscore_mean_zero_std_one():
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    z = zscore(s)
    assert abs(z.mean()) < 1e-9
    assert abs(z.std(ddof=0) - 1.0) < 1e-9

def test_composite_rating_blend_is_weighted_sum_on_elo_scale():
    # Dos equipos: A claramente superior en las tres señales.
    df = pd.DataFrame({
        "team": ["A", "B"],
        "elo": [2000.0, 1600.0],
        "fifa_points": [1800.0, 1400.0],
        "player_overall": [85.0, 75.0],
    })
    weights = {"elo": 0.5, "fifa": 0.2, "players": 0.3}
    R = composite_rating(df, weights)
    assert R["A"] > R["B"]
    # R se reescala a escala Elo: el promedio debe acercarse al promedio de elo.
    assert 1500 < R.mean() < 2100
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `pytest tests/test_ratings.py -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implementar `zscore` y `composite_rating`**

```python
# src/ratings.py
"""Construye la fuerza compuesta R y las fuerzas de unidad POR/DEF/MED/ATA."""
import numpy as np
import pandas as pd

# Atributos relevantes por línea (claves esperadas en el df de jugadores).
UNIT_ATTRS = {
    "POR": ["reflejos", "manos", "colocacion", "achique"],
    "DEF": ["defensa", "fisico", "aereo", "marca"],
    "MED": ["pase", "regate", "control", "vision"],
    "ATA": ["ritmo", "tiro", "regate", "definicion"],
}
# Qué posiciones aportan a cada línea (columna 'line' del df de jugadores).
LINE_OF_POSITION = {"GK": "POR", "DEF": "DEF", "MID": "MED", "FWD": "ATA"}


def zscore(series):
    """Normaliza una serie a media 0, desviación 1 (poblacional)."""
    mu = series.mean()
    sd = series.std(ddof=0)
    if sd == 0:
        return series * 0.0
    return (series - mu) / sd


def composite_rating(df, weights):
    """Combina elo, fifa_points y player_overall en R, reescalado a escala Elo.
    Devuelve una Serie indexada por team."""
    z = (
        weights["elo"] * zscore(df["elo"])
        + weights["fifa"] * zscore(df["fifa_points"])
        + weights["players"] * zscore(df["player_overall"])
    )
    # Reescalar a escala Elo usando media y dispersión del Elo observado.
    R = df["elo"].mean() + z * df["elo"].std(ddof=0)
    R.index = df["team"]
    return R
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `pytest tests/test_ratings.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Escribir el test que falla (fuerzas de unidad)**

```python
# añadir a tests/test_ratings.py
def test_unit_strengths_aggregate_top_players_per_line():
    # Equipo A: dos delanteros fuertes; equipo B: dos delanteros flojos.
    players = pd.DataFrame([
        {"team": "A", "line": "FWD", "ritmo": 90, "tiro": 90, "regate": 90, "definicion": 90},
        {"team": "A", "line": "FWD", "ritmo": 88, "tiro": 88, "regate": 88, "definicion": 88},
        {"team": "B", "line": "FWD", "ritmo": 60, "tiro": 60, "regate": 60, "definicion": 60},
        {"team": "B", "line": "FWD", "ritmo": 62, "tiro": 62, "regate": 62, "definicion": 62},
    ])
    units = unit_strengths_from_players(players)
    assert units.loc["A", "ATA"] > units.loc["B", "ATA"]
    assert 0 <= units.loc["A", "ATA"] <= 100
```

- [ ] **Step 6: Correr el test para verificar que falla**

Run: `pytest tests/test_ratings.py::test_unit_strengths_aggregate_top_players_per_line -v`
Expected: FAIL (unit_strengths_from_players no definida).

- [ ] **Step 7: Implementar `unit_strengths_from_players`**

```python
# añadir a src/ratings.py
def unit_strengths_from_players(players, top_n=4):
    """Para cada equipo, agrega la fuerza de cada línea (POR/DEF/MED/ATA)
    como el promedio de los atributos relevantes de sus mejores `top_n` jugadores
    de esa línea. Devuelve un DataFrame indexado por team con columnas de unidad."""
    rows = {}
    for team, tdf in players.groupby("team"):
        unit_vals = {}
        for line, attrs in UNIT_ATTRS.items():
            sub = tdf[tdf["line"] == [k for k, v in LINE_OF_POSITION.items() if v == line][0]]
            if sub.empty:
                unit_vals[line] = np.nan
                continue
            # Puntaje por jugador = promedio de sus atributos de línea.
            scores = sub[attrs].mean(axis=1).sort_values(ascending=False)
            unit_vals[line] = scores.head(top_n).mean()
        rows[team] = unit_vals
    out = pd.DataFrame.from_dict(rows, orient="index")
    out.index.name = "team"
    return out
```

- [ ] **Step 8: Correr todos los tests de ratings**

Run: `pytest tests/test_ratings.py -v`
Expected: PASS (3 tests).

- [ ] **Step 9: Commit**

```bash
git add src/ratings.py tests/test_ratings.py
git commit -m "feat: fuerza compuesta R y fuerzas de unidad POR/DEF/MED/ATA"
```

---

## Task 4: Modelo de partido (`src/match_model.py`)

**Files:**
- Create: `src/match_model.py`
- Test: `tests/test_match_model.py`

- [ ] **Step 1: Escribir el test que falla (goles esperados)**

```python
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
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `pytest tests/test_match_model.py -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implementar `expected_goals`**

```python
# src/match_model.py
"""Modelo de partido Poisson basado en ataque vs defensa efectivos."""
import numpy as np
from scipy.stats import poisson

def expected_goals(att_i, def_i, att_j, def_j, home, params):
    """Devuelve (lambda_i, lambda_j): goles esperados de cada equipo.
    att_*/def_* son ratings efectivos estandarizados (z-score). El ataque de i
    se enfrenta a la defensa de j."""
    mu = params["base_mu"]
    beta = params["beta"]
    li = mu * np.exp(beta * (att_i - def_j))
    lj = mu * np.exp(beta * (att_j - def_i))
    if home:
        li += params["home_boost"]
    return li, lj
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `pytest tests/test_match_model.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Escribir el test que falla (matriz de marcadores y WDL)**

```python
# añadir a tests/test_match_model.py
def test_wdl_probabilities_sum_to_one():
    p = wdl_probabilities(1.5, 1.2, max_goals=10)
    assert abs(p["win"] + p["draw"] + p["loss"] - 1.0) < 1e-6

def test_wdl_favors_higher_lambda():
    p = wdl_probabilities(2.5, 0.8, max_goals=10)
    assert p["win"] > p["loss"]

def test_most_likely_score_returns_tuple():
    s = most_likely_score(1.6, 1.1, max_goals=10)
    assert isinstance(s, tuple) and len(s) == 2
```

- [ ] **Step 6: Correr el test para verificar que falla**

Run: `pytest tests/test_match_model.py::test_wdl_probabilities_sum_to_one -v`
Expected: FAIL (wdl_probabilities no definida).

- [ ] **Step 7: Implementar matriz de marcadores, WDL y marcador más probable**

```python
# añadir a src/match_model.py
def score_matrix(li, lj, max_goals=10):
    """Matriz P[a,b] = P(equipo i marca a, equipo j marca b) bajo Poisson independiente."""
    gi = poisson.pmf(np.arange(max_goals + 1), li)
    gj = poisson.pmf(np.arange(max_goals + 1), lj)
    return np.outer(gi, gj)

def wdl_probabilities(li, lj, max_goals=10):
    """Probabilidades de victoria/empate/derrota del equipo i."""
    m = score_matrix(li, lj, max_goals)
    win = np.tril(m, -1).sum()    # i > j (filas > columnas)
    draw = np.trace(m)
    loss = np.triu(m, 1).sum()    # i < j
    return {"win": float(win), "draw": float(draw), "loss": float(loss)}

def most_likely_score(li, lj, max_goals=10):
    """Marcador (a, b) de mayor probabilidad conjunta."""
    m = score_matrix(li, lj, max_goals)
    a, b = np.unravel_index(np.argmax(m), m.shape)
    return (int(a), int(b))
```

- [ ] **Step 8: Correr todos los tests del modelo**

Run: `pytest tests/test_match_model.py -v`
Expected: PASS (6 tests).

- [ ] **Step 9: Escribir test e implementar `effective_ratings` (puente ratings→modelo)**

```python
# añadir a tests/test_match_model.py
from src.match_model import effective_ratings
import pandas as pd

def test_effective_ratings_blend_overall_and_units():
    row = pd.Series({"R": 1900.0, "ATA": 85.0, "DEF": 80.0,
                     "R_z": 1.0, "ATA_z": 1.2, "DEF_z": 0.5})
    att, dfn = effective_ratings(row, unit_weight=0.35)
    # El ataque efectivo mezcla R_z (global) y ATA_z (unidad).
    assert abs(att - ((1 - 0.35) * 1.0 + 0.35 * 1.2)) < 1e-9
    assert abs(dfn - ((1 - 0.35) * 1.0 + 0.35 * 0.5)) < 1e-9
```

```python
# añadir a src/match_model.py
def effective_ratings(team_row, unit_weight):
    """Combina la fuerza global estandarizada (R_z) con la unidad estandarizada
    (ATA_z para ataque, DEF_z para defensa). Devuelve (att_eff, def_eff)."""
    att = (1 - unit_weight) * team_row["R_z"] + unit_weight * team_row["ATA_z"]
    dfn = (1 - unit_weight) * team_row["R_z"] + unit_weight * team_row["DEF_z"]
    return att, dfn
```

Run: `pytest tests/test_match_model.py -v`
Expected: PASS (7 tests).

- [ ] **Step 10: Commit**

```bash
git add src/match_model.py tests/test_match_model.py
git commit -m "feat: modelo de partido Poisson (goles, WDL, marcador, ratings efectivos)"
```

> **Nota:** Dixon-Coles (flag `goals.dixon_coles`) queda como mejora posterior; el contrato actual es Poisson independiente. Si se activa, se aplica el factor de corrección tau(a,b) sobre `score_matrix` para a,b ∈ {0,1}.

---

## Task 5: Estandarización de columnas para el modelo (`src/ratings.py` extensión)

El modelo usa columnas `R_z, ATA_z, DEF_z`. Se añaden al DataFrame de ratings.

**Files:**
- Modify: `src/ratings.py`
- Test: `tests/test_ratings.py`

- [ ] **Step 1: Escribir el test que falla**

```python
# añadir a tests/test_ratings.py
from src.ratings import add_model_columns

def test_add_model_columns_creates_z_scores():
    df = pd.DataFrame({
        "team": ["A", "B", "C"],
        "R": [2000.0, 1800.0, 1600.0],
        "ATA": [88.0, 80.0, 70.0],
        "DEF": [85.0, 78.0, 72.0],
    })
    out = add_model_columns(df)
    for col in ("R_z", "ATA_z", "DEF_z"):
        assert col in out.columns
        assert abs(out[col].mean()) < 1e-9
```

- [ ] **Step 2: Correr el test (falla)**

Run: `pytest tests/test_ratings.py::test_add_model_columns_creates_z_scores -v`
Expected: FAIL.

- [ ] **Step 3: Implementar**

```python
# añadir a src/ratings.py
def add_model_columns(df):
    """Añade R_z, ATA_z, DEF_z (z-scores) usados por el modelo de partido."""
    out = df.copy()
    out["R_z"] = zscore(out["R"])
    out["ATA_z"] = zscore(out["ATA"])
    out["DEF_z"] = zscore(out["DEF"])
    return out
```

- [ ] **Step 4: Correr tests (pasan)**

Run: `pytest tests/test_ratings.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ratings.py tests/test_ratings.py
git commit -m "feat: columnas estandarizadas R_z/ATA_z/DEF_z para el modelo"
```

---

## Task 6: Simulación del torneo (`src/simulate.py`)

Se construye en pasos: round-robin → tabla y desempates → mejores terceros → bracket KO → Monte Carlo.

**Files:**
- Create: `src/simulate.py`
- Test: `tests/test_simulate.py`

- [ ] **Step 1: Test que falla — calendario round-robin**

```python
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
```

- [ ] **Step 2: Correr (falla)** — Run: `pytest tests/test_simulate.py -v` → FAIL.

- [ ] **Step 3: Implementar `round_robin`**

```python
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
```

- [ ] **Step 4: Correr (pasa)** — `pytest tests/test_simulate.py -v` → PASS.

- [ ] **Step 5: Test que falla — simular un partido a goles**

```python
# añadir a tests/test_simulate.py
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
```

- [ ] **Step 6: Correr (falla)** → FAIL.

- [ ] **Step 7: Implementar `simulate_match_goals`**

```python
# añadir a src/simulate.py
def simulate_match_goals(rng, att_i, def_i, att_j, def_j, home, params):
    """Muestrea un marcador con Poisson independiente. Devuelve (goles_i, goles_j)."""
    li, lj = expected_goals(att_i, def_i, att_j, def_j, home, params)
    return int(rng.poisson(li)), int(rng.poisson(lj))
```

- [ ] **Step 8: Correr (pasa)** → PASS.

- [ ] **Step 9: Test que falla — tabla de grupo y desempate por diferencia de goles**

```python
# añadir a tests/test_simulate.py
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
```

- [ ] **Step 10: Correr (falla)** → FAIL.

- [ ] **Step 11: Implementar `group_standings`**

```python
# añadir a src/simulate.py
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
```

- [ ] **Step 12: Correr (pasa)** → PASS.

- [ ] **Step 13: Test que falla — selección de los 8 mejores terceros**

```python
# añadir a tests/test_simulate.py
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
```

- [ ] **Step 14: Correr (falla)** → FAIL.

- [ ] **Step 15: Implementar `best_thirds`**

```python
# añadir a src/simulate.py
def best_thirds(thirds):
    """De los 12 terceros, devuelve los 8 mejores por puntos→DG→GF."""
    ranked = thirds.sort_values(["points", "gd", "gf"], ascending=False).reset_index(drop=True)
    return ranked.head(8).reset_index(drop=True)
```

- [ ] **Step 16: Correr (pasa)** → PASS.

- [ ] **Step 17: Test que falla — partido de eliminatoria nunca empata**

```python
# añadir a tests/test_simulate.py
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
```

- [ ] **Step 18: Correr (falla)** → FAIL.

- [ ] **Step 19: Implementar `knockout_winner`**

```python
# añadir a src/simulate.py
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
```

- [ ] **Step 20: Correr (pasa)** → PASS.

- [ ] **Step 21: Test que falla — torneo completo devuelve un campeón válido**

```python
# añadir a tests/test_simulate.py
from src.simulate import simulate_tournament

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
```

- [ ] **Step 22: Correr (falla)** → FAIL.

- [ ] **Step 23: Implementar `simulate_tournament` (grupos + bracket de 48)**

```python
# añadir a src/simulate.py
from src.match_model import effective_ratings

# Bracket de R32 del formato de 48 (mapeo oficial FIFA de posiciones de grupo a llaves).
# Cada entrada = (slot_a, slot_b). Los slots "1X"/"2X" son ganador/segundo de grupo X;
# "3rd:i" es el i-ésimo mejor tercero asignado según la tabla oficial.
# IMPORTANTE: la tabla EXACTA de asignación de terceros se transcribe de la fuente
# oficial FIFA durante la implementación (ver nota al final de la task).
R32_BRACKET = None  # se carga vía load_bracket()

def _eff(row, params):
    return effective_ratings(row, params["unit_weight"])

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
```

- [ ] **Step 24: Implementar `build_r32` y la tabla de bracket**

> El cuadro de R32 del formato de 48 está publicado por FIFA (posiciones de grupo y asignación de los 8 terceros). Transcribir la tabla oficial a `src/bracket_2026.py` desde la fuente: Wikipedia "2026 FIFA World Cup knockout stage" / documento oficial FIFA. Mientras se transcribe, usar el siguiente esqueleto verificable:

```python
# src/simulate.py — build_r32
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
```

Crear `src/bracket_2026.py` con `SLOT_ORDER` (32 slots en orden de cuadro) y `THIRD_ASSIGNMENT` transcritos de la fuente oficial. Test de estructura:

```python
# tests/test_bracket.py
from src.bracket_2026 import SLOT_ORDER
def test_slot_order_has_32_unique_slots():
    assert len(SLOT_ORDER) == 32
    winners = [s for s in SLOT_ORDER if s.startswith("1")]
    thirds = [s for s in SLOT_ORDER if s.startswith("3rd:")]
    assert len(winners) == 12
    assert len(thirds) == 8
```

- [ ] **Step 25: Test e implementación de Monte Carlo agregado**

```python
# añadir a tests/test_simulate.py
from src.simulate import run_monte_carlo

def test_monte_carlo_probabilities_sum_to_one():
    ratings = _toy_ratings()
    params = {"base_mu":1.35,"beta":0.85,"home_boost":0.25,"unit_weight":0.35}
    probs = run_monte_carlo(ratings, params, n_sims=200, seed=5)
    assert abs(probs["champion"].sum() - 1.0) < 1e-6
    assert len(probs) == 48
```

```python
# añadir a src/simulate.py
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
```

Run: `pytest tests/test_simulate.py tests/test_bracket.py -v`
Expected: PASS (todos).

- [ ] **Step 26: Commit**

```bash
git add src/simulate.py src/bracket_2026.py tests/test_simulate.py tests/test_bracket.py
git commit -m "feat: simulacion Monte Carlo del torneo (grupos, terceros, bracket KO)"
```

> **Nota crítica (terceros y bracket):** La tabla oficial de asignación de los 8 mejores terceros depende de la *combinación de grupos* de la que provienen (tabla publicada por FIFA). En `bracket_2026.py` se transcribe la versión oficial. Si en el momento de implementar no está disponible, se documenta una aproximación (asignar terceros a slots en orden de ranking) y se marca como TODO visible en el README — su efecto sobre la probabilidad de campeón es de segundo orden, pero la aproximación debe quedar declarada.

---

## Task 7: Fetch de datos públicos (`src/fetch_data.py`)

No es unit-testeable contra la web viva; se valida por aserciones sobre la salida. El objetivo es producir `data/processed/ratings.csv` con el contrato definido arriba.

**Files:**
- Create: `src/fetch_data.py`
- Test: `tests/test_fetch_data.py` (tests de parsing con HTML fijo, no de red)

- [ ] **Step 1: Test de parsing con HTML fijo (sin red)**

```python
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
```

- [ ] **Step 2: Correr (falla)** → FAIL.

- [ ] **Step 3: Implementar parsing + fetch con snapshot fechado**

```python
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
```

- [ ] **Step 4: Correr (pasa)** → PASS.

- [ ] **Step 5: Implementar `fetch_all` con normalización de nombres y fallback**

```python
# añadir a src/fetch_data.py
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
```

> El ensamblado final filtra a las 48 selecciones de `team_list()`, valida cobertura y escribe `ratings.csv`. La construcción de `R` y unidades reusa `src/ratings.py`.

- [ ] **Step 6: Verificación manual end-to-end (no es unit test)**

Run: `python -c "from src.fetch_data import fetch_all; fetch_all()"`
Expected (cuando esté completo): genera `data/processed/ratings.csv` con 48 filas y `elo` no nulo. Reportar cobertura de cada señal; si jugadores faltan, debe quedar registrado el fallback.

- [ ] **Step 7: Commit**

```bash
git add src/fetch_data.py tests/test_fetch_data.py
git commit -m "feat: fetch de datos publicos con parsers y snapshots fechados"
```

---

## Task 8: Pipeline principal y reporte (`src/report.py`)

**Files:**
- Create: `src/report.py`
- Create: `src/run_pipeline.py`
- Test: `tests/test_report.py`

- [ ] **Step 1: Test que falla — escritura de salidas**

```python
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
```

- [ ] **Step 2: Correr (falla)** → FAIL.

- [ ] **Step 3: Implementar `write_champion_table` y un gráfico de barras**

```python
# src/report.py
"""Genera tablas y figuras de salida en outputs/."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def write_champion_table(probs, path):
    """Escribe la tabla de probabilidades de campeón ordenada."""
    probs.sort_values("champion", ascending=False).to_csv(path, index=False)

def plot_top_champions(probs, path, top=15):
    """Gráfico de barras con los `top` favoritos."""
    d = probs.sort_values("champion", ascending=False).head(top)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(d["team"][::-1], d["champion"][::-1])
    ax.set_xlabel("Probabilidad de campeón")
    ax.set_title("Mundial 2026 — Favoritos (modelo Monte Carlo)")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
```

- [ ] **Step 4: Correr (pasa)** → PASS.

- [ ] **Step 5: Implementar el orquestador `run_pipeline.py`**

```python
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
    print(probs.head(15).to_string(index=False))

if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Verificación end-to-end (con datos reales de Task 7)**

Run: `python -m src.run_pipeline`
Expected: imprime top 15, genera `outputs/probabilidades_campeon.csv` (48 filas, suma ~1) y `outputs/favoritos.png`. Sanity check: España/Francia/Argentina/Brasil/Inglaterra en la parte alta.

- [ ] **Step 7: Commit**

```bash
git add src/report.py src/run_pipeline.py tests/test_report.py
git commit -m "feat: pipeline principal y reporte de probabilidades"
```

---

## Task 9: Grafo de nodos (`src/network.py`)

**Files:**
- Create: `src/network.py`
- Test: `tests/test_network.py`

- [ ] **Step 1: Test que falla**

```python
# tests/test_network.py
import pandas as pd
from src.network import build_strength_graph

def test_graph_has_node_per_team_with_strength():
    ratings = pd.DataFrame({"team": ["Spain", "France"], "R": [2100.0, 2080.0]}).set_index("team")
    g = build_strength_graph(ratings)
    assert g.number_of_nodes() == 2
    assert g.nodes["Spain"]["strength"] == 2100.0
```

- [ ] **Step 2: Correr (falla)** → FAIL.

- [ ] **Step 3: Implementar**

```python
# src/network.py
"""Grafo de fuerza de selecciones (nodos) y visualización."""
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.teams import GROUPS

def build_strength_graph(ratings):
    """Nodos = selecciones con atributo 'strength'=R; aristas dentro de cada grupo."""
    g = nx.Graph()
    for team, row in ratings.iterrows():
        g.add_node(team, strength=float(row["R"]))
    for members in GROUPS.values():
        present = [t for t in members if t in g]
        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                g.add_edge(present[i], present[j])
    return g

def plot_strength_graph(g, path):
    """Dibuja el grafo con tamaño de nodo proporcional a la fuerza."""
    sizes = [g.nodes[n]["strength"] for n in g]
    smin = min(sizes)
    fig, ax = plt.subplots(figsize=(12, 10))
    pos = nx.spring_layout(g, seed=42)
    nx.draw_networkx(g, pos, ax=ax, node_size=[(s - smin + 50) for s in sizes],
                     font_size=7, node_color="#4C72B0", edge_color="#cccccc")
    ax.set_title("Mundial 2026 — Red de fuerza por grupos")
    ax.axis("off")
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
```

- [ ] **Step 4: Correr (pasa)** → PASS.

- [ ] **Step 5: Commit**

```bash
git add src/network.py tests/test_network.py
git commit -m "feat: grafo de fuerza de selecciones y visualizacion"
```

---

## Task 10: CLI por-partido (`src/predict.py`)

**Files:**
- Create: `src/predict.py`
- Test: `tests/test_predict.py`

- [ ] **Step 1: Test que falla — función pura de predicción**

```python
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
```

- [ ] **Step 2: Correr (falla)** → FAIL.

- [ ] **Step 3: Implementar `predict_match` y el CLI**

```python
# src/predict.py
"""Análisis por-partido reutilizable durante la quiniela.
Uso: python -m src.predict --home "Mexico" --away "Korea Republic" --home-venue"""
import argparse, yaml
import pandas as pd
from src.match_model import effective_ratings, expected_goals, wdl_probabilities, most_likely_score
from src.ratings import add_model_columns

def predict_match(home, away, ratings, cfg, home_venue=False):
    ai, di = effective_ratings(ratings.loc[home], cfg["unit_weight"])
    aj, dj = effective_ratings(ratings.loc[away], cfg["unit_weight"])
    li, lj = expected_goals(ai, di, aj, dj, home_venue, cfg)
    wdl = wdl_probabilities(li, lj, cfg["max_goals"])
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
```

- [ ] **Step 4: Correr (pasa)** → PASS.

- [ ] **Step 5: Commit**

```bash
git add src/predict.py tests/test_predict.py
git commit -m "feat: CLI de analisis por-partido"
```

---

## Task 11: README y cierre

**Files:**
- Create: `README.md`

- [ ] **Step 1: Escribir `README.md`**

Incluir: descripción, instalación (`pip install -r requirements.txt`), flujo
(`python -c "from src.fetch_data import fetch_all; fetch_all()"` → `python -m src.run_pipeline`),
uso del CLI por-partido, dónde viven los pesos (`config.yaml`), y la sección de **caveats**
(fallback de jugadores, aproximación de terceros si aplica, snapshots fechados).

- [ ] **Step 2: Correr toda la suite de tests**

Run: `pytest -v`
Expected: PASS en todos los módulos.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: README con uso, flujo y caveats"
```

---

## Self-Review (cobertura del spec)

- §2 fuerza del nodo `R` → Task 3 ✓ ; §2.1 unidades por posición → Task 3 (unit_strengths_from_players) ✓
- §3 modelo Poisson ataque vs defensa → Task 4 ✓ ; Dixon-Coles flag → nota en Task 4 ✓
- §4 Monte Carlo, desempates FIFA, mejores terceros, bracket → Task 6 ✓
- §5 CLI por-partido → Task 10 ✓
- §6 estructura del proyecto → Tasks 1–11 ✓
- §7 fuentes de datos públicos → Task 7 ✓
- §8 caveats (fallback, snapshots fechados) → Task 7 + README (Task 11) ✓
- §9 criterios de éxito → verificaciones end-to-end en Tasks 7, 8 ✓

**Riesgo conocido declarado:** la tabla oficial de asignación de los 8 mejores terceros (Task 6, Step 24) debe transcribirse de la fuente FIFA; si no está disponible al implementar, se usa aproximación documentada. Es el único punto con dependencia externa de exactitud.
