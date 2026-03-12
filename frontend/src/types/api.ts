// API response envelope
export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data: T | null;
  pagination: Pagination | null;
  error: ApiError | null;
}

export interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ApiError {
  code: string;
  detail: string;
}

// Parse log
export interface ParsedLog {
  player_name: string;
  opponent_name: string;
  winner: string;
  went_first: boolean | null;
  first_player_name: string | null;
  total_turns: number;
  prizes_taken: number;
  prizes_lost: number;
  first_ko_by: string;
  turning_points: Array<Record<string, unknown>>;
  turns: TurnEvent[];
  timeline_markdown: string;
  prize_table_markdown: string;
  competitive_summary_markdown: string;
}

export interface TurnEvent {
  turn_number?: number;
  player?: string;
  actions?: string[];
  [key: string]: unknown;
}

// Match
export interface Match {
  match_id: string;
  created_at: string;
  player_name: string;
  opponent_name: string;
  player_deck: string | null;
  opponent_deck: string | null;
  went_first: boolean | null;
  result: "win" | "loss" | "unknown";
  turn_count: number;
  prizes_taken: number;
  prizes_lost: number;
  prize_diff: number;
  winner: string;
  summary_text: string | null;
  turns: TurnEvent[];
  notes?: string;
  tags?: string[];
}

// Stats
export interface OverviewStats {
  total_matches: number;
  wins: number;
  losses: number;
  win_rate: number;
  average_prize_differential: number;
  average_turn_count: number;
  go_first_win_rate: number;
  go_second_win_rate: number;
  recent_trend: RecentTrendPoint[];
}

export interface GoFirstStats {
  first_matches: number;
  first_wins: number;
  first_win_rate: number;
  second_matches: number;
  second_wins: number;
  second_win_rate: number;
}

export interface RecentTrendPoint {
  date: string;
  matches: number;
  wins: number;
  win_rate: number;
}

export interface DeckStat {
  deck_name: string;
  matches: number;
  wins: number;
  win_rate: number;
  avg_prize_diff: number;
  avg_turn_count: number;
}

export interface MatchupStat {
  player_deck: string;
  opponent_deck: string;
  matches: number;
  wins: number;
  win_rate: number;
  avg_prize_diff: number;
  avg_turn_count: number;
}

// Save match request
export interface SaveMatchRequest {
  raw_log: string;
  player_name?: string;
  player_deck?: string;
  opponent_deck?: string;
  notes?: string;
}
