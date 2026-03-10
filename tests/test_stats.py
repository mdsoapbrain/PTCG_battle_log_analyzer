from __future__ import annotations

from backend.core.schemas import MatchCreateRequest
from backend.core.stats import compute_overview
from backend.services.match_service import MatchService


def test_stats_overview(db_session) -> None:
    service = MatchService(db_session)
    service.create_match(
        MatchCreateRequest(
            raw_log="""Setup
A won the coin toss.
A decided to go first.
[playerName]'s Turn
Opponent conceded. Neurologist2024 wins.
""",
            player_name="Neurologist2024",
            player_deck="DeckA",
            opponent_deck="DeckX",
        ),
        user_id="local-user",
    )
    service.create_match(
        MatchCreateRequest(
            raw_log="""Setup
B won the coin toss.
B decided to go first.
[playerName]'s Turn
All Prize cards taken. B wins.
""",
            player_name="Neurologist2024",
            player_deck="DeckA",
            opponent_deck="DeckY",
        ),
        user_id="local-user",
    )

    overview = compute_overview(db_session, user_id="local-user")
    assert overview["total_matches"] == 2
    assert overview["wins"] == 1
    assert overview["win_rate"] == 50.0
