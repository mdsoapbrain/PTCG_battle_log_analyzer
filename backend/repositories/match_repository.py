from __future__ import annotations

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from backend.core.models import Event, Match, Turn


class MatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_match(
        self,
        *,
        user_id: str,
        source_log: str,
        parsed: dict,
        player_deck: str | None,
        opponent_deck: str | None,
        summary_text: str,
    ) -> Match:
        result = "unknown"
        if parsed.get("winner") == "You":
            result = "win"
        elif parsed.get("winner") == "Opp":
            result = "loss"

        match = Match(
            user_id=user_id,
            source_log=source_log,
            player_name=parsed.get("you_name", "Unknown"),
            opponent_name=parsed.get("opp_name", "Unknown"),
            player_deck=player_deck,
            opponent_deck=opponent_deck,
            went_first=(True if parsed.get("you_go_first") == 1 else False if parsed.get("you_go_first") == 0 else None),
            result=result,
            turn_count=int(parsed.get("total_turns", 0)),
            prizes_taken=int(parsed.get("you_prize_taken", 0)),
            prizes_lost=int(parsed.get("opp_prize_taken", 0)),
            prize_diff=int(parsed.get("you_prize_taken", 0)) - int(parsed.get("opp_prize_taken", 0)),
            summary_text=summary_text,
        )
        self.db.add(match)
        self.db.flush()

        turn_id_map: dict[int, str] = {}
        for turn in parsed.get("turns", []):
            raw_text = "\n".join(e.get("detail_text", "") for e in turn.get("events", []))
            turn_obj = Turn(
                match_id=match.id,
                turn_number=int(turn.get("turn_index", 0)),
                acting_player=turn.get("active_player"),
                raw_text=raw_text,
                extracted_summary=raw_text,
            )
            self.db.add(turn_obj)
            self.db.flush()
            turn_id_map[int(turn.get("turn_index", 0))] = turn_obj.id

        for turn in parsed.get("turns", []):
            turn_index = int(turn.get("turn_index", 0))
            for event in turn.get("events", []):
                self.db.add(
                    Event(
                        match_id=match.id,
                        turn_id=turn_id_map.get(turn_index),
                        event_type=event.get("event_type", "other"),
                        actor=turn.get("active_player") or "Unknown",
                        target=event.get("pokemon_involved"),
                        card_name=None,
                        value=float(event["damage"]) if event.get("damage") is not None else None,
                        metadata_json={
                            "prize_delta_you": int(event.get("prize_delta_you", 0)),
                            "prize_delta_opp": int(event.get("prize_delta_opp", 0)),
                            "is_turning_point": bool(event.get("is_turning_point", False)),
                        },
                        detail_text=event.get("detail_text", ""),
                    )
                )

        self.db.commit()
        self.db.refresh(match)
        return match

    def list_matches(
        self,
        *,
        page: int,
        page_size: int,
        player_deck: str | None,
        opponent_deck: str | None,
        result: str | None,
    ) -> tuple[int, list[Match]]:
        filters = []
        if player_deck:
            filters.append(Match.player_deck == player_deck)
        if opponent_deck:
            filters.append(Match.opponent_deck == opponent_deck)
        if result:
            filters.append(Match.result == result)

        query = select(Match)
        count_query = select(func.count(Match.id))
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        total = int(self.db.execute(count_query).scalar() or 0)
        items = self.db.execute(
            query.order_by(Match.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        ).scalars().all()
        return total, items

    def get_match(self, match_id: str) -> Match | None:
        return self.db.execute(select(Match).where(Match.id == match_id)).scalar_one_or_none()
