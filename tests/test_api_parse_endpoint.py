from __future__ import annotations


def test_parse_endpoint(client) -> None:
    payload = {
        "raw_log": """Setup
Rival won the coin toss.
Rival decided to go first.
[playerName]'s Turn
No Benched Pokémon for backup. Neurologist2024 wins.
""",
        "player_name": "Neurologist2024",
    }
    resp = client.post("/parse-log", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["winner"] == "You"
    assert data["data"]["opponent_name"] == "Rival"
