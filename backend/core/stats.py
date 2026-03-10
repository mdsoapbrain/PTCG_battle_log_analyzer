from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from backend.core.models import Match


def _pct(wins: int, n: int) -> float:
    return round((wins / n) * 100.0, 2) if n else 0.0


def _base_match_query(user_id: str | None = None):
    stmt = select(Match)
    if user_id:
        stmt = stmt.where(Match.user_id == user_id)
    return stmt


def compute_overview(db: Session, user_id: str | None = None) -> dict:
    stmt = select(
        func.count(Match.id),
        func.sum(case((Match.result == "win", 1), else_=0)),
        func.avg(Match.prize_diff),
        func.avg(Match.turn_count),
    )
    if user_id:
        stmt = stmt.where(Match.user_id == user_id)

    total, wins, avg_prize_diff, avg_turn_count = db.execute(stmt).one()
    total = int(total or 0)
    wins = int(wins or 0)
    losses = max(total - wins, 0)

    go_first = compute_go_first(db, user_id)

    return {
        "total_matches": total,
        "wins": wins,
        "losses": losses,
        "win_rate": _pct(wins, total),
        "average_prize_differential": float(avg_prize_diff or 0.0),
        "average_turn_count": float(avg_turn_count or 0.0),
        "go_first_win_rate": go_first["first_win_rate"],
        "go_second_win_rate": go_first["second_win_rate"],
        "recent_trend": compute_recent_trend(db, user_id),
    }


def compute_go_first(db: Session, user_id: str | None = None) -> dict:
    stmt = select(
        Match.went_first,
        func.count(Match.id),
        func.sum(case((Match.result == "win", 1), else_=0)),
    ).group_by(Match.went_first)
    if user_id:
        stmt = stmt.where(Match.user_id == user_id)

    rows = db.execute(stmt).all()

    first_matches = first_wins = second_matches = second_wins = 0
    for went_first, matches, wins in rows:
        if went_first is True:
            first_matches = int(matches or 0)
            first_wins = int(wins or 0)
        elif went_first is False:
            second_matches = int(matches or 0)
            second_wins = int(wins or 0)

    return {
        "first_matches": first_matches,
        "first_wins": first_wins,
        "first_win_rate": _pct(first_wins, first_matches),
        "second_matches": second_matches,
        "second_wins": second_wins,
        "second_win_rate": _pct(second_wins, second_matches),
    }


def compute_by_deck(db: Session, user_id: str | None = None) -> list[dict]:
    stmt = select(
        func.coalesce(func.nullif(Match.player_deck, ""), "Unknown").label("deck_name"),
        func.count(Match.id).label("matches"),
        func.sum(case((Match.result == "win", 1), else_=0)).label("wins"),
        func.avg(Match.turn_count).label("avg_turn_count"),
        func.avg(Match.prize_diff).label("avg_prize_diff"),
    ).group_by("deck_name").order_by(func.count(Match.id).desc())
    if user_id:
        stmt = stmt.where(Match.user_id == user_id)

    rows = db.execute(stmt).all()
    results: list[dict] = []
    for row in rows:
        matches = int(row.matches or 0)
        wins = int(row.wins or 0)
        results.append(
            {
                "deck_name": row.deck_name,
                "matches": matches,
                "wins": wins,
                "win_rate": _pct(wins, matches),
                "avg_turn_count": float(row.avg_turn_count or 0.0),
                "avg_prize_diff": float(row.avg_prize_diff or 0.0),
            }
        )
    return results


def compute_by_matchup(db: Session, user_id: str | None = None) -> list[dict]:
    stmt = select(
        func.coalesce(func.nullif(Match.player_deck, ""), "Unknown").label("player_deck"),
        func.coalesce(func.nullif(Match.opponent_deck, ""), "Unknown").label("opponent_deck"),
        func.count(Match.id).label("matches"),
        func.sum(case((Match.result == "win", 1), else_=0)).label("wins"),
        func.avg(Match.turn_count).label("avg_turn_count"),
        func.avg(Match.prize_diff).label("avg_prize_diff"),
    ).group_by("player_deck", "opponent_deck").order_by(func.count(Match.id).desc())
    if user_id:
        stmt = stmt.where(Match.user_id == user_id)

    rows = db.execute(stmt).all()
    results: list[dict] = []
    for row in rows:
        matches = int(row.matches or 0)
        wins = int(row.wins or 0)
        results.append(
            {
                "player_deck": row.player_deck,
                "opponent_deck": row.opponent_deck,
                "matches": matches,
                "wins": wins,
                "win_rate": _pct(wins, matches),
                "avg_turn_count": float(row.avg_turn_count or 0.0),
                "avg_prize_diff": float(row.avg_prize_diff or 0.0),
            }
        )
    return results


def compute_recent_trend(db: Session, user_id: str | None = None, days: int = 14) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = select(Match.created_at, Match.result).where(Match.created_at >= cutoff)
    if user_id:
        stmt = stmt.where(Match.user_id == user_id)

    rows = db.execute(stmt).all()
    daily: dict[str, dict[str, int]] = defaultdict(lambda: {"matches": 0, "wins": 0})
    for created_at, result in rows:
        day = created_at.date().isoformat()
        daily[day]["matches"] += 1
        if result == "win":
            daily[day]["wins"] += 1

    trend = []
    for day in sorted(daily):
        matches = daily[day]["matches"]
        wins = daily[day]["wins"]
        trend.append({"date": day, "matches": matches, "wins": wins, "win_rate": _pct(wins, matches)})
    return trend
