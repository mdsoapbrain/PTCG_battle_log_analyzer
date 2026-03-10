from __future__ import annotations

import re
from collections import Counter
from typing import Any


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
WIN_LINE_PATTERNS = [
    re.compile(r"All Prize cards taken\. ([A-Za-z0-9_]+) wins\.?"),
    re.compile(r"(?:[A-Za-z0-9_]+|Opponent) was inactive for too long\. ([A-Za-z0-9_]+) wins\.?"),
    re.compile(r"([A-Za-z0-9_]+) conceded\. ([A-Za-z0-9_]+) wins\.?"),
    re.compile(r"No Benched Pokemon for backup\. ([A-Za-z0-9_]+) wins\.?"),
]


def normalize_text(text: str) -> str:
    return text.replace("\u2019", "'").replace("\u2018", "'").replace("\u00e9", "e")


def extract_winner_name(line: str) -> str | None:
    if not any(pat.match(line) for pat in WIN_LINE_PATTERNS):
        return None
    m = re.search(r"([A-Za-z0-9_]+) wins\.?$", line)
    return m.group(1) if m else None


def map_player(name: str | None, you_name: str, opp_name: str) -> str:
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
        re.compile(r"^([A-Za-z0-9_]+) (?:drew|played|attached|evolved|retreated|ended|chose|won|decided|shuffled|took|discarded|moved|put|used|is)"),
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


