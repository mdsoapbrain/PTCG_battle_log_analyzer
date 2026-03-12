import type { ApiResponse, ParsedLog, Match, OverviewStats, GoFirstStats, DeckStat, MatchupStat, SaveMatchRequest } from "@/types/api";

const rawApiBase = import.meta.env.VITE_API_BASE_URL?.trim();
const API_BASE = (rawApiBase && rawApiBase.length > 0 ? rawApiBase : "http://localhost:8001").replace(/\/+$/, "");

async function request<T>(path: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const token = localStorage.getItem("auth_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  let json: ApiResponse<T> | null = null;
  try {
    json = await res.json();
  } catch {
    // noop
  }

  if (!res.ok || !json || !json.success) {
    const detail = json?.error?.detail || json?.message || `HTTP ${res.status}`;
    throw new Error(detail);
  }
  return json;
}

export const api = {
  parseLog: (rawLog: string, playerName?: string) =>
    request<ParsedLog>("/parse-log", {
      method: "POST",
      body: JSON.stringify({ raw_log: rawLog, player_name: playerName || undefined }),
    }),

  saveMatch: (data: SaveMatchRequest) =>
    request<Match>("/matches", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getMatches: (params?: Record<string, string>) => {
    const query = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{ items: Match[] }>(`/matches${query}`);
  },

  getMatch: (matchId: string) =>
    request<Match>(`/matches/${matchId}`),

  getOverviewStats: () =>
    request<OverviewStats>("/stats/overview"),

  getGoFirstStats: () =>
    request<GoFirstStats>("/stats/go-first"),

  async getDeckStats() {
    const res = await request<{ rows: DeckStat[] }>("/stats/by-deck");
    return { ...res, data: res.data?.rows ?? [] } as ApiResponse<DeckStat[]>;
  },

  async getMatchupStats() {
    const res = await request<{ rows: MatchupStat[] }>("/stats/by-matchup");
    return { ...res, data: res.data?.rows ?? [] } as ApiResponse<MatchupStat[]>;
  },
};
