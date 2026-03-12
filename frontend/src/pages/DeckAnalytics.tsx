import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { DeckStat } from "@/types/api";
import { DeckWinRateChart } from "@/components/dashboard/DeckWinRateChart";
import { ApiError, EmptyState } from "@/components/ui/api-error";
import { cn } from "@/lib/utils";

export default function DeckAnalytics() {
  const [deckStats, setDeckStats] = useState<DeckStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getDeckStats();
      setDeckStats(res.data ?? []);
    } catch (err: any) {
      setError(err.message || "Failed to load deck stats");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Deck Analytics</h1>
        <p className="text-sm text-muted-foreground">Performance breakdown by deck archetype</p>
      </div>

      {error ? (
        <ApiError message={error} onRetry={load} />
      ) : loading ? (
        <div className="text-center py-20 text-muted-foreground">Loading…</div>
      ) : deckStats.length === 0 ? (
        <EmptyState message="No deck data yet. Save some matches with deck names to see analytics." />
      ) : (
        <>
          <div className="rounded-lg border border-border bg-card p-5">
            <h2 className="font-display font-semibold text-foreground mb-4">Win Rate by Deck</h2>
            <DeckWinRateChart data={deckStats} />
          </div>

          <div className="rounded-lg border border-border bg-card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-muted-foreground">
                  <th className="text-left py-3 px-4 font-medium">Deck</th>
                  <th className="text-center py-3 px-4 font-medium">Games</th>
                  <th className="text-center py-3 px-4 font-medium">Wins</th>
                  <th className="text-center py-3 px-4 font-medium">Losses</th>
                  <th className="text-center py-3 px-4 font-medium">Win Rate</th>
                  <th className="text-center py-3 px-4 font-medium">Avg Prize Diff</th>
                  <th className="text-center py-3 px-4 font-medium">Avg Turns</th>
                </tr>
              </thead>
              <tbody>
                {deckStats.map((d) => {
                  const losses = Math.max(d.matches - d.wins, 0);
                  return (
                    <tr key={d.deck_name} className="border-b border-border/50 hover:bg-secondary/30 transition-colors">
                      <td className="py-3 px-4 font-medium text-foreground">{d.deck_name}</td>
                      <td className="py-3 px-4 text-center font-mono">{d.matches}</td>
                      <td className="py-3 px-4 text-center font-mono text-win">{d.wins}</td>
                      <td className="py-3 px-4 text-center font-mono text-loss">{losses}</td>
                      <td className="py-3 px-4 text-center">
                        <span className={cn("font-mono font-semibold", d.win_rate >= 55 ? "text-win" : d.win_rate >= 45 ? "text-draw" : "text-loss")}>
                          {d.win_rate.toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center font-mono">
                        <span className={cn(d.avg_prize_diff > 0 ? "text-win" : d.avg_prize_diff < 0 ? "text-loss" : "text-muted-foreground")}>
                          {d.avg_prize_diff > 0 ? "+" : ""}{d.avg_prize_diff.toFixed(1)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center font-mono text-muted-foreground">{d.avg_turn_count.toFixed(1)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
