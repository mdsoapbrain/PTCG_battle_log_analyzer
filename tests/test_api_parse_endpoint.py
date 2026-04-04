from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    ("raw_log", "expected_winner", "expected_opponent", "expected_went_first"),
    [
        (
            """Setup
Rival won the coin toss.
Rival decided to go first.
[playerName]'s Turn
No Benched Pokémon for backup. Neurologist2024 wins.
""",
            "You",
            "Rival",
            False,
        ),
        (
            """Setup
Rival won the coin toss.
Rival decided to go first.
[playerName]'s Turn
Opponent conceded. Neurologist2024 wins.
""",
            "You",
            "Rival",
            False,
        ),
        (
            """Setup
Rival won the coin toss.
Rival decided to go first.
[playerName]'s Turn
Opponent was inactive for too long. Neurologist2024 wins.
""",
            "You",
            "Rival",
            False,
        ),
    ],
)
def test_parse_endpoint(client, raw_log: str, expected_winner: str, expected_opponent: str, expected_went_first: bool) -> None:
    payload = {
        "raw_log": raw_log,
        "player_name": "Neurologist2024",
    }
    resp = client.post("/parse-log", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["winner"] == expected_winner
    assert data["data"]["opponent_name"] == expected_opponent
    assert data["data"]["went_first"] is expected_went_first
