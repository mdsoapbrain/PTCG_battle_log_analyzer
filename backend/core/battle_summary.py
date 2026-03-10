from __future__ import annotations

from collections import defaultdict
from typing import Any


def render_timeline(parsed: dict[str, Any]) -> str:
    tp_by_turn: dict[int, list[str]] = defaultdict(list)
    for tp in parsed.get("turning_points", []):
        tp_by_turn[tp["turn_index"]].append(tp["description"])

    lines: list[str] = []
    for turn in parsed["turns"]:
        active = turn["active_player"] or "Unknown"
        lines.append(f"Turn {turn['turn_index']} - {active}")
        had_key_line = False
        for event in turn["events"]:
            et = event["event_type"]
            if et == "supporter":
                lines.append(f"- Supporter: {event['detail_text']}")
                had_key_line = True
            elif et == "stadium":
                lines.append(f"- Stadium: {event['detail_text']}")
                had_key_line = True
            elif et == "evolve":
                lines.append(f"- Evolution: {event['detail_text']}")
                had_key_line = True
            elif et == "attack":
                dmg = f" ({event['damage']} damage)" if event.get("damage") is not None else ""
                lines.append(f"- Attack: {event['detail_text']}{dmg}")
                had_key_line = True
            elif et == "ability":
                lines.append(f"- Ability: {event['detail_text']}")
                had_key_line = True
            elif et == "ko":
                lines.append(f"- KO: {event['detail_text']}")
                had_key_line = True
            elif et == "prize":
                lines.append(
                    f"- Prize: {event['detail_text']} (Total: You {event['score_you']} - Opp {event['score_opp']})"
                )
                had_key_line = True
            elif et == "item":
                lines.append(f"- Key Event: {event['detail_text']}")
                had_key_line = True
            elif et == "other":
                lines.append(f"- Board: {event['detail_text']}")
                had_key_line = True
        if not had_key_line:
            lines.append("- No key events captured.")
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
    def summarize_range(start_t: int, end_t: int | None) -> str:
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
