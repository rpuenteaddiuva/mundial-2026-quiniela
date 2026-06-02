# Modelo de quiniela — Mundial 2026

Pipeline en Python que estima la **probabilidad de campeón** del Mundial 2026
combinando una **fuerza compuesta por selección** (Elo + ranking FIFA + atributos
de jugadores) con una **simulación Monte Carlo** del torneo (fase de grupos,
mejores terceros y bracket de eliminatorias del formato de 48 equipos). El modelo
es reutilizable **partido a partido** para apoyar la quiniela.

## Cómo funciona

1. **Datos** (`src/teams.py`, `src/fetch_data.py`): los 12 grupos del sorteo
   (5 dic 2025) son un hecho fijo y se codifican con nombres canónicos. El resto
   de señales (Elo, FIFA, jugadores) se descargan y se ensamblan en
   `data/processed/ratings.csv`.
2. **Ratings** (`src/ratings.py`): cada señal se estandariza (z-score) y se mezcla
   con los pesos de `config.yaml` para construir la fuerza compuesta `R`
   (reescalada a escala Elo, ~1500–2100). Los atributos de jugadores agregan las
   fuerzas de unidad **POR/DEF/MED/ATA** (escala 0–100).
3. **Modelo de partido** (`src/match_model.py`): de las fuerzas efectivas de
   ataque y defensa se derivan los goles esperados (Poisson, ataque vs defensa),
   la matriz de marcadores, las probabilidades de victoria/empate/derrota y el
   marcador más probable.
4. **Simulación** (`src/simulate.py`, `src/bracket_2026.py`): round-robin de
   grupos con desempates FIFA (puntos → diferencia de goles → goles a favor),
   selección de los 8 mejores terceros, construcción del cuadro de Ronda de 32 y
   Monte Carlo del torneo completo.
5. **Salidas** (`src/report.py`, `src/run_pipeline.py`, `src/network.py`): tabla
   de probabilidades de campeón, gráfico de favoritos y grafo de fuerza por grupos.
6. **Análisis por-partido** (`src/predict.py`): CLI reutilizable durante la
   quiniela.

## Contrato de datos

`data/processed/ratings.csv` — una fila por selección (48 filas):

```
team, confederation, elo, fifa_points, player_overall, POR, DEF, MED, ATA, R
```

donde `POR/DEF/MED/ATA/player_overall` están en escala 0–100 y `R` en escala tipo
Elo (~1500–2100).

## Instalación

```bash
pip install -r requirements.txt
```

Requiere Python 3.11+. Dependencias: pandas, numpy, scipy, networkx, matplotlib,
PyYAML, requests, BeautifulSoup4, pytest.

## Flujo de uso

1. **Descargar y ensamblar los datos** (genera `data/processed/ratings.csv` con
   snapshots crudos fechados en `data/raw/`):

   ```bash
   python -c "from src.fetch_data import fetch_all; fetch_all()"
   ```

2. **Correr el pipeline completo** (Monte Carlo + reporte):

   ```bash
   python -m src.run_pipeline
   ```

   Imprime el top 15 de favoritos y genera en `outputs/`:
   - `probabilidades_campeon.csv` (48 filas, las probabilidades suman ~1)
   - `favoritos.png` (gráfico de barras de los favoritos)

## CLI por-partido

Para analizar un cruce concreto durante la quiniela:

```bash
python -m src.predict --home "Mexico" --away "Korea Republic" --home-venue
```

Usa `--home-venue` cuando el equipo local juega en sede anfitriona (US/MX/CA),
para aplicar la ventaja local del modelo. Salida:

```
Mexico vs Korea Republic
  P(victoria Mexico): ...
  P(empate):          ...
  P(victoria Korea Republic): ...
  Goles esperados: ... - ...
  Marcador más probable: x-y
```

## Configuración (pesos y parámetros)

Todos los pesos y parámetros viven en `config.yaml`:

- `weights`: peso de cada señal en la fuerza compuesta `R` (`elo`, `fifa`,
  `players`; deben sumar 1.0).
- `goals`: parámetros del modelo de goles Poisson (`base_mu`, `beta`,
  `home_boost`, `unit_weight`, `max_goals`, `dixon_coles`).
- `simulation`: número de simulaciones (`n_sims`) y semilla (`seed`).

## Tests

```bash
pytest -v
```

## Caveats

- **Snapshots fechados:** `fetch_all()` guarda los HTML crudos en `data/raw/` con
  fecha en el nombre para que los resultados sean reproducibles frente a cambios
  en las fuentes en vivo.
- **Fallback de jugadores:** si el componente de atributos de jugadores falla, las
  columnas `POR/DEF/MED/ATA` se rellenan con `NaN` y el ensamblado debe documentar
  la cobertura efectiva de cada señal. El fetch de FIFA y jugadores está marcado
  como pendiente en `src/fetch_data.py` (`fetch_fifa`, `fetch_players`); ver el
  código para las fuentes previstas.
- **Aproximación de los mejores terceros:** la asignación exacta de los 8 mejores
  terceros a los huecos del cuadro depende del Anexo C de la reglamentación FIFA
  (495 combinaciones según cuáles 8 de los 12 grupos producen un tercero
  clasificado) y solo se determina con los resultados reales. Aquí se usa una
  **aproximación documentada**: el n-ésimo mejor tercero (ranking 0..7) se asigna
  al n-ésimo hueco en orden de aparición del cuadro (M74, M77, M79, M80, M81, M82,
  M85, M87). Su efecto sobre la probabilidad de campeón es de segundo orden. Ver
  `src/bracket_2026.py` para el detalle y las restricciones por hueco.
- **Desempates de grupo:** se aplican puntos → diferencia de goles → goles a
  favor. El enfrentamiento directo y el fair play se omiten por simplicidad; su
  impacto sobre la probabilidad de campeón es marginal.
- **Modelo de goles:** el contrato actual es Poisson independiente. El ajuste
  Dixon-Coles (flag `goals.dixon_coles`) queda como mejora posterior.

## Estructura del proyecto

| Archivo | Responsabilidad |
|---|---|
| `config.yaml` | Pesos de señales, parámetros del modelo de goles, N de simulaciones, seed |
| `src/teams.py` | 12 grupos × 4 equipos, nombres canónicos, sedes anfitrionas |
| `src/ratings.py` | z-score, fuerzas de unidad, fuerza compuesta `R`, columnas del modelo |
| `src/match_model.py` | Goles esperados, matriz de marcadores, P(V/E/D), marcador más probable |
| `src/simulate.py` | Round-robin, tabla de grupo, mejores terceros, KO, Monte Carlo |
| `src/bracket_2026.py` | Cuadro de Ronda de 32 (slots y asignación de terceros) |
| `src/network.py` | Grafo de fuerza (networkx) + visualización |
| `src/fetch_data.py` | Descarga Elo/FIFA/jugadores y ensambla `data/processed/` |
| `src/predict.py` | CLI de análisis por-partido |
| `src/report.py` | Tablas y figuras de salida |
| `src/run_pipeline.py` | Orquestador del pipeline completo |
| `tests/` | Tests unitarios por módulo |
