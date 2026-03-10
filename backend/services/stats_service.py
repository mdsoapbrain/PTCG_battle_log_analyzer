from __future__ import annotations

from sqlalchemy.orm import Session

from backend.core.schemas import DeckStatsResponse, GoFirstStatsResponse, MatchupStatsResponse, StatsOverviewResponse
from backend.core.stats import compute_by_deck, compute_by_matchup, compute_go_first, compute_overview


class StatsService:
    def __init__(self, db: Session):
        self.db = db

    def overview(self, user_id: str | None = None) -> StatsOverviewResponse:
        return StatsOverviewResponse(**compute_overview(self.db, user_id=user_id))

    def go_first(self, user_id: str | None = None) -> GoFirstStatsResponse:
        return GoFirstStatsResponse(**compute_go_first(self.db, user_id=user_id))

    def by_deck(self, user_id: str | None = None) -> DeckStatsResponse:
        return DeckStatsResponse(rows=compute_by_deck(self.db, user_id=user_id))

    def by_matchup(self, user_id: str | None = None) -> MatchupStatsResponse:
        return MatchupStatsResponse(rows=compute_by_matchup(self.db, user_id=user_id))
