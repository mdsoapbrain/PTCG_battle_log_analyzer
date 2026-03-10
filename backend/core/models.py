from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    external_auth_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str] = mapped_column(String(120), default="local-user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    matches: Mapped[list[Match]] = relationship("Match", back_populates="user", cascade="all, delete-orphan")


class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    archetype: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    source_log: Mapped[str] = mapped_column(Text)
    player_name: Mapped[str] = mapped_column(String(120), index=True)
    opponent_name: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    player_deck: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    opponent_deck: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)

    went_first: Mapped[bool | None] = mapped_column(Boolean, nullable=True, index=True)
    result: Mapped[str] = mapped_column(String(20), default="unknown", index=True)

    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    prizes_taken: Mapped[int] = mapped_column(Integer, default=0)
    prizes_lost: Mapped[int] = mapped_column(Integer, default=0)
    prize_diff: Mapped[int] = mapped_column(Integer, default=0)

    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User | None] = relationship("User", back_populates="matches")
    turns: Mapped[list[Turn]] = relationship("Turn", back_populates="match", cascade="all, delete-orphan")
    events: Mapped[list[Event]] = relationship("Event", back_populates="match", cascade="all, delete-orphan")


class Turn(Base):
    __tablename__ = "turns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    match_id: Mapped[str] = mapped_column(String(36), ForeignKey("matches.id"), index=True)
    turn_number: Mapped[int] = mapped_column(Integer, index=True)
    acting_player: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    match: Mapped[Match] = relationship("Match", back_populates="turns")
    events: Mapped[list[Event]] = relationship("Event", back_populates="turn", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    match_id: Mapped[str] = mapped_column(String(36), ForeignKey("matches.id"), index=True)
    turn_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("turns.id"), nullable=True, index=True)

    event_type: Mapped[str] = mapped_column(String(40), index=True)
    actor: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    target: Mapped[str | None] = mapped_column(String(200), nullable=True)
    card_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    detail_text: Mapped[str] = mapped_column(Text)

    match: Mapped[Match] = relationship("Match", back_populates="events")
    turn: Mapped[Turn | None] = relationship("Turn", back_populates="events")
