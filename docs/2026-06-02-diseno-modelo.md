# Diseño — Modelo de quiniela Mundial 2026

**Fecha:** 2026-06-02
**Autor:** rpuente@addiuva.com (con Claude Code)
**Objetivo:** Estimar la probabilidad de campeón del Mundial 2026 (FIFA, masculino) mediante un
modelo de "nodos" (selecciones = nodos con fuerza compuesta) y simulación Monte Carlo del torneo,
y dejar el motor reutilizable para análisis partido a partido durante la quiniela de la oficina.

---

## 1. Concepto

Cada selección es un **nodo** con una **fuerza compuesta** `R_i`. Los partidos del torneo conectan
los nodos. La probabilidad de campeón **no surge de un truco de grafos**: surge de **simular el
torneo completo miles de veces** usando esas fuerzas y agregando los resultados. El grafo aporta
(a) el marco conceptual de fuerza relativa y (b) una **visualización** del bracket y de las
conexiones de fuerza. Las salidas son estimaciones probabilísticas, no certezas.

---

## 2. Fuerza del nodo `R_i` — mezcla de señales públicas

Combinación vía z-score ponderado de tres señales (pesos en `config.yaml`, ajustables a mano):

| Señal | Peso sugerido | Fuente pública |
|---|---|---|
| Elo (basado en resultados) | 50% | eloratings.net |
| Ranking FIFA | 20% | FIFA oficial (inside.fifa.com) |
| Habilidad de plantilla (jugadores, consciente de posición) | 30% | EA FC / sofifa / Transfermarkt / ESPN squad rankings |

### 2.1 Componente de jugadores — **consciente de posición (por líneas)**

Un "overall" único comprime perfiles muy distintos (un central de 85 ≠ un extremo de 85 ≠ un
portero de 85). Por eso el componente de jugadores se agrega por **línea / unidad**, usando los
atributos relevantes a cada posición:

- **POR (Portero):** reflejos, manos, colocación, achique.
- **DEF (Defensa):** defensa, físico, juego aéreo, marca.
- **MED (Mediocampo):** pase, regate, control, visión.
- **ATA (Ataque):** ritmo, tiro, regate, definición.

Cada equipo obtiene cuatro **fuerzas de unidad**: `POR_i`, `DEF_i`, `MED_i`, `ATA_i`
(además del compuesto `R_i`). Estas alimentan el modelo de partido para que el **ataque de un
equipo se enfrente a la defensa del rival**, que es como se deciden los partidos reales.

---

## 3. Modelo de partido — Poisson de goles

De la diferencia de fuerza relevante (ataque del equipo vs defensa del rival, ajustado por `R_i`
global y ventaja local en sedes US/MX/CA) se derivan los goles esperados de cada lado (`λ_i`, `λ_j`)
y se simula el marcador con distribución de Poisson.

- Ventaja clave: produce **goles y diferencia de goles**, necesarios para los desempates de grupo.
- **Mejora opcional (flag):** ajuste **Dixon-Coles** para corregir la sobre/sub-estimación de
  empates y marcadores bajos.
- *Alternativa descartada:* mapeo Elo directo a V/E/D (más simple pero requiere un modelo de goles
  aparte para desempates).

API reutilizable: `match_model.match_probabilities(team_a, team_b, context)` →
`P(victoria), P(empate), P(derrota)`, goles esperados y marcador más probable.

---

## 4. Simulación Monte Carlo del torneo

- **Fase de grupos:** 12 grupos × 6 partidos, con **reglas de desempate FIFA reales**
  (puntos → diferencia de goles → goles a favor → enfrentamiento directo → fair play → sorteo).
  Avanzan 1°, 2° de cada grupo + los **8 mejores terceros**.
- **Eliminatorias:** R32 → R16 → 4tos → semis → final, respetando el **bracket fijo** de FIFA
  (mapeo predeterminado de posiciones de grupo). Empate en eliminatoria → prórroga → penales
  (modelado con ligera ventaja al favorito o ~50/50 configurable).
- **N = 20,000** simulaciones (configurable). Se agregan por equipo:
  `% campeón`, `% finalista`, `% semifinal`, `% cuartos`, `% avanza de grupo`, `% gana grupo`.

---

## 5. Reutilizable por partido

CLI para análisis puntual de cada juego durante la quiniela:

```
python -m src.predict --home "Mexico" --away "Korea Republic"
```

Salida: P(V/E/D), goles esperados por lado, marcador más probable y top de marcadores.

---

## 6. Estructura del proyecto

```
mundial-2026-quiniela/
├── config.yaml          # pesos de señales, N sims, parámetros del modelo
├── data/raw/            # snapshots fetcheados (elo, fifa, jugadores, grupos)
├── data/processed/      # CSVs limpios (ratings por equipo y por unidad)
├── src/
│   ├── fetch_data.py    # baja datos públicos (con fecha de snapshot)
│   ├── ratings.py       # construye R_i y fuerzas de unidad POR/DEF/MED/ATA
│   ├── match_model.py   # modelo Poisson de partido (+ Dixon-Coles opcional)
│   ├── simulate.py      # Monte Carlo del torneo (grupos + KO + desempates FIFA)
│   ├── network.py       # grafo de fuerza + visualización del bracket
│   ├── predict.py       # CLI de análisis por-partido
│   └── report.py        # tablas y gráficos de salida
├── outputs/             # probabilidades_campeon.csv, figuras, reporte
├── docs/                # este diseño y notas
└── README.md
```

**Stack:** Python — pandas, numpy, scipy, networkx, matplotlib (+ PyYAML). Reportes en español.

---

## 7. Datos: fuentes verificadas (2026-06-02)

- **Grupos 2026 (sorteo 5 dic 2025):** confirmados, 12 grupos de 4.
  Fuentes: NBC Sports, Wikipedia (2026 FIFA World Cup).
- **Elo de selecciones:** eloratings.net.
- **Ranking FIFA:** inside.fifa.com/fifa-world-ranking/men.
- **Habilidad de jugadores:** ESPN squad rankings, EA FC / sofifa (atributos por posición),
  Transfermarkt (valor de mercado como señal de respaldo).

---

## 8. Caveats / decisiones explícitas

- El rating jugador-por-jugador (atributos por posición) puede requerir scraping. Si una fuente se
  bloquea, el componente de jugadores cae elegantemente a Elo+FIFA y queda **documentado** en el
  reporte (sin romper el pipeline).
- Todos los snapshots de datos se guardan con **fecha** en `data/raw/` para reproducibilidad y para
  poder re-correr el modelo a medida que avanza el torneo.
- Las probabilidades son estimaciones de modelo; el objetivo es apoyar decisiones de quiniela, no
  garantizar resultados.

---

## 9. Criterios de éxito

1. Tabla `probabilidades_campeon.csv` con las 48 selecciones y sus probabilidades de campeón
   (+ etapas intermedias), sumando ~100%.
2. Resultados sensatos frente a la intuición y a casas de apuestas públicas (sanity check:
   los favoritos históricos —España, Francia, Argentina, Brasil, Inglaterra— deben aparecer arriba).
3. CLI por-partido funcional para reusar en cada jornada.
4. Pipeline reproducible: `fetch → ratings → simulate → report` corre de punta a punta.
