from __future__ import annotations

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.schemas import ApiResponse, ParseLogRequest, ParseLogResponse
from backend.services.match_service import MatchService
from backend.utils.responses import success_response


router = APIRouter(tags=["parse"])


@router.post(
    "/parse-log",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse battle log without saving",
    description="Parses a raw PTCG Live battle log and returns structured summary data without writing to database.",
    responses={
        200: {
            "description": "Log parsed successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Battle log parsed successfully.",
                        "data": {
                            "player_name": "Neurologist2024",
                            "opponent_name": "Rival123",
                            "winner": "You",
                            "went_first": False,
                            "total_turns": 7,
                        },
                        "pagination": None,
                        "error": None,
                    }
                }
            },
        }
    },
)
def parse_log_endpoint(
    payload: ParseLogRequest = Body(...),
    db: Session = Depends(get_db),
) -> ApiResponse:
    service = MatchService(db)
    parsed: ParseLogResponse = service.parse_only(payload)
    return success_response(message="Battle log parsed successfully.", data=parsed.model_dump())
