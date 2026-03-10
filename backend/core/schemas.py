from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Literal


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class ApiError(BaseModel):
    code: str
    detail: str


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Any | None = None
    pagination: PaginationMeta | None = None
    error: ApiError | None = None


class MatchEvent(BaseModel):
    turn_index: int
    active_player: str
    event_type: str
    detail_text: str
    pokemon_involved: str | None = None
    damage: int | None = None
    prize_delta_you: int = 0
    prize_delta_opp: int = 0
    is_turning_point: bool = False


class TurnSummary(BaseModel):
    turn_index: int
    active_player: str | None = None
    prize_delta_you: int = 0
    prize_delta_opp: int = 0
    events: list[MatchEvent] = Field(default_factory=list)


class ParseLogRequest(BaseModel):
    raw_log: str = Field(..., description="Raw PTCG Live battle log text")
    player_name: str = Field(default="Neurologist2024", description="Your in-game player name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "player_name": "Neurologist2024",
                "raw_log": "Setup\nOpponent won the coin toss.\nOpponent decided to go first.\n[playerName]'s Turn\nOpponent conceded. Neurologist2024 wins.",
            }
        }
    )


class ParseLogResponse(BaseModel):
    player_name: str
    opponent_name: str
    winner: str
    went_first: bool | None
    first_player_name: str | None
    total_turns: int
    prizes_taken: int
    prizes_lost: int
    first_ko_by: str
    turning_points: list[dict[str, Any]] = Field(default_factory=list)
    turns: list[TurnSummary] = Field(default_factory=list)
    timeline_markdown: str
    prize_table_markdown: str
    competitive_summary_markdown: str


class MatchCreateRequest(BaseModel):
    raw_log: str = Field(..., description="Raw PTCG Live battle log text")
    player_name: str = Field(default="Neurologist2024", description="Your in-game player name")
    player_deck: str | None = Field(default=None, description="Optional deck name for player")
    opponent_deck: str | None = Field(default=None, description="Optional deck name for opponent")
    notes: str | None = Field(default=None, description="Optional note")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "player_name": "Neurologist2024",
                "player_deck": "Teal Mask Ogerpon ex",
                "opponent_deck": "Garchomp ex",
                "raw_log": "Setup\nOpponent won the coin toss.\nOpponent decided to go first.\n[playerName]'s Turn\nNo Benched Pokémon for backup. Neurologist2024 wins.",
                "notes": "Imported from ranked ladder",
            }
        }
    )


class MatchResponse(BaseModel):
    match_id: str
    created_at: datetime
    player_name: str
    opponent_name: str
    player_deck: str | None = None
    opponent_deck: str | None = None
    went_first: bool | None = None
    result: Literal["win", "loss", "unknown"]
    turn_count: int
    prizes_taken: int
    prizes_lost: int
    prize_diff: int
    winner: str
    summary_text: str | None = None
    turns: list[TurnSummary] = Field(default_factory=list)


class MatchListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[MatchResponse]


class StatsOverviewResponse(BaseModel):
    total_matches: int
    wins: int
    losses: int
    win_rate: float
    average_prize_differential: float
    average_turn_count: float
    go_first_win_rate: float | None = None
    go_second_win_rate: float | None = None
    recent_trend: list[dict[str, Any]] = Field(default_factory=list)


class DeckStatsRow(BaseModel):
    deck_name: str
    matches: int
    wins: int
    win_rate: float
    avg_turn_count: float
    avg_prize_diff: float


class DeckStatsResponse(BaseModel):
    rows: list[DeckStatsRow]


class MatchupStatsRow(BaseModel):
    player_deck: str
    opponent_deck: str
    matches: int
    wins: int
    win_rate: float
    avg_turn_count: float
    avg_prize_diff: float


class MatchupStatsResponse(BaseModel):
    rows: list[MatchupStatsRow]


class GoFirstStatsResponse(BaseModel):
    first_matches: int
    first_wins: int
    first_win_rate: float
    second_matches: int
    second_wins: int
    second_win_rate: float


class ErrorResponse(BaseModel):
    detail: str
