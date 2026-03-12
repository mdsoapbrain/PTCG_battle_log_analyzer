import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { StatCard } from "@/components/dashboard/StatCard";
import { MatchTable } from "@/components/dashboard/MatchTable";
import { DeckWinRateChart } from "@/components/dashboard/DeckWinRateChart";
import { ApiError, EmptyState } from "@/components/ui/api-error";
import { api } from "@/lib/api";
import type { OverviewStats, GoFirstStats, DeckStat, Match } from "@/types/api";
import { Trophy, Target, Hash, ArrowUpDown, Swords } from "lucide-react";

export default function Dashboard() {
  const navigate = useNavigate();
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [goFirst, setGoFirst] = useState<GoFirstStats | null>(null);
  const [deckStats, setDeckStats] = useState<DeckStat[] | null>(null);
  const [recent, setRecent] = useState<Match[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ov, gf, ds, rm] = await Promise.all([
        api.getOverviewStats(),
        api.getGoFirstStats(),
        api.getDeckStats(),
        api.getMatches({ page: "1", page_size: "5" }),
      ]);
      setOverview(ov.data ?? null);
      setGoFirst(gf.data ?? null);
      setDeckStats(ds.data ?? null);
      setRecent(rm.data?.items ?? null);
    } catch (err: any) {
      setError(err.message || "Failed to connect to backend");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return <div className="text-center py-20 text-muted-foreground">Loading dashboard…</div>;
  }

  if (error) {
    return (
      <div className="max-w-6xl space-y-6">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Your competitive overview</p>
        </div>
        <ApiError message={error} onRetry={load} />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Your competitive overview</p>
      </div>

      {overview && goFirst ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <StatCard title="Total Matches" value={overview.total_matches} icon={Hash} />
          <StatCard title="Win Rate" value={`${overview.win_rate}%`} icon={Trophy} variant={overview.win_rate >= 50 ? "win" : "loss"} />
          <StatCard title="Go First WR" value={`${goFirst.first_win_rate}%`} icon={ArrowUpDown} subtitle={`${goFirst.first_matches} games`} />
          <StatCard title="Go Second WR" value={`${goFirst.second_win_rate}%`} icon={ArrowUpDown} subtitle={`${goFirst.second_matches} games`} />
          <StatCard title="Avg Prize Diff" value={overview.average_prize_differential > 0 ? `+${overview.average_prize_differential}` : overview.average_prize_differential.toString()} icon={Target} variant={overview.average_prize_differential > 0 ? "win" : "loss"} />
          <StatCard title="Avg Turns" value={overview.average_turn_count} icon={Swords} />
        </div>
      ) : (
        <EmptyState message="No stats available yet. Parse and save some matches to get started." />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="rounded-lg border border-border bg-card p-5">
          <h2 className="font-display font-semibold text-foreground mb-4">Deck Win Rates</h2>
          {deckStats && deckStats.length > 0 ? <DeckWinRateChart data={deckStats} /> : <EmptyState message="No deck data yet." />}
        </div>

        <div className="rounded-lg border border-border bg-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display font-semibold text-foreground">Recent Matches</h2>
            <button onClick={() => navigate("/history")} className="text-xs text-primary hover:underline">View all →</button>
          </div>
          {recent && recent.length > 0 ? (
            <MatchTable matches={recent.slice(0, 5)} onRowClick={(m) => navigate(`/match/${m.match_id}`)} compact />
          ) : (
            <EmptyState message="No matches recorded yet." />
          )}
        </div>
      </div>
    </div>
  );
}
