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
