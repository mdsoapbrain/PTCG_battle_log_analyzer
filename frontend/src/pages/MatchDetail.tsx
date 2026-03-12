import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "@/lib/api";
import type { Match } from "@/types/api";
import { ResultBadge } from "@/components/ui/result-badge";
import { StatCard } from "@/components/dashboard/StatCard";
import { ApiError } from "@/components/ui/api-error";
import { ArrowLeft, Swords, Target, ArrowUpDown, Hash } from "lucide-react";
import { format } from "date-fns";

export default function MatchDetail() {
  const { matchId } = useParams<{ matchId: string }>();
  const [match, setMatch] = useState<Match | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getMatch(matchId!);
      setMatch(res.data ?? null);
    } catch (err: any) {
      setError(err.message || "Failed to load match");
    } finally {
      setLoading(false);
    }
  }, [matchId]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return <div className="text-center py-20 text-muted-foreground">Loading…</div>;
  }

  if (error) {
    return (
      <div className="max-w-4xl space-y-6">
        <Link to="/history" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
          <ArrowLeft className="h-4 w-4" /> Back to History
        </Link>
        <ApiError message={error} onRetry={load} />
      </div>
    );
  }

  if (!match) {
    return <div className="text-center py-20 text-muted-foreground">Match not found.</div>;
  }

  return (
    <div className="max-w-4xl space-y-6">
      <Link to="/history" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="h-4 w-4" /> Back to History
      </Link>

      <div className="flex items-center gap-4">
        <ResultBadge result={match.result} className="text-sm px-3 py-1" />
        <div>
          <h1 className="text-xl font-display font-bold text-foreground">
            {match.player_name} vs {match.opponent_name}
          </h1>
          <p className="text-sm text-muted-foreground">{format(new Date(match.created_at), "PPPp")}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard title="My Deck" value={match.player_deck || "—"} icon={Swords} />
        <StatCard title="Opp Deck" value={match.opponent_deck || "—"} icon={Swords} />
        <StatCard title="Went First" value={match.went_first === null ? "Unknown" : match.went_first ? "Yes" : "No"} icon={ArrowUpDown} />
        <StatCard title="Turns" value={match.turn_count} icon={Hash} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <StatCard title="Prizes Taken" value={match.prizes_taken} variant="win" icon={Target} />
        <StatCard title="Prizes Lost" value={match.prizes_lost} variant="loss" icon={Target} />
      </div>

      {match.summary_text && (
        <div className="rounded-lg border border-border bg-card p-5">
          <h2 className="font-display font-semibold text-foreground mb-2">Summary</h2>
          <pre className="text-sm text-muted-foreground whitespace-pre-wrap font-mono leading-relaxed">{match.summary_text}</pre>
        </div>
      )}

      {match.notes && (
        <div className="rounded-lg border border-border bg-card p-5">
          <h2 className="font-display font-semibold text-foreground mb-2">Notes</h2>
          <p className="text-sm text-foreground">{match.notes}</p>
        </div>
      )}

      {match.tags && match.tags.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {match.tags.map((tag) => (
            <span key={tag} className="px-2 py-0.5 text-xs rounded bg-secondary text-secondary-foreground">{tag}</span>
          ))}
        </div>
      )}
    </div>
  );
}
