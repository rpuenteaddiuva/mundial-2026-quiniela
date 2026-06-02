# src/bracket_2026.py
"""Cuadro de eliminatorias (Ronda de 32) del Mundial 2026, formato de 48 equipos.

Cada slot del cuadro es:
  - "1X" : ganador del grupo X (A..L)
  - "2X" : segundo del grupo X (A..L)
  - "3rd:n" : el n-ésimo mejor tercero (por ranking 0..7), asignado a un hueco.

SLOT_ORDER lista los 32 slots en orden de llave del cuadro: la primera llave es
SLOT_ORDER[0] vs SLOT_ORDER[1], la segunda SLOT_ORDER[2] vs SLOT_ORDER[3], etc.
Corresponde al orden oficial de partidos de la Ronda de 32 (M73..M88):
  M73(2A-2B), M74(1E-3ro), M75(1F-2C), M76(1C-2F), M77(1I-3ro), M78(2E-2I),
  M79(1A-3ro), M80(1L-3ro), M81(1D-3ro), M82(1G-3ro), M83(2K-2L), M84(1H-2J),
  M85(1B-3ro), M86(1J-2H), M87(1K-3ro), M88(2D-2G).
Total: 12 ganadores (1A-1L), 12 segundos (2A-2L) y 8 terceros.

Estructura del cuadro (qué slot va en cada llave) verificada con alta confianza
desde Wikipedia "2026 FIFA World Cup knockout stage", FIFA.com y prensa
(Sky Sports, ESPN). Fuentes:
  https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_knockout_stage
  https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/knockout-stage-match-schedule-bracket
"""

SLOT_ORDER = [
    "2A", "2B",       # M73
    "1E", "3rd:0",    # M74
    "1F", "2C",       # M75
    "1C", "2F",       # M76
    "1I", "3rd:1",    # M77
    "2E", "2I",       # M78
    "1A", "3rd:2",    # M79
    "1L", "3rd:3",    # M80
    "1D", "3rd:4",    # M81
    "1G", "3rd:5",    # M82
    "2K", "2L",       # M83
    "1H", "2J",       # M84
    "1B", "3rd:6",    # M85
    "1J", "2H",       # M86
    "1K", "3rd:7",    # M87
    "2D", "2G",       # M88
]

# THIRD_ASSIGNMENT — descripción de cómo se asignan los 8 mejores terceros a los
# huecos del cuadro.
#
# FIFA define 8 huecos para terceros en el cuadro (partidos 74, 77, 79, 80, 81,
# 82, 85 y 87 de la Ronda de 32), cada uno enfrentado a un ganador de grupo. Los
# 8 mejores terceros se ordenan en una tabla única de clasificación (puntos,
# diferencia de goles, goles a favor, etc.). La asignación del tercero concreto a
# cada hueco NO es libre: depende de CUÁLES 8 de los 12 grupos (A..L) produjeron
# un tercero clasificado. Como C(12,8)=495, FIFA publicó en el Anexo C de la
# reglamentación una tabla con las 495 combinaciones posibles; cada fila indica
# qué letra de grupo va a cada partido, garantizando que ningún tercero enfrente
# al ganador de su propio grupo y respetando las restricciones de cada hueco
# (cada partido solo admite terceros de un subconjunto fijo de grupos:
#   M74 = 3ro de A/B/C/D/F
#   M77 = C/D/F/G/H
#   M79 = C/E/F/H/I
#   M80 = E/H/I/J/K
#   M81 = B/E/F/I/J
#   M82 = A/E/H/I/J
#   M85 = E/F/G/I/J
#   M87 = D/E/I/J/L
# ).
#
# APROXIMACIÓN USADA AQUÍ: como no se reproduce la fila exacta del Anexo C (solo
# se conoce tras el sorteo/resultados reales), se asigna 3rd:0..3rd:7 a los
# huecos en orden de aparición en el cuadro (M74, M77, M79, M80, M81, M82, M85,
# M87); es decir, terceros en orden de ranking a los slots 3rd:n.
#
# Confianza: aproximación. Lo único aproximado es CUÁL tercero por ranking
# (3rd:0..7) cae en cada hueco, porque la fila exacta del Anexo C (495
# combinaciones) solo se determina con los grupos reales clasificados. Su efecto
# sobre la probabilidad de campeón es de segundo orden.
THIRD_ASSIGNMENT = (
    "Aproximacion: los 8 mejores terceros (ranking 0..7) se asignan a los huecos "
    "del cuadro en orden de aparicion (M74, M77, M79, M80, M81, M82, M85, M87). "
    "La fila exacta del Anexo C de FIFA (495 combinaciones) depende de cuales 8 "
    "de los 12 grupos produjeron un tercero clasificado y solo se conoce tras los "
    "resultados reales; aqui 3rd:n mapea el n-esimo mejor tercero al n-esimo hueco."
)