def parse_log(text: str, you_name: str = "Neurologist2024") -> dict[str, Any]:
    raw_lines = [normalize_text(x.strip()) for x in text.splitlines() if x.strip()]
    opp_name = guess_opp_name(raw_lines, you_name)

    decided_first_re = re.compile(r"^([A-Za-z0-9_]+) decided to go first\.$")
    first_player_name = None
    for line in raw_lines:
        m = decided_first_re.match(line)
        if m:
            first_player_name = m.group(1)
            break

    you_go_first = None if first_player_name is None else (1 if first_player_name == you_name else 0)

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
    current_turn: dict[str, Any] | None = None
    you_prize_taken = 0
    opp_prize_taken = 0
    first_ko_by = "Unknown"
    winner = "Unknown"
    first_ex_ko_ref: tuple[int, int] | None = None

    turn_marker_re = re.compile(r"^([A-Za-z0-9_]+)'s Turn$")
    placeholder_turn_marker = "[playerName]'s Turn"

    def start_turn(active_player_name: str | None) -> dict[str, Any]:
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

    def infer_line_player(line: str) -> str | None:
        m = re.match(r"^([A-Za-z0-9_]+)(?:'s)?\b", line)
        if not m:
            return None
        candidate = m.group(1)
        mapped = map_player(candidate, you_name, opp_name)
        return mapped if mapped in ("You", "Opp") else None

    def add_event(
        event_type: str,
        detail_text: str,
        pokemon_involved: str | None = None,
        damage: int | None = None,
        prize_delta_you: int = 0,
        prize_delta_opp: int = 0,
        ko_target_owner: str | None = None,
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

        winner_name = extract_winner_name(line)
        if winner_name:
            winner = map_player(winner_name, you_name, opp_name)
            if current_turn is not None:
                add_event("other", f"Game End: {line}")

        if current_turn is None:
            continue

        if current_turn["active_player"] is None:
            inferred = infer_line_player(line)
            if inferred:
                current_turn["active_player"] = inferred

        m_played = re.match(r"^([A-Za-z0-9_]+) played (.+)\.$", line)
        if m_played:
            player_name, card = m_played.groups()
            actor = map_player(player_name, you_name, opp_name)
            if current_turn["active_player"] is None and actor in ("You", "Opp"):
                current_turn["active_player"] = actor

            line_lower = line.lower()
            if "to the stadium spot" in line_lower:
                add_event("stadium", f"{actor}: {card}")
            elif "to the bench" in line_lower or "to the active spot" in line_lower or "to become the active pokemon" in line_lower:
                add_event("other", f"{actor}: {card}")
            elif "Boss's Orders" in card:
                add_event("supporter", f"{actor}: {card}")
            elif any(hint in card for hint in SUPPORTER_HINTS):
                add_event("supporter", f"{actor}: {card}")
            elif any(k in card for k in KEY_RESOURCE_CARDS):
                add_event("item", f"{actor}: {card}")
            continue

        m_now_active = re.match(r"^([A-Za-z0-9_]+)'s (.+) is now in the Active Spot\.$", line)
        if m_now_active:
            actor_name, pokemon = m_now_active.groups()
            actor = map_player(actor_name, you_name, opp_name)
            add_event("other", f"{actor}: {pokemon} moved to Active Spot", pokemon_involved=pokemon)
            continue

        m_evo = re.match(r"^([A-Za-z0-9_]+) evolved (.+) to (.+) on the (Bench|Active Spot)\.?$", line)
        if m_evo:
            player_name, src_pkm, dst_pkm, zone = m_evo.groups()
            actor = map_player(player_name, you_name, opp_name)
            add_event("evolve", f"{actor}: {src_pkm} -> {dst_pkm} ({zone})", pokemon_involved=dst_pkm)
            continue

        m_attack_damage = re.match(
            r"^([A-Za-z0-9_]+)'s (.+) used (.+) on ([A-Za-z0-9_]+)'s (.+) for (\d+) damage\.?$",
            line,
        )
        if m_attack_damage:
            atk_player, atk_pokemon, move_name, _, def_pokemon, damage = m_attack_damage.groups()
            actor = map_player(atk_player, you_name, opp_name)
            detail = f"{actor}: {atk_pokemon} used {move_name} on {def_pokemon} for {damage}"
            add_event("attack", detail, pokemon_involved=f"{atk_pokemon} -> {def_pokemon}", damage=int(damage))
            continue

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

        m_took_damage = re.match(r"^([A-Za-z0-9_]+)'s (.+) took (\d+) damage\.?$", line)
        if m_took_damage:
            dmg_owner, dmg_target, dmg = m_took_damage.groups()
            target_owner = map_player(dmg_owner, you_name, opp_name)
            add_event("attack", f"Damage: {dmg_target} ({target_owner}) took {dmg}", pokemon_involved=dmg_target, damage=int(dmg))
            continue

        m_ko = re.match(r"^([A-Za-z0-9_]+)'s (.+) was Knocked Out!$", line)
        if m_ko:
            target_owner_name, target_pokemon = m_ko.groups()
            ko_target_owner = map_player(target_owner_name, you_name, opp_name)
            add_event("ko", f"KO: {target_pokemon} ({ko_target_owner})", pokemon_involved=target_pokemon, ko_target_owner=ko_target_owner)
            if first_ko_by == "Unknown":
                first_ko_by = current_turn["active_player"] or "Unknown"
            if first_ex_ko_ref is None and "ex" in target_pokemon.lower():
                first_ex_ko_ref = (len(turns), len(current_turn["events"]) - 1)
            continue

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
            add_event("prize", f"Prize: {mapped} +{prize_count}", prize_delta_you=delta_you, prize_delta_opp=delta_opp)
            current_turn["events"][-1]["score_you"] = you_prize_taken
            current_turn["events"][-1]["score_opp"] = opp_prize_taken
            continue

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
    max_swing = 0
    max_swing_turn: dict[str, Any] | None = None
    for t in turns:
        swing = t["prize_delta_you"] - t["prize_delta_opp"]
        if abs(swing) > abs(max_swing):
            max_swing = swing
            max_swing_turn = t

    if max_swing_turn is not None and max_swing != 0:
        turning_points.append(
            {
                "tp_type": "prize_swing",
                "turn_index": max_swing_turn["turn_index"],
                "description": f"Largest prize swing in Turn {max_swing_turn['turn_index']} (net {max_swing:+d})",
                "you_prize_taken": max_swing_turn["prize_end_you"],
                "opp_prize_taken": max_swing_turn["prize_end_opp"],
                "prize_diff": max_swing_turn["prize_end_you"] - max_swing_turn["prize_end_opp"],
            }
        )
        max_swing_turn["turning_point_types"].append("prize_swing")
        for event in max_swing_turn["events"]:
            if event["event_type"] == "prize":
                event["is_turning_point"] = True

    if first_ex_ko_ref is not None and len(turning_points) < 2:
        turn_list_index, event_index = first_ex_ko_ref
        if 0 <= turn_list_index < len(turns):
            turn_obj = turns[turn_list_index]
            if 0 <= event_index < len(turn_obj["events"]):
                ko_event = turn_obj["events"][event_index]
                ko_event["is_turning_point"] = True
                turning_points.append(
                    {
                        "tp_type": "ex_ko",
                        "turn_index": turn_obj["turn_index"],
                        "description": f"First ex KO in Turn {turn_obj['turn_index']}: {ko_event['detail_text']}",
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
                    "turn_index": turn["turn_index"],
                    "active_player": active,
                    "event_type": event["event_type"],
                    "detail_text": event["detail_text"],
                    "pokemon_involved": event.get("pokemon_involved"),
                    "damage": event.get("damage"),
                    "prize_delta_you": event.get("prize_delta_you", 0),
                    "prize_delta_opp": event.get("prize_delta_opp", 0),
                    "is_turning_point": bool(event.get("is_turning_point")),
                }
            )
    return flattened
