from __future__ import annotations

from pathlib import Path

from backend.core.database import SessionLocal, init_db
from backend.core.schemas import MatchCreateRequest
from backend.services.match_service import MatchService


def main() -> None:
    init_db()
    base_log = Path("backend/demo_assets/sample_raw_log.txt").read_text(encoding="utf-8")

    demo_payloads = [
        MatchCreateRequest(
            raw_log=base_log,
            player_name="Neurologist2024",
            player_deck="Teal Mask Ogerpon ex",
            opponent_deck="Charizard ex",
            notes="seed data 1",
        ),
        MatchCreateRequest(
            raw_log=base_log.replace("No Benched Pokémon for backup. Neurologist2024 wins.", "Opponent conceded. Neurologist2024 wins."),
            player_name="Neurologist2024",
            player_deck="Teal Mask Ogerpon ex",
            opponent_deck="Raging Bolt ex",
            notes="seed data 2",
        ),
        MatchCreateRequest(
            raw_log=base_log.replace("Neurologist2024 wins.", "Rival123 wins."),
            player_name="Neurologist2024",
            player_deck="Teal Mask Ogerpon ex",
            opponent_deck="Garchomp ex",
            notes="seed data 3",
        ),
    ]

    with SessionLocal() as db:
        svc = MatchService(db)
        for payload in demo_payloads:
            created = svc.create_match(payload, user_id="local-user")
            print(f"seeded match: {created.match_id} ({created.result})")


if __name__ == "__main__":
    main()
