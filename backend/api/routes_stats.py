from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.core.auth_stub import AuthUser, get_current_user_stub
from backend.core.database import get_db
from backend.core.schemas import ApiResponse
from backend.services.stats_service import StatsService
from backend.utils.responses import success_response


router = APIRouter(prefix="/stats", tags=["stats"])


@router.get(
    "/overview",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Overview statistics",
    description="Returns top-level match statistics including win rate, average turns, prize differential, and recent trend.",
    responses={
        200: {
            "description": "Overview stats response.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Overview stats fetched successfully.",
                        "data": {
                            "total_matches": 12,
                            "wins": 8,
                            "losses": 4,
                            "win_rate": 66.67,
                            "average_prize_differential": 1.25,
                            "average_turn_count": 8.4,
                            "go_first_win_rate": 71.4,
                            "go_second_win_rate": 60.0,
                            "recent_trend": [{"date": "2026-03-10", "matches": 3, "wins": 2, "win_rate": 66.67}],
                        },
                        "pagination": None,
                        "error": None,
                    }
                }
            },
        }
    },
)
def stats_overview(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user_stub),
) -> ApiResponse:
    payload = StatsService(db).overview(user_id=user.user_id)
    return success_response(message="Overview stats fetched successfully.", data=payload.model_dump(mode="json"))


@router.get(
    "/go-first",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Go-first vs go-second statistics",
    description="Returns split metrics for matches where the player went first vs second.",
    responses={
        200: {
            "description": "First/second split response.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Go-first stats fetched successfully.",
                        "data": {
                            "first_matches": 7,
                            "first_wins": 5,
                            "first_win_rate": 71.43,
                            "second_matches": 5,
                            "second_wins": 3,
                            "second_win_rate": 60.0,
                        },
                        "pagination": None,
                        "error": None,
                    }
                }
            },
        }
    },
)
def stats_go_first(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user_stub),
) -> ApiResponse:
    payload = StatsService(db).go_first(user_id=user.user_id)
    return success_response(message="Go-first stats fetched successfully.", data=payload.model_dump(mode="json"))


@router.get(
    "/by-deck",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Statistics by player deck",
    description="Returns win rate, average turns, and prize differential grouped by player deck.",
    responses={200: {"description": "Deck grouped stats response."}},
)
def stats_by_deck(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user_stub),
) -> ApiResponse:
    payload = StatsService(db).by_deck(user_id=user.user_id)
    return success_response(message="Deck stats fetched successfully.", data=payload.model_dump(mode="json"))


@router.get(
    "/by-matchup",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Statistics by matchup",
    description="Returns grouped performance by (player_deck, opponent_deck).",
    responses={200: {"description": "Matchup grouped stats response."}},
)
def stats_by_matchup(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user_stub),
) -> ApiResponse:
    payload = StatsService(db).by_matchup(user_id=user.user_id)
    return success_response(message="Matchup stats fetched successfully.", data=payload.model_dump(mode="json"))
