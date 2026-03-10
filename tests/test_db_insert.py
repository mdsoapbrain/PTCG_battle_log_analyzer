from __future__ import annotations

from sqlalchemy import select

from backend.core.models import Match
from backend.core.schemas import MatchCreateRequest
from backend.services.match_service import MatchService


def test_db_insert_match(db_session) -> None:
    service = MatchService(db_session)
    req = MatchCreateRequest(
        raw_log="""Setup
Rival won the coin toss.
Rival decided to go first.
[playerName]'s Turn
Opponent conceded. Neurologist2024 wins.
""",
        player_name="Neurologist2024",
        player_deck="Ogerpon",
        opponent_deck="Charizard",
    )
    created = service.create_match(req, user_id="local-user")
    assert created.match_id

    count = db_session.execute(select(Match)).scalars().all()
    assert len(count) == 1
    assert count[0].result == "win"
