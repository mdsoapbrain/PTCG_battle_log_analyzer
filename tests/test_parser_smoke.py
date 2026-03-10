from __future__ import annotations

from backend.core.parser import parse_log


def test_parse_log_smoke() -> None:
    raw = """Setup
Opp won the coin toss.
Opp decided to go first.
[playerName]'s Turn
Opp drew a card.
[playerName]'s Turn
Opponent conceded. Neurologist2024 wins.
"""
    parsed = parse_log(raw, you_name="Neurologist2024")

    assert parsed["opp_name"] == "Opp"
    assert parsed["winner"] == "You"
    assert parsed["total_turns"] == 2
