from __future__ import annotations

from sqlalchemy.orm import Session

from backend.core.battle_summary import render_competitive_summary, render_prize_table, render_timeline
from backend.core.parser import parse_log
from backend.core.schemas import (
    MatchCreateRequest,
    MatchEvent,
    MatchListResponse,
    MatchResponse,
    ParseLogRequest,
    ParseLogResponse,
    TurnSummary,
)
from backend.repositories.match_repository import MatchRepository


class MatchService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MatchRepository(db)

    def parse_only(self, request: ParseLogRequest) -> ParseLogResponse:
        parsed = parse_log(request.raw_log, you_name=request.player_name)
        timeline = render_timeline(parsed)
        prize_table = render_prize_table(parsed)
        summary = render_competitive_summary(parsed)

        turns = [
            TurnSummary(
                turn_index=t["turn_index"],
                active_player=t.get("active_player"),
                prize_delta_you=t.get("prize_delta_you", 0),
                prize_delta_opp=t.get("prize_delta_opp", 0),
                events=[
                    MatchEvent(
                        turn_index=t["turn_index"],
                        active_player=t.get("active_player") or "Unknown",
                        event_type=e["event_type"],
                        detail_text=e["detail_text"],
                        pokemon_involved=e.get("pokemon_involved"),
                        damage=e.get("damage"),
                        prize_delta_you=e.get("prize_delta_you", 0),
                        prize_delta_opp=e.get("prize_delta_opp", 0),
                        is_turning_point=bool(e.get("is_turning_point", False)),
                    )
                    for e in t.get("events", [])
                ],
            )
            for t in parsed.get("turns", [])
        ]

        return ParseLogResponse(
            player_name=request.player_name,
            opponent_name=parsed.get("opp_name", "Unknown"),
            winner=parsed.get("winner", "Unknown"),
            went_first=True if parsed.get("you_go_first") == 1 else False if parsed.get("you_go_first") == 0 else None,
            first_player_name=parsed.get("first_player_name"),
            total_turns=parsed.get("total_turns", 0),
            prizes_taken=parsed.get("you_prize_taken", 0),
            prizes_lost=parsed.get("opp_prize_taken", 0),
            first_ko_by=parsed.get("first_ko_by", "Unknown"),
            turning_points=parsed.get("turning_points", []),
            turns=turns,
            timeline_markdown=timeline,
            prize_table_markdown=prize_table,
            competitive_summary_markdown=summary,
        )

    def create_match(self, request: MatchCreateRequest, user_id: str) -> MatchResponse:
        parsed = parse_log(request.raw_log, you_name=request.player_name)
        parsed["you_deck_name"] = request.player_deck
        parsed["opp_deck_name"] = request.opponent_deck

        summary = render_competitive_summary(parsed)
        match = self.repo.create_match(
            user_id=user_id,
            source_log=request.raw_log,
            parsed=parsed,
            player_deck=request.player_deck,
            opponent_deck=request.opponent_deck,
            summary_text=summary,
        )

        turns = [
            TurnSummary(
                turn_index=t["turn_index"],
                active_player=t.get("active_player"),
                prize_delta_you=t.get("prize_delta_you", 0),
                prize_delta_opp=t.get("prize_delta_opp", 0),
                events=[
                    MatchEvent(
                        turn_index=t["turn_index"],
                        active_player=t.get("active_player") or "Unknown",
                        event_type=e["event_type"],
                        detail_text=e["detail_text"],
                        pokemon_involved=e.get("pokemon_involved"),
                        damage=e.get("damage"),
                        prize_delta_you=e.get("prize_delta_you", 0),
                        prize_delta_opp=e.get("prize_delta_opp", 0),
                        is_turning_point=bool(e.get("is_turning_point", False)),
                    )
                    for e in t.get("events", [])
                ],
            )
            for t in parsed.get("turns", [])
        ]

        return MatchResponse(
            match_id=match.id,
            created_at=match.created_at,
            player_name=match.player_name,
            opponent_name=match.opponent_name or "Unknown",
            player_deck=match.player_deck,
            opponent_deck=match.opponent_deck,
            went_first=match.went_first,
            result=match.result,
            turn_count=match.turn_count,
            prizes_taken=match.prizes_taken,
            prizes_lost=match.prizes_lost,
            prize_diff=match.prize_diff,
            winner=parsed.get("winner", "Unknown"),
            summary_text=match.summary_text,
            turns=turns,
        )

    def list_matches(
        self,
        *,
        page: int,
        page_size: int,
        player_deck: str | None,
        opponent_deck: str | None,
        result: str | None,
    ) -> MatchListResponse:
        total, items = self.repo.list_matches(
            page=page,
            page_size=page_size,
            player_deck=player_deck,
            opponent_deck=opponent_deck,
            result=result,
        )
        response_items = [
            MatchResponse(
                match_id=m.id,
                created_at=m.created_at,
                player_name=m.player_name,
                opponent_name=m.opponent_name or "Unknown",
                player_deck=m.player_deck,
                opponent_deck=m.opponent_deck,
                went_first=m.went_first,
                result=m.result,
                turn_count=m.turn_count,
                prizes_taken=m.prizes_taken,
                prizes_lost=m.prizes_lost,
                prize_diff=m.prize_diff,
                winner="You" if m.result == "win" else "Opp" if m.result == "loss" else "Unknown",
                summary_text=m.summary_text,
                turns=[],
            )
            for m in items
        ]
        return MatchListResponse(page=page, page_size=page_size, total=total, items=response_items)

    def get_match(self, match_id: str) -> MatchResponse | None:
        m = self.repo.get_match(match_id)
        if not m:
            return None
        turn_summaries = [
            TurnSummary(
                turn_index=t.turn_number,
                active_player=t.acting_player,
                prize_delta_you=0,
                prize_delta_opp=0,
                events=[
                    MatchEvent(
                        turn_index=t.turn_number,
                        active_player=e.actor or "Unknown",
                        event_type=e.event_type,
                        detail_text=e.detail_text,
                        pokemon_involved=e.target,
                        damage=int(e.value) if e.value is not None else None,
                        prize_delta_you=(e.metadata_json or {}).get("prize_delta_you", 0),
                        prize_delta_opp=(e.metadata_json or {}).get("prize_delta_opp", 0),
                        is_turning_point=bool((e.metadata_json or {}).get("is_turning_point", False)),
                    )
                    for e in t.events
                ],
            )
            for t in sorted(m.turns, key=lambda x: x.turn_number)
        ]
        return MatchResponse(
            match_id=m.id,
            created_at=m.created_at,
            player_name=m.player_name,
            opponent_name=m.opponent_name or "Unknown",
            player_deck=m.player_deck,
            opponent_deck=m.opponent_deck,
            went_first=m.went_first,
            result=m.result,
            turn_count=m.turn_count,
            prizes_taken=m.prizes_taken,
            prizes_lost=m.prizes_lost,
            prize_diff=m.prize_diff,
            winner="You" if m.result == "win" else "Opp" if m.result == "loss" else "Unknown",
            summary_text=m.summary_text,
            turns=turn_summaries,
        )
