from __future__ import annotations

import re
import sqlite3
import uuid
import csv
import io
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Optional

try:
    import streamlit as st
except ModuleNotFoundError:  # Allow parser/DB functions to run without Streamlit installed.
    st = None


YOU_DEFAULT = "Neurologist2024"
DB_PATH = "ptcg_logs.db"
KEY_RESOURCE_CARDS = ["Unfair Stamp", "Iono", "Judge", "Prime Catcher"]
SUPPORTER_HINTS = [
    "Boss's Orders",
    "Iono",
    "Judge",
    "Professor",
    "Carmine",
    "Lillie's Determination",
    "Ciphermaniac's Codebreaking",
    "Dawn",
    "Arven",
    "Colress",
]
ABILITY_MOVE_HINTS = ["Teal Dance"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_text(text: str) -> str:
    return text.replace("\u2019", "'").replace("\u2018", "'")


def ensure_db(db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS games (
            game_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            you_name TEXT NOT NULL,
            opp_name TEXT,
            you_deck_name TEXT,
            opp_deck_name TEXT,
            winner TEXT,
            you_prize_taken INTEGER DEFAULT 0,
            opp_prize_taken INTEGER DEFAULT 0,
            total_turns INTEGER DEFAULT 0,
            first_ko_by TEXT,
            notes TEXT,
            you_go_first INTEGER,
            first_player_name TEXT,
            format_date TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            game_id TEXT NOT NULL,
            turn_index INTEGER NOT NULL,
            active_player TEXT,
            event_type TEXT NOT NULL,
            detail_text TEXT NOT NULL,
            pokemon_involved TEXT,
            damage INTEGER,
            prize_delta_you INTEGER DEFAULT 0,
            prize_delta_opp INTEGER DEFAULT 0,
            is_turning_point INTEGER DEFAULT 0,
            FOREIGN KEY (game_id) REFERENCES games(game_id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS turning_points (
            tp_id TEXT PRIMARY KEY,
            game_id TEXT NOT NULL,
            turn_index INTEGER NOT NULL,
            tp_type TEXT NOT NULL,
            description TEXT,
            you_prize_taken INTEGER DEFAULT 0,
            opp_prize_taken INTEGER DEFAULT 0,
            prize_diff INTEGER DEFAULT 0,
            FOREIGN KEY (game_id) REFERENCES games(game_id)
        )
        """
    )

    cur.execute("CREATE INDEX IF NOT EXISTS idx_games_created_at ON games(created_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_games_you_deck ON games(you_deck_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_games_opp_deck ON games(opp_deck_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_game_turn ON events(game_id, turn_index)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tp_game_turn ON turning_points(game_id, turn_index)")

    # Lightweight migrations for old schema.
    cur.execute("PRAGMA table_info(games)")
    game_cols = {row[1] for row in cur.fetchall()}
    for col_def in [
        ("you_go_first", "INTEGER"),
        ("first_player_name", "TEXT"),
        ("format_date", "TEXT"),
    ]:
        if col_def[0] not in game_cols:
            cur.execute(f"ALTER TABLE games ADD COLUMN {col_def[0]} {col_def[1]}")

    # Backfill legacy rows to avoid first/second aggregation failures.
    cur.execute("UPDATE games SET you_go_first = 1 WHERE you_go_first IS NULL")

    conn.commit()
    conn.close()


def map_player(name: Optional[str], you_name: str, opp_name: str) -> str:
    if not name:
        return "Unknown"
    if name == you_name:
        return "You"
    if name == opp_name:
        return "Opp"
    return "Unknown"


def guess_opp_name(lines: list[str], you_name: str) -> str:
    counts: Counter[str] = Counter()
    patterns = [
        re.compile(r"^([A-Za-z0-9_]+) (?:drew|played|attached|evolved|retreated|ended|chose|won|decided|shuffled|took|discarded|moved|put|used|is)") ,
        re.compile(r"^([A-Za-z0-9_]+)'s "),
        re.compile(r"All Prize cards taken\. ([A-Za-z0-9_]+) wins\.?"),
    ]
    for line in lines:
        for pat in patterns:
            m = pat.search(line)
            if m:
                name = m.group(1)
                if name != you_name:
                    counts[name] += 1
    return counts.most_common(1)[0][0] if counts else "Unknown"


def parse_log(text: str, you_name: str = YOU_DEFAULT) -> dict[str, Any]:
    raw_lines = [normalize_text(x.strip()) for x in text.splitlines() if x.strip()]
    opp_name = guess_opp_name(raw_lines, you_name)

    decided_first_re = re.compile(r"^([A-Za-z0-9_]+) decided to go first\.$")
    first_player_name = None
    for line in raw_lines:
        m = decided_first_re.match(line)
        if m:
            first_player_name = m.group(1)
            break

    if first_player_name is None:
        you_go_first: Optional[int] = None
    else:
        you_go_first = 1 if first_player_name == you_name else 0

    starting_active: dict[str, str] = {}
    active_setup_re = re.compile(r"^([A-Za-z0-9_]+) played (.+) to the Active Spot\.$")
    for line in raw_lines:
        m = active_setup_re.match(line)
        if m:
            p_name, pokemon = m.groups()
            p_key = map_player(p_name, you_name, opp_name)
            if p_key in ("You", "Opp") and p_key not in starting_active:
                starting_active[p_key] = pokemon

    turns: list[dict[str, Any]] = []
    turn_index = 0
    current_turn: Optional[dict[str, Any]] = None
    you_prize_taken = 0
    opp_prize_taken = 0
    first_ko_by = "Unknown"
    winner = "Unknown"
    first_ex_ko_ref: Optional[tuple[int, int]] = None

    turn_marker_re = re.compile(r"^([A-Za-z0-9_]+)'s Turn$")
    placeholder_turn_marker = "[playerName]'s Turn"

    def start_turn(active_player_name: Optional[str]) -> dict[str, Any]:
        nonlocal turn_index
        turn_index += 1
        active = map_player(active_player_name, you_name, opp_name)
        return {
            "turn_index": turn_index,
            "active_player": active if active != "Unknown" else None,
            "events": [],
            "prize_delta_you": 0,
            "prize_delta_opp": 0,
            "prize_start_you": you_prize_taken,
            "prize_start_opp": opp_prize_taken,
            "prize_end_you": you_prize_taken,
            "prize_end_opp": opp_prize_taken,
            "turning_point_types": [],
        }

    def infer_line_player(line: str) -> Optional[str]:
        m = re.match(r"^([A-Za-z0-9_]+)(?:'s)?\b", line)
        if not m:
            return None
        candidate = m.group(1)
        mapped = map_player(candidate, you_name, opp_name)
        if mapped in ("You", "Opp"):
            return mapped
        return None

    def add_event(
        event_type: str,
        detail_text: str,
        pokemon_involved: Optional[str] = None,
        damage: Optional[int] = None,
        prize_delta_you: int = 0,
        prize_delta_opp: int = 0,
        ko_target_owner: Optional[str] = None,
    ) -> None:
        if current_turn is None:
            return
        current_turn["events"].append(
            {
                "event_type": event_type,
                "detail_text": detail_text,
                "pokemon_involved": pokemon_involved,
                "damage": damage,
                "prize_delta_you": prize_delta_you,
                "prize_delta_opp": prize_delta_opp,
                "is_turning_point": False,
                "ko_target_owner": ko_target_owner,
                "score_you": you_prize_taken,
                "score_opp": opp_prize_taken,
            }
        )

    for line in raw_lines:
        if line == placeholder_turn_marker:
            if current_turn is not None:
                current_turn["prize_end_you"] = you_prize_taken
                current_turn["prize_end_opp"] = opp_prize_taken
                turns.append(current_turn)
            current_turn = start_turn(None)
            continue

        m_turn = turn_marker_re.match(line)
        if m_turn:
            if current_turn is not None:
                current_turn["prize_end_you"] = you_prize_taken
                current_turn["prize_end_opp"] = opp_prize_taken
                turns.append(current_turn)
            current_turn = start_turn(m_turn.group(1))
            continue

        # Winner line.
        m_win = re.match(r"All Prize cards taken\. ([A-Za-z0-9_]+) wins\.?", line)
        if m_win:
            winner = map_player(m_win.group(1), you_name, opp_name)

        if current_turn is None:
            continue

        if current_turn["active_player"] is None:
            inferred = infer_line_player(line)
            if inferred:
                current_turn["active_player"] = inferred

        # Supporter/Stadium/Item style "played ..." line.
        m_played = re.match(r"^([A-Za-z0-9_]+) played (.+)\.$", line)
        if m_played:
            player_name, card = m_played.groups()
            actor = map_player(player_name, you_name, opp_name)
            if current_turn["active_player"] is None and actor in ("You", "Opp"):
                current_turn["active_player"] = actor

            if "to the Stadium spot" in line:
                add_event("stadium", f"{actor}: {card}")
            elif "to the Bench" in line or "to the Active Spot" in line:
                add_event("other", f"{actor}: {card}")
            elif "Boss's Orders" in card:
                add_event("supporter", f"{actor}: {card}")
            elif any(hint in card for hint in SUPPORTER_HINTS):
                add_event("supporter", f"{actor}: {card}")
            elif any(k in card for k in KEY_RESOURCE_CARDS):
                add_event("item", f"{actor}: {card}")
            continue

        # Evolution line.
        m_evo = re.match(r"^([A-Za-z0-9_]+) evolved (.+) to (.+) on the (Bench|Active Spot)\.?$", line)
        if m_evo:
            player_name, src_pkm, dst_pkm, zone = m_evo.groups()
            actor = map_player(player_name, you_name, opp_name)
            add_event("evolve", f"{actor}: {src_pkm} -> {dst_pkm} ({zone})", pokemon_involved=dst_pkm)
            continue

        # Attack with direct damage text.
        m_attack_damage = re.match(
            r"^([A-Za-z0-9_]+)'s (.+) used (.+) on ([A-Za-z0-9_]+)'s (.+) for (\d+) damage\.?$",
            line,
        )
        if m_attack_damage:
            atk_player, atk_pokemon, move_name, def_player, def_pokemon, damage = m_attack_damage.groups()
            actor = map_player(atk_player, you_name, opp_name)
            detail = f"{actor}: {atk_pokemon} used {move_name} on {def_pokemon} for {damage}"
            add_event("attack", detail, pokemon_involved=f"{atk_pokemon} -> {def_pokemon}", damage=int(damage))
            continue

        # Attack with no explicit damage in same line.
        m_attack = re.match(r"^([A-Za-z0-9_]+)'s (.+) used (.+)\.?$", line)
        if m_attack:
            atk_player, atk_pokemon, move_name = m_attack.groups()
            move_name = move_name.rstrip(".").strip()
            actor = map_player(atk_player, you_name, opp_name)
            if move_name in ABILITY_MOVE_HINTS:
                add_event("ability", f"{actor}: {atk_pokemon} used {move_name}", pokemon_involved=atk_pokemon)
            else:
                add_event("attack", f"{actor}: {atk_pokemon} used {move_name}", pokemon_involved=atk_pokemon)
            continue

        # Explicit damage line (some moves split to next line).
        m_took_damage = re.match(r"^([A-Za-z0-9_]+)'s (.+) took (\d+) damage\.?$", line)
        if m_took_damage:
            dmg_owner, dmg_target, dmg = m_took_damage.groups()
            target_owner = map_player(dmg_owner, you_name, opp_name)
            add_event("attack", f"Damage: {dmg_target} ({target_owner}) took {dmg}", pokemon_involved=dmg_target, damage=int(dmg))
            continue

        # KO.
        m_ko = re.match(r"^([A-Za-z0-9_]+)'s (.+) was Knocked Out!$", line)
        if m_ko:
            target_owner_name, target_pokemon = m_ko.groups()
            ko_target_owner = map_player(target_owner_name, you_name, opp_name)
            add_event(
                "ko",
                f"KO: {target_pokemon} ({ko_target_owner})",
                pokemon_involved=target_pokemon,
                ko_target_owner=ko_target_owner,
            )
            if first_ko_by == "Unknown":
                first_ko_by = current_turn["active_player"] or "Unknown"
            if first_ex_ko_ref is None and "ex" in target_pokemon.lower():
                first_ex_ko_ref = (len(turns), len(current_turn["events"]) - 1)
            continue

        # Prize.
        m_prize_1 = re.match(r"^([A-Za-z0-9_]+) took a Prize card\.$", line)
        m_prize_2 = re.match(r"^([A-Za-z0-9_]+) took (\d+) Prize cards\.$", line)
        if m_prize_1 or m_prize_2:
            prize_player = m_prize_1.group(1) if m_prize_1 else m_prize_2.group(1)
            prize_count = 1 if m_prize_1 else int(m_prize_2.group(2))
            mapped = map_player(prize_player, you_name, opp_name)

            delta_you = prize_count if mapped == "You" else 0
            delta_opp = prize_count if mapped == "Opp" else 0
            you_prize_taken += delta_you
            opp_prize_taken += delta_opp
            current_turn["prize_delta_you"] += delta_you
            current_turn["prize_delta_opp"] += delta_opp
            add_event(
                "prize",
                f"Prize: {mapped} +{prize_count}",
                prize_delta_you=delta_you,
                prize_delta_opp=delta_opp,
            )
            current_turn["events"][-1]["score_you"] = you_prize_taken
            current_turn["events"][-1]["score_opp"] = opp_prize_taken
            continue

        # Key resources in any other line.
        if any(card in line for card in KEY_RESOURCE_CARDS):
            add_event("item", f"Key resource: {line}")

    if current_turn is not None:
        current_turn["prize_end_you"] = you_prize_taken
        current_turn["prize_end_opp"] = opp_prize_taken
        turns.append(current_turn)

    if winner == "Unknown":
        if you_prize_taken >= 6 and you_prize_taken >= opp_prize_taken:
            winner = "You"
        elif opp_prize_taken >= 6 and opp_prize_taken >= you_prize_taken:
            winner = "Opp"

    turning_points: list[dict[str, Any]] = []

    # Turning point 1: largest prize swing turn.
    max_swing = 0
    max_swing_turn: Optional[dict[str, Any]] = None
    for t in turns:
        swing = t["prize_delta_you"] - t["prize_delta_opp"]
        if abs(swing) > abs(max_swing):
            max_swing = swing
            max_swing_turn = t

    if max_swing_turn is not None and max_swing != 0:
        tp_desc = f"Largest prize swing in Turn {max_swing_turn['turn_index']} (net {max_swing:+d})"
        turning_points.append(
            {
                "tp_type": "prize_swing",
                "turn_index": max_swing_turn["turn_index"],
                "description": tp_desc,
                "you_prize_taken": max_swing_turn["prize_end_you"],
                "opp_prize_taken": max_swing_turn["prize_end_opp"],
                "prize_diff": max_swing_turn["prize_end_you"] - max_swing_turn["prize_end_opp"],
            }
        )
        max_swing_turn["turning_point_types"].append("prize_swing")
        for event in max_swing_turn["events"]:
            if event["event_type"] == "prize":
                event["is_turning_point"] = True

    # Turning point 2: first ex KO.
    if first_ex_ko_ref is not None and len(turning_points) < 2:
        turn_list_index, event_index = first_ex_ko_ref
        if 0 <= turn_list_index < len(turns):
            turn_obj = turns[turn_list_index]
            if 0 <= event_index < len(turn_obj["events"]):
                ko_event = turn_obj["events"][event_index]
                ko_event["is_turning_point"] = True
                tp_desc = f"First ex KO in Turn {turn_obj['turn_index']}: {ko_event['detail_text']}"
                turning_points.append(
                    {
                        "tp_type": "ex_ko",
                        "turn_index": turn_obj["turn_index"],
                        "description": tp_desc,
                        "you_prize_taken": ko_event.get("score_you", turn_obj["prize_end_you"]),
                        "opp_prize_taken": ko_event.get("score_opp", turn_obj["prize_end_opp"]),
                        "prize_diff": ko_event.get("score_you", 0) - ko_event.get("score_opp", 0),
                    }
                )
                turn_obj["turning_point_types"].append("ex_ko")

    return {
        "you_name": you_name,
        "opp_name": opp_name,
        "first_player_name": first_player_name,
        "you_go_first": you_go_first,
        "winner": winner,
        "you_prize_taken": you_prize_taken,
        "opp_prize_taken": opp_prize_taken,
        "score_text": f"{winner} wins {max(you_prize_taken, opp_prize_taken)}-{min(you_prize_taken, opp_prize_taken)}"
        if winner in ("You", "Opp")
        else f"You {you_prize_taken} - Opp {opp_prize_taken}",
        "total_turns": len(turns),
        "first_ko_by": first_ko_by,
        "turns": turns,
        "turning_points": turning_points[:2],
        "starting_active": {
            "You": starting_active.get("You", "Unknown"),
            "Opp": starting_active.get("Opp", "Unknown"),
        },
    }


def build_events(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for turn in parsed["turns"]:
        active = turn["active_player"] or "Unknown"
        for event in turn["events"]:
            flattened.append(
                {
                    "event_id": str(uuid.uuid4()),
                    "turn_index": turn["turn_index"],
                    "active_player": active,
                    "event_type": event["event_type"],
                    "detail_text": event["detail_text"],
                    "pokemon_involved": event.get("pokemon_involved"),
                    "damage": event.get("damage"),
                    "prize_delta_you": event.get("prize_delta_you", 0),
                    "prize_delta_opp": event.get("prize_delta_opp", 0),
                    "is_turning_point": 1 if event.get("is_turning_point") else 0,
                }
            )
    return flattened


def save_game_and_events(db_path: str, parsed: dict[str, Any]) -> str:
    ensure_db(db_path)
    game_id = str(uuid.uuid4())

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO games (
            game_id, created_at, you_name, opp_name, you_deck_name, opp_deck_name,
            winner, you_prize_taken, opp_prize_taken, total_turns, first_ko_by, notes,
            you_go_first, first_player_name, format_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            game_id,
            utc_now_iso(),
            parsed["you_name"],
            parsed["opp_name"],
            parsed.get("you_deck_name"),
            parsed.get("opp_deck_name"),
            parsed.get("winner"),
            parsed.get("you_prize_taken", 0),
            parsed.get("opp_prize_taken", 0),
            parsed.get("total_turns", 0),
            parsed.get("first_ko_by"),
            parsed.get("notes"),
            parsed.get("you_go_first"),
            parsed.get("first_player_name"),
            parsed.get("format_date"),
        ),
    )

    for event in build_events(parsed):
        cur.execute(
            """
            INSERT INTO events (
                event_id, game_id, turn_index, active_player, event_type, detail_text,
                pokemon_involved, damage, prize_delta_you, prize_delta_opp, is_turning_point
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["event_id"],
                game_id,
                event["turn_index"],
                event["active_player"],
                event["event_type"],
                event["detail_text"],
                event["pokemon_involved"],
                event["damage"],
                event["prize_delta_you"],
                event["prize_delta_opp"],
                event["is_turning_point"],
            ),
        )

    for tp in parsed.get("turning_points", []):
        cur.execute(
            """
            INSERT INTO turning_points (
                tp_id, game_id, turn_index, tp_type, description,
                you_prize_taken, opp_prize_taken, prize_diff
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                game_id,
                tp.get("turn_index", 0),
                tp.get("tp_type", "unknown"),
                tp.get("description", ""),
                tp.get("you_prize_taken", 0),
                tp.get("opp_prize_taken", 0),
                tp.get("prize_diff", 0),
            ),
        )

    conn.commit()
    conn.close()
    return game_id


def render_timeline(parsed: dict[str, Any]) -> str:
    tp_by_turn: dict[int, list[str]] = defaultdict(list)
    for tp in parsed.get("turning_points", []):
        tp_by_turn[tp["turn_index"]].append(tp["description"])

    lines: list[str] = []
    for turn in parsed["turns"]:
        active = turn["active_player"] or "Unknown"
        lines.append(f"Turn {turn['turn_index']} - {active}")
        for event in turn["events"]:
            et = event["event_type"]
            if et == "supporter":
                lines.append(f"- Supporter: {event['detail_text']}")
            elif et == "stadium":
                lines.append(f"- Stadium: {event['detail_text']}")
            elif et == "evolve":
                lines.append(f"- Evolution: {event['detail_text']}")
            elif et == "attack":
                dmg = f" ({event['damage']} damage)" if event.get("damage") is not None else ""
                lines.append(f"- Attack: {event['detail_text']}{dmg}")
            elif et == "ability":
                lines.append(f"- Ability: {event['detail_text']}")
            elif et == "ko":
                lines.append(f"- KO: {event['detail_text']}")
            elif et == "prize":
                lines.append(
                    f"- Prize: {event['detail_text']} (Total: You {event['score_you']} - Opp {event['score_opp']})"
                )
            elif et == "item":
                lines.append(f"- Key Event: {event['detail_text']}")
            elif et == "other":
                lines.append(f"- Board: {event['detail_text']}")
        for tp_text in tp_by_turn.get(turn["turn_index"], []):
            lines.append(f"- STAR Turning Point: {tp_text}")
        lines.append("")
    return "\n".join(lines).strip()


def render_prize_table(parsed: dict[str, Any]) -> str:
    lines = [
        "| # | Turn | Active Player | KO Target (Owner) | Prize Taken | Score (You-Opp) |",
        "|---|---:|---|---|---|---|",
    ]

    row_idx = 1
    for turn in parsed["turns"]:
        active = turn["active_player"] or "Unknown"
        for event in turn["events"]:
            if event["event_type"] not in ("ko", "prize"):
                continue

            ko_cell = "-"
            prize_cell = "-"
            if event["event_type"] == "ko":
                ko_cell = event["detail_text"].replace("KO: ", "")
            if event["event_type"] == "prize":
                prize_cell = event["detail_text"].replace("Prize: ", "")

            lines.append(
                f"| {row_idx} | {turn['turn_index']} | {active} | {ko_cell} | {prize_cell} | {event['score_you']}-{event['score_opp']} |"
            )
            row_idx += 1

    if row_idx == 1:
        lines.append("| 1 | - | - | - | - | 0-0 |")

    return "\n".join(lines)


def render_competitive_summary(parsed: dict[str, Any]) -> str:
    def summarize_range(start_t: int, end_t: Optional[int]) -> str:
        snippets: list[str] = []
        for turn in parsed["turns"]:
            if turn["turn_index"] < start_t:
                continue
            if end_t is not None and turn["turn_index"] > end_t:
                continue
            for event in turn["events"]:
                if event["event_type"] in {"supporter", "attack", "ability", "ko", "prize", "stadium", "evolve", "other"}:
                    snippets.append(f"T{turn['turn_index']}: {event['detail_text']}")
                if len(snippets) >= 4:
                    break
            if len(snippets) >= 4:
                break
        return "\n".join([f"- {x}" for x in snippets]) if snippets else "- N/A"

    first_text = "Unknown"
    if parsed.get("you_go_first") == 1:
        first_text = "You"
    elif parsed.get("you_go_first") == 0:
        first_text = "Opp"

    tp_lines = [f"- {idx + 1}) {tp['description']}" for idx, tp in enumerate(parsed.get("turning_points", []))]
    if not tp_lines:
        tp_lines = ["- 1) N/A", "- 2) N/A"]
    elif len(tp_lines) == 1:
        tp_lines.append("- 2) N/A")

    ko_you = 0
    ko_opp = 0
    for turn in parsed["turns"]:
        for event in turn["events"]:
            if event["event_type"] == "ko":
                if event.get("ko_target_owner") == "Opp":
                    ko_you += 1
                elif event.get("ko_target_owner") == "You":
                    ko_opp += 1

    return "\n".join(
        [
            "Decks:",
            f"- You: {parsed.get('you_deck_name') or 'Unknown'}",
            f"- Opp: {parsed.get('opp_deck_name') or 'Unknown'}",
            "",
            "Opening:",
            f"- First: {first_text}",
            f"- Starting Active: You {parsed['starting_active']['You']}, Opp {parsed['starting_active']['Opp']}",
            "",
            "Early Game (T1-2):",
            summarize_range(1, 2),
            "",
            "Mid Game (T3-5):",
            summarize_range(3, 5),
            "",
            "Key Turning Points:",
            *tp_lines,
            "",
            "Late Game (T6+):",
            summarize_range(6, None),
            "",
            "Result:",
            f"- Winner: {parsed.get('winner', 'Unknown')}",
            f"- Score: You {parsed.get('you_prize_taken', 0)} - Opp {parsed.get('opp_prize_taken', 0)}",
            f"- Total turns: {parsed.get('total_turns', 0)}",
            f"- KO count: You {ko_you}, Opp {ko_opp}",
        ]
    )


def compute_stats(db_path: str) -> dict[str, Any]:
    ensure_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    def pct(wins: int, n: int) -> float:
        return round((wins / n) * 100.0, 2) if n else 0.0

    overall = cur.execute(
        """
        SELECT
            COUNT(*) AS n,
            SUM(CASE WHEN winner='You' THEN 1 ELSE 0 END) AS wins,
            AVG(total_turns) AS avg_turns,
            AVG(you_prize_taken - opp_prize_taken) AS avg_prize_diff
        FROM games
        """
    ).fetchone()

    by_opp_deck = cur.execute(
        """
        SELECT
            COALESCE(NULLIF(opp_deck_name, ''), 'Unknown') AS deck,
            COUNT(*) AS n,
            SUM(CASE WHEN winner='You' THEN 1 ELSE 0 END) AS wins,
            AVG(total_turns) AS avg_turns,
            AVG(you_prize_taken - opp_prize_taken) AS avg_prize_diff
        FROM games
        GROUP BY COALESCE(NULLIF(opp_deck_name, ''), 'Unknown')
        ORDER BY n DESC
        LIMIT 10
        """
    ).fetchall()

    by_you_deck = cur.execute(
        """
        SELECT
            COALESCE(NULLIF(you_deck_name, ''), 'Unknown') AS deck,
            COUNT(*) AS n,
            SUM(CASE WHEN winner='You' THEN 1 ELSE 0 END) AS wins,
            AVG(total_turns) AS avg_turns,
            AVG(you_prize_taken - opp_prize_taken) AS avg_prize_diff
        FROM games
        GROUP BY COALESCE(NULLIF(you_deck_name, ''), 'Unknown')
        ORDER BY n DESC
        """
    ).fetchall()

    by_matchup = cur.execute(
        """
        SELECT
            COALESCE(NULLIF(you_deck_name, ''), 'Unknown') AS you_deck,
            COALESCE(NULLIF(opp_deck_name, ''), 'Unknown') AS opp_deck,
            COUNT(*) AS n,
            SUM(CASE WHEN winner='You' THEN 1 ELSE 0 END) AS wins,
            AVG(total_turns) AS avg_turns,
            AVG(you_prize_taken - opp_prize_taken) AS avg_prize_diff
        FROM games
        GROUP BY
            COALESCE(NULLIF(you_deck_name, ''), 'Unknown'),
            COALESCE(NULLIF(opp_deck_name, ''), 'Unknown')
        ORDER BY n DESC
        """
    ).fetchall()

    first_second = cur.execute(
        """
        SELECT
            CASE
                WHEN you_go_first = 0 THEN 'You go second'
                ELSE 'You go first'
            END AS bucket,
            COUNT(*) AS n,
            SUM(CASE WHEN winner='You' THEN 1 ELSE 0 END) AS wins,
            AVG(total_turns) AS avg_turns,
            AVG(you_prize_taken - opp_prize_taken) AS avg_prize_diff
        FROM games
        GROUP BY bucket
        """
    ).fetchall()

    tp_type_rows = cur.execute(
        """
        SELECT tp_type, COUNT(*) AS n
        FROM turning_points
        GROUP BY tp_type
        ORDER BY n DESC
        """
    ).fetchall()

    tp_state_rows = cur.execute(
        """
        WITH first_tp AS (
            SELECT t1.*
            FROM turning_points t1
            JOIN (
                SELECT game_id, MIN(turn_index) AS min_turn
                FROM turning_points
                GROUP BY game_id
            ) t2 ON t1.game_id = t2.game_id AND t1.turn_index = t2.min_turn
        )
        SELECT
            CASE
                WHEN first_tp.prize_diff > 0 THEN 'Ahead'
                WHEN first_tp.prize_diff < 0 THEN 'Behind'
                ELSE 'Tied'
            END AS state,
            COUNT(*) AS n,
            SUM(CASE WHEN games.winner='You' THEN 1 ELSE 0 END) AS wins
        FROM first_tp
        JOIN games ON first_tp.game_id = games.game_id
        GROUP BY state
        """
    ).fetchall()

    conn.close()

    overall_n = overall["n"] or 0
    overall_wins = overall["wins"] or 0

    first_second_map = {
        "You go first": {"n": 0, "wins": 0, "avg_turns": None, "avg_prize_diff": None},
        "You go second": {"n": 0, "wins": 0, "avg_turns": None, "avg_prize_diff": None},
    }
    for row in first_second:
        first_second_map[row["bucket"]] = {
            "n": row["n"],
            "wins": row["wins"] or 0,
            "avg_turns": row["avg_turns"],
            "avg_prize_diff": row["avg_prize_diff"],
        }

    return {
        "overall": {
            "n": overall_n,
            "wins": overall_wins,
            "win_rate": pct(overall_wins, overall_n),
            "avg_turns": overall["avg_turns"],
            "avg_prize_diff": overall["avg_prize_diff"],
        },
        "by_opp_deck": [
            {
                "deck": row["deck"],
                "n": row["n"],
                "wins": row["wins"] or 0,
                "win_rate": pct(row["wins"] or 0, row["n"]),
                "avg_turns": row["avg_turns"],
                "avg_prize_diff": row["avg_prize_diff"],
            }
            for row in by_opp_deck
        ],
        "by_you_deck": [
            {
                "deck": row["deck"],
                "n": row["n"],
                "wins": row["wins"] or 0,
                "win_rate": pct(row["wins"] or 0, row["n"]),
                "avg_turns": row["avg_turns"],
                "avg_prize_diff": row["avg_prize_diff"],
            }
            for row in by_you_deck
        ],
        "by_matchup": [
            {
                "matchup": f"{row['you_deck']} vs {row['opp_deck']}",
                "n": row["n"],
                "wins": row["wins"] or 0,
                "win_rate": pct(row["wins"] or 0, row["n"]),
                "avg_turns": row["avg_turns"],
                "avg_prize_diff": row["avg_prize_diff"],
            }
            for row in by_matchup
        ],
        "first_second": {
            "You go first": {
                **first_second_map["You go first"],
                "win_rate": pct(first_second_map["You go first"]["wins"], first_second_map["You go first"]["n"]),
            },
            "You go second": {
                **first_second_map["You go second"],
                "win_rate": pct(first_second_map["You go second"]["wins"], first_second_map["You go second"]["n"]),
            },
            "n_first": first_second_map["You go first"]["n"],
            "n_second": first_second_map["You go second"]["n"],
            "n_unknown": 0,
        },
        "turning_point_types": [{"tp_type": row["tp_type"], "n": row["n"]} for row in tp_type_rows],
        "turning_point_state_winrate": [
            {
                "state": row["state"],
                "n": row["n"],
                "wins": row["wins"] or 0,
                "win_rate": pct(row["wins"] or 0, row["n"]),
            }
            for row in tp_state_rows
        ],
    }


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    if not rows:
        headers = "| " + " | ".join(title for _, title in columns) + " |"
        splitter = "|" + "|".join(["---"] * len(columns)) + "|"
        empty = "| " + " | ".join(["-"] * len(columns)) + " |"
        return "\n".join([headers, splitter, empty])

    headers = "| " + " | ".join(title for _, title in columns) + " |"
    splitter = "|" + "|".join(["---"] * len(columns)) + "|"
    body = []
    for row in rows:
        values = []
        for key, _ in columns:
            val = row.get(key)
            if isinstance(val, float):
                values.append(f"{val:.2f}")
            else:
                values.append(str(val))
        body.append("| " + " | ".join(values) + " |")
    return "\n".join([headers, splitter] + body)


def csv_bytes(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([title for _, title in columns])
    for row in rows:
        writer.writerow([row.get(key, "") for key, _ in columns])
    return output.getvalue().encode("utf-8")


def render_stats(stats: dict[str, Any]) -> None:
    st.subheader("Database Stats")

    overall = stats["overall"]
    st.markdown(
        "\n".join(
            [
                f"- Overall Win Rate (You): **{overall['win_rate']:.2f}%** (n={overall['n']})",
                f"- Average total turns: **{(overall['avg_turns'] or 0):.2f}**",
                f"- Average prize differential (You-Opp): **{(overall['avg_prize_diff'] or 0):.2f}**",
            ]
        )
    )

    st.markdown("**Win Rate by Opp Deck Name (Top 10)**")
    st.markdown(
        markdown_table(
            stats["by_opp_deck"],
            [
                ("deck", "Opp Deck"),
                ("n", "n"),
                ("wins", "Wins"),
                ("win_rate", "Win Rate %"),
                ("avg_turns", "Avg Turns"),
                ("avg_prize_diff", "Avg Prize Diff"),
            ],
        )
    )
    st.download_button(
        "Download Opp Deck Stats CSV",
        data=csv_bytes(
            stats["by_opp_deck"],
            [
                ("deck", "Opp Deck"),
                ("n", "n"),
                ("wins", "Wins"),
                ("win_rate", "Win Rate %"),
                ("avg_turns", "Avg Turns"),
                ("avg_prize_diff", "Avg Prize Diff"),
            ],
        ),
        file_name="stats_by_opp_deck.csv",
        mime="text/csv",
    )

    st.markdown("**Win Rate by You Deck Name**")
    st.markdown(
        markdown_table(
            stats["by_you_deck"],
            [
                ("deck", "You Deck"),
                ("n", "n"),
                ("wins", "Wins"),
                ("win_rate", "Win Rate %"),
                ("avg_turns", "Avg Turns"),
                ("avg_prize_diff", "Avg Prize Diff"),
            ],
        )
    )
    st.download_button(
        "Download You Deck Stats CSV",
        data=csv_bytes(
            stats["by_you_deck"],
            [
                ("deck", "You Deck"),
                ("n", "n"),
                ("wins", "Wins"),
                ("win_rate", "Win Rate %"),
                ("avg_turns", "Avg Turns"),
                ("avg_prize_diff", "Avg Prize Diff"),
            ],
        ),
        file_name="stats_by_you_deck.csv",
        mime="text/csv",
    )

    st.markdown("**Average Turns / Prize Diff by Matchup**")
    st.markdown(
        markdown_table(
            stats["by_matchup"],
            [
                ("matchup", "Matchup"),
                ("n", "n"),
                ("win_rate", "Win Rate %"),
                ("avg_turns", "Avg Turns"),
                ("avg_prize_diff", "Avg Prize Diff"),
            ],
        )
    )
    st.download_button(
        "Download Matchup Stats CSV",
        data=csv_bytes(
            stats["by_matchup"],
            [
                ("matchup", "Matchup"),
                ("n", "n"),
                ("win_rate", "Win Rate %"),
                ("avg_turns", "Avg Turns"),
                ("avg_prize_diff", "Avg Prize Diff"),
            ],
        ),
        file_name="stats_by_matchup.csv",
        mime="text/csv",
    )

    fs = stats["first_second"]
    st.markdown("**First/Second Advantage**")
    st.markdown(
        "\n".join(
            [
                f"- You go first: {fs['You go first']['win_rate']:.2f}% (n={fs['You go first']['n']}), avg turns {(fs['You go first']['avg_turns'] or 0):.2f}, avg prize diff {(fs['You go first']['avg_prize_diff'] or 0):.2f}",
                f"- You go second: {fs['You go second']['win_rate']:.2f}% (n={fs['You go second']['n']}), avg turns {(fs['You go second']['avg_turns'] or 0):.2f}, avg prize diff {(fs['You go second']['avg_prize_diff'] or 0):.2f}",
                f"- Sample size split: n_first={fs['n_first']}, n_second={fs['n_second']}, n_unknown={fs['n_unknown']}",
            ]
        )
    )
    st.download_button(
        "Download First/Second Stats CSV",
        data=csv_bytes(
            [
                {
                    "bucket": "You go first",
                    "n": fs["You go first"]["n"],
                    "wins": fs["You go first"]["wins"],
                    "win_rate": fs["You go first"]["win_rate"],
                    "avg_turns": fs["You go first"]["avg_turns"],
                    "avg_prize_diff": fs["You go first"]["avg_prize_diff"],
                },
                {
                    "bucket": "You go second",
                    "n": fs["You go second"]["n"],
                    "wins": fs["You go second"]["wins"],
                    "win_rate": fs["You go second"]["win_rate"],
                    "avg_turns": fs["You go second"]["avg_turns"],
                    "avg_prize_diff": fs["You go second"]["avg_prize_diff"],
                },
            ],
            [
                ("bucket", "Bucket"),
                ("n", "n"),
                ("wins", "Wins"),
                ("win_rate", "Win Rate %"),
                ("avg_turns", "Avg Turns"),
                ("avg_prize_diff", "Avg Prize Diff"),
            ],
        ),
        file_name="stats_first_second.csv",
        mime="text/csv",
    )

    st.markdown("**Key Turning Points Summary**")
    st.markdown("Most common turning point type")
    st.markdown(markdown_table(stats["turning_point_types"], [("tp_type", "Type"), ("n", "Count")]))
    st.markdown("Win rate after first turning point by state")
    st.markdown(
        markdown_table(
            stats["turning_point_state_winrate"],
            [("state", "State at TP"), ("n", "n"), ("wins", "Wins"), ("win_rate", "Win Rate %")],
        )
    )


def main() -> None:
    if st is None:
        raise RuntimeError(
            "streamlit is not installed. Install it with `python3 -m pip install streamlit` "
            "and then run `streamlit run app.py`."
        )
    ensure_db(DB_PATH)

    st.set_page_config(page_title="PTCG Live Battle Log Parser", layout="wide")
    st.title("PTCG Live Battle Log -> DB + Auto Summary")
    st.caption("Player mapping fixed: Neurologist2024 = You, opponent = Opp")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        you_deck_name = st.text_input("You Deck Name", value="")
    with col_b:
        opp_deck_name = st.text_input("Opp Deck Name", value="")
    with col_c:
        format_date = st.text_input("Format/Date", value="")

    notes = st.text_input("Notes (optional)", value="")

    default_log = ""
    try:
        with open("sample_log.txt", "r", encoding="utf-8") as f:
            default_log = f.read()
    except FileNotFoundError:
        default_log = ""

    battle_log = st.text_area("Paste battle log", value=default_log, height=420)

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        do_save = st.button("Parse & Save", type="primary", use_container_width=True)
    with btn_col2:
        do_summary_only = st.button("Generate Summary Only", use_container_width=True)

    parsed: Optional[dict[str, Any]] = None

    if do_save or do_summary_only:
        if not battle_log.strip():
            st.warning("Please paste a battle log first.")
        else:
            parsed = parse_log(battle_log, you_name=YOU_DEFAULT)
            parsed["you_deck_name"] = you_deck_name.strip() or None
            parsed["opp_deck_name"] = opp_deck_name.strip() or None
            parsed["format_date"] = format_date.strip() or None
            parsed["notes"] = notes.strip() or None

            if do_save:
                game_id = save_game_and_events(DB_PATH, parsed)
                st.success(f"Saved game: {game_id}")

    if parsed:
        st.subheader("A) Turn Timeline")
        st.markdown(render_timeline(parsed))

        st.subheader("B) KO + Prize Tracker")
        st.markdown(render_prize_table(parsed))

        st.subheader("C) Competitive Summary Template")
        st.markdown(render_competitive_summary(parsed))

    stats = compute_stats(DB_PATH)
    render_stats(stats)


if __name__ == "__main__":
    main()
