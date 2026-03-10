from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.core.auth_stub import AuthUser, get_current_user_stub
from backend.core.database import get_db
from backend.core.schemas import ApiResponse, MatchCreateRequest
from backend.services.match_service import MatchService
from backend.utils.responses import paginated_response, success_response


router = APIRouter(prefix="/matches", tags=["matches"])


@router.post(
    "",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Parse and save a match",
    description="Parses a battle log, persists match/turn/event records, and returns the saved match summary.",
    responses={
        201: {
            "description": "Match saved.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Match saved successfully.",
                        "data": {
                            "match_id": "f44dc8d7-33de-4f02-8b83-0f9b5f63db7a",
                            "result": "win",
                            "player_name": "Neurologist2024",
                            "opponent_name": "Rival123",
                        },
                        "pagination": None,
                        "error": None,
                    }
                }
            },
        }
    },
)
def create_match(
    payload: MatchCreateRequest = Body(...),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user_stub),
) -> ApiResponse:
    service = MatchService(db)
    match = service.create_match(payload, user_id=user.user_id)
    return success_response(message="Match saved successfully.", data=match.model_dump(mode="json"))


@router.get(
    "",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="List matches",
    description="Returns paginated match records with optional deck/result filters.",
)
def list_matches(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=200, description="Items per page"),
    player_deck: str | None = Query(None, description="Filter by player deck name"),
    opponent_deck: str | None = Query(None, description="Filter by opponent deck name"),
    result: str | None = Query(default=None, pattern="^(win|loss|unknown)$", description="Filter by result"),
    db: Session = Depends(get_db),
) -> ApiResponse:
    service = MatchService(db)
    result_page = service.list_matches(
        page=page,
        page_size=page_size,
        player_deck=player_deck,
        opponent_deck=opponent_deck,
        result=result,
    )
    return paginated_response(
        message="Matches fetched successfully.",
        data={"items": [i.model_dump(mode="json") for i in result_page.items]},
        page=result_page.page,
        page_size=result_page.page_size,
        total=result_page.total,
    )


@router.get(
    "/{match_id}",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Get one match",
    description="Returns one match by id, including turns and events.",
    responses={
        404: {
            "description": "Match not found.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Request failed",
                        "data": None,
                        "pagination": None,
                        "error": {"code": "HTTP_404", "detail": "Match not found"},
                    }
                }
            },
        }
    },
)
def get_match(match_id: str, db: Session = Depends(get_db)) -> ApiResponse:
    service = MatchService(db)
    match = service.get_match(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return success_response(message="Match fetched successfully.", data=match.model_dump(mode="json"))
