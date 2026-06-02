# tests/test_bracket.py
from src.bracket_2026 import SLOT_ORDER
def test_slot_order_has_32_unique_slots():
    assert len(SLOT_ORDER) == 32
    winners = [s for s in SLOT_ORDER if s.startswith("1")]
    thirds = [s for s in SLOT_ORDER if s.startswith("3rd:")]
    assert len(winners) == 12
    assert len(thirds) == 8
