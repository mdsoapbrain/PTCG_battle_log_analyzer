import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { MatchupStat } from "@/types/api";
import { ApiError, EmptyState } from "@/components/ui/api-error";
import { cn } from "@/lib/utils";

export default function MatchupAnalytics() {
  const [matchups, setMatchups] = useState<MatchupStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<keyof MatchupStat>("win_rate");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getMatchupStats();
      setMatchups(res.data ?? []);
    } catch (err: any) {
      setError(err.message || "Failed to load matchup stats");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const sorted = [...matchups].sort((a, b) => {
    const av = a[sortKey] as number;
    const bv = b[sortKey] as number;
    return sortDir === "desc" ? bv - av : av - bv;
  });

  const toggleSort = (key: keyof MatchupStat) => {
    if (sortKey === key) setSortDir(sortDir === "desc" ? "asc" : "desc");
    else { setSortKey(key); setSortDir("desc"); }
  };

  const SortHeader = ({ label, field }: { label: string; field: keyof MatchupStat }) => (
    <th
      className="text-center py-3 px-4 font-medium cursor-pointer hover:text-foreground transition-colors select-none"
      onClick={() => toggleSort(field)}
    >
      {label} {sortKey === field && (sortDir === "desc" ? "↓" : "↑")}
    </th>
  );

  return (
    <div className="max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Matchup Analytics</h1>
        <p className="text-sm text-muted-foreground">Head-to-head performance by deck pairing</p>
      </div>

      {error ? (
        <ApiError message={error} onRetry={load} />
      ) : loading ? (
        <div className="text-center py-20 text-muted-foreground">Loading…</div>
      ) : matchups.length === 0 ? (
        <EmptyState message="No matchup data yet. Save matches with deck names to see head-to-head stats." />
      ) : (
        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-muted-foreground">
                <th className="text-left py-3 px-4 font-medium">My Deck</th>
                <th className="text-left py-3 px-4 font-medium">vs Opponent Deck</th>
                <SortHeader label="Games" field="matches" />
                <SortHeader label="Wins" field="wins" />
                <SortHeader label="Win Rate" field="win_rate" />
                <SortHeader label="Avg Prize Diff" field="avg_prize_diff" />
              </tr>
            </thead>
            <tbody>
              {sorted.map((m, i) => (
                <tr key={i} className="border-b border-border/50 hover:bg-secondary/30 transition-colors">
                  <td className="py-3 px-4 font-medium text-foreground">{m.player_deck}</td>
                  <td className="py-3 px-4 text-muted-foreground">{m.opponent_deck}</td>
                  <td className="py-3 px-4 text-center font-mono">{m.matches}</td>
                  <td className="py-3 px-4 text-center font-mono text-win">{m.wins}</td>
                  <td className="py-3 px-4 text-center">
                    <span className={cn("font-mono font-semibold", m.win_rate >= 55 ? "text-win" : m.win_rate >= 45 ? "text-draw" : "text-loss")}>
                      {m.win_rate.toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center font-mono">
                    <span className={cn(m.avg_prize_diff > 0 ? "text-win" : m.avg_prize_diff < 0 ? "text-loss" : "text-muted-foreground")}>
                      {m.avg_prize_diff > 0 ? "+" : ""}{m.avg_prize_diff.toFixed(1)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
