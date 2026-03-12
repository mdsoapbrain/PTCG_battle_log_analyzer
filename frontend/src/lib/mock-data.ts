/**
 * Mock data for development. Replace with real API calls.
 * All mock data is isolated here for easy swapping.
 */
import type { Match, OverviewStats, GoFirstStats, DeckStat, MatchupStat } from "@/types/api";

export const mockOverview: OverviewStats = {
  total_matches: 142,
  wins: 89,
  losses: 53,
  win_rate: 62.7,
  average_prize_differential: 1.8,
  average_turn_count: 8.3,
  go_first_win_rate: 69.1,
  go_second_win_rate: 56.8,
  recent_trend: [],
};

export const mockGoFirst: GoFirstStats = {
  first_matches: 68,
  first_wins: 47,
  first_win_rate: 69.1,
  second_matches: 74,
  second_wins: 42,
  second_win_rate: 56.8,
};

export const mockDeckStats: DeckStat[] = [
  { deck_name: "Charizard ex", matches: 45, wins: 32, win_rate: 71.1, avg_prize_diff: 2.3, avg_turn_count: 7.8 },
  { deck_name: "Teal Mask Ogerpon ex", matches: 38, wins: 24, win_rate: 63.2, avg_prize_diff: 1.5, avg_turn_count: 8.9 },
  { deck_name: "Lugia VSTAR", matches: 30, wins: 18, win_rate: 60.0, avg_prize_diff: 1.2, avg_turn_count: 9.1 },
  { deck_name: "Regidrago VSTAR", matches: 29, wins: 15, win_rate: 51.7, avg_prize_diff: 0.4, avg_turn_count: 8.5 },
];

export const mockMatchups: MatchupStat[] = [
  { player_deck: "Charizard ex", opponent_deck: "Lugia VSTAR", matches: 12, wins: 9, win_rate: 75.0, avg_prize_diff: 2.8, avg_turn_count: 7.2 },
  { player_deck: "Charizard ex", opponent_deck: "Regidrago VSTAR", matches: 8, wins: 5, win_rate: 62.5, avg_prize_diff: 1.2, avg_turn_count: 8.3 },
  { player_deck: "Teal Mask Ogerpon ex", opponent_deck: "Charizard ex", matches: 10, wins: 4, win_rate: 40.0, avg_prize_diff: -1.1, avg_turn_count: 9.4 },
  { player_deck: "Teal Mask Ogerpon ex", opponent_deck: "Garchomp ex", matches: 7, wins: 5, win_rate: 71.4, avg_prize_diff: 2.0, avg_turn_count: 8.0 },
  { player_deck: "Lugia VSTAR", opponent_deck: "Charizard ex", matches: 9, wins: 3, win_rate: 33.3, avg_prize_diff: -2.1, avg_turn_count: 9.1 },
];

export const mockRecentMatches: Match[] = [
  {
    match_id: "f44dc8d7-33de-4f02-8b83-0f9b5f63db7a",
    created_at: "2026-03-11T19:20:00Z",
    player_name: "Neurologist2024",
    opponent_name: "Rival123",
    player_deck: "Charizard ex",
    opponent_deck: "Garchomp ex",
    went_first: false,
    result: "win",
    turn_count: 7,
    prizes_taken: 6,
    prizes_lost: 4,
    prize_diff: 2,
    winner: "You",
    summary_text: "Close game with a late-game Charizard ex sweep.",
    turns: [],
  },
  {
    match_id: "a12bc3d4-5678-9012-ab34-cd5678ef9012",
    created_at: "2026-03-11T17:45:00Z",
    player_name: "Neurologist2024",
    opponent_name: "AceTrainer",
    player_deck: "Teal Mask Ogerpon ex",
    opponent_deck: "Lugia VSTAR",
    went_first: true,
    result: "loss",
    turn_count: 9,
    prizes_taken: 4,
    prizes_lost: 6,
    prize_diff: -2,
    winner: "AceTrainer",
    summary_text: "Lugia VSTAR established early pressure with Archeops.",
    turns: [],
  },
  {
    match_id: "b23cd4e5-6789-0123-bc45-de6789fa0123",
    created_at: "2026-03-10T22:10:00Z",
    player_name: "Neurologist2024",
    opponent_name: "DragonMaster",
    player_deck: "Charizard ex",
    opponent_deck: "Regidrago VSTAR",
    went_first: true,
    result: "win",
    turn_count: 6,
    prizes_taken: 6,
    prizes_lost: 2,
    prize_diff: 4,
    winner: "You",
    summary_text: "Dominant early game with turn 2 Charizard ex setup.",
    turns: [],
  },
  {
    match_id: "c34de5f6-7890-1234-cd56-ef7890ab1234",
    created_at: "2026-03-10T20:30:00Z",
    player_name: "Neurologist2024",
    opponent_name: "PikaFan99",
    player_deck: "Lugia VSTAR",
    opponent_deck: "Pikachu ex",
    went_first: false,
    result: "win",
    turn_count: 8,
    prizes_taken: 6,
    prizes_lost: 3,
    prize_diff: 3,
    winner: "You",
    summary_text: "Lugia VSTAR tanked hits and swept with Colorless attackers.",
    turns: [],
  },
  {
    match_id: "d45ef6a7-8901-2345-de67-fa8901bc2345",
    created_at: "2026-03-10T18:00:00Z",
    player_name: "Neurologist2024",
    opponent_name: "ShadowRider",
    player_deck: "Regidrago VSTAR",
    opponent_deck: "Dragapult ex",
    went_first: true,
    result: "loss",
    turn_count: 10,
    prizes_taken: 5,
    prizes_lost: 6,
    prize_diff: -1,
    winner: "ShadowRider",
    summary_text: "Dragapult ex spread damage was too much to handle.",
    turns: [],
  },
];
