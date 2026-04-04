from __future__ import annotations

from sqlalchemy import select

from backend.core.models import Match
from backend.core.schemas import MatchCreateRequest
from backend.repositories.match_repository import MatchRepository
from backend.services.match_service import MatchService


def test_repair_saved_matches_recomputes_match_fields(db_session) -> None:
    service = MatchService(db_session)
    created = service.create_match(
        MatchCreateRequest(
            raw_log="""Setup
Rival won the coin toss.
Rival decided to go first.
[playerName]'s Turn
Opponent conceded. Neurologist2024 wins.
""",
            player_name="Neurologist2024",
            player_deck="Ogerpon",
            opponent_deck="Charizard",
        ),
        user_id="local-user",
    )

    match = db_session.execute(select(Match).where(Match.id == created.match_id)).scalar_one()
    match.result = "loss"
    match.went_first = True
    match.opponent_name = "WrongName"
    match.turn_count = 99
    match.summary_text = "broken"
    db_session.commit()

    repaired = MatchRepository(db_session).repair_saved_matches()
    repaired_match = db_session.execute(select(Match).where(Match.id == created.match_id)).scalar_one()

    assert repaired == 1
    assert repaired_match.result == "win"
    assert repaired_match.went_first is False
    assert repaired_match.opponent_name == "Rival"
    assert repaired_match.turn_count == 1
    assert "Winner: You" in (repaired_match.summary_text or "")
