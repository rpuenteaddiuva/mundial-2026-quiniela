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
