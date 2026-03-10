"""initial schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-03-11
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("external_auth_id", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "decks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("archetype", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_decks_name", "decks", ["name"])

    op.create_table(
        "matches",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_log", sa.Text(), nullable=False),
        sa.Column("player_name", sa.String(length=120), nullable=False),
        sa.Column("opponent_name", sa.String(length=120), nullable=True),
        sa.Column("player_deck", sa.String(length=200), nullable=True),
        sa.Column("opponent_deck", sa.String(length=200), nullable=True),
        sa.Column("went_first", sa.Boolean(), nullable=True),
        sa.Column("result", sa.String(length=20), nullable=False),
        sa.Column("turn_count", sa.Integer(), nullable=False),
        sa.Column("prizes_taken", sa.Integer(), nullable=False),
        sa.Column("prizes_lost", sa.Integer(), nullable=False),
        sa.Column("prize_diff", sa.Integer(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=True),
    )
    op.create_index("ix_matches_created_at", "matches", ["created_at"])
    op.create_index("ix_matches_opponent_deck", "matches", ["opponent_deck"])
    op.create_index("ix_matches_opponent_name", "matches", ["opponent_name"])
    op.create_index("ix_matches_player_deck", "matches", ["player_deck"])
    op.create_index("ix_matches_player_name", "matches", ["player_name"])
    op.create_index("ix_matches_result", "matches", ["result"])
    op.create_index("ix_matches_user_id", "matches", ["user_id"])
    op.create_index("ix_matches_went_first", "matches", ["went_first"])

    op.create_table(
        "turns",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("match_id", sa.String(length=36), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("turn_number", sa.Integer(), nullable=False),
        sa.Column("acting_player", sa.String(length=20), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("extracted_summary", sa.Text(), nullable=True),
    )
    op.create_index("ix_turns_match_id", "turns", ["match_id"])
    op.create_index("ix_turns_turn_number", "turns", ["turn_number"])

    op.create_table(
        "events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("match_id", sa.String(length=36), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("turn_id", sa.String(length=36), sa.ForeignKey("turns.id"), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("actor", sa.String(length=20), nullable=True),
        sa.Column("target", sa.String(length=200), nullable=True),
        sa.Column("card_name", sa.String(length=200), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("detail_text", sa.Text(), nullable=False),
    )
    op.create_index("ix_events_actor", "events", ["actor"])
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_match_id", "events", ["match_id"])
    op.create_index("ix_events_turn_id", "events", ["turn_id"])


def downgrade() -> None:
    op.drop_index("ix_events_turn_id", table_name="events")
    op.drop_index("ix_events_match_id", table_name="events")
    op.drop_index("ix_events_event_type", table_name="events")
    op.drop_index("ix_events_actor", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_turns_turn_number", table_name="turns")
    op.drop_index("ix_turns_match_id", table_name="turns")
    op.drop_table("turns")

    op.drop_index("ix_matches_went_first", table_name="matches")
    op.drop_index("ix_matches_user_id", table_name="matches")
    op.drop_index("ix_matches_result", table_name="matches")
    op.drop_index("ix_matches_player_name", table_name="matches")
    op.drop_index("ix_matches_player_deck", table_name="matches")
    op.drop_index("ix_matches_opponent_name", table_name="matches")
    op.drop_index("ix_matches_opponent_deck", table_name="matches")
    op.drop_index("ix_matches_created_at", table_name="matches")
    op.drop_table("matches")

    op.drop_index("ix_decks_name", table_name="decks")
    op.drop_table("decks")

    op.drop_table("users")
