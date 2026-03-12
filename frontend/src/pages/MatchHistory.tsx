import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import type { Match, Pagination } from "@/types/api";
import { MatchTable } from "@/components/dashboard/MatchTable";
import { ApiError, EmptyState } from "@/components/ui/api-error";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search } from "lucide-react";

export default function MatchHistory() {
  const navigate = useNavigate();
  const [matches, setMatches] = useState<Match[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const [deckFilter, setDeckFilter] = useState("");
  const [resultFilter, setResultFilter] = useState<string>("all");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { page: page.toString(), page_size: "20" };
      if (deckFilter) params.player_deck = deckFilter;
      if (resultFilter !== "all") params.result = resultFilter;
      const res = await api.getMatches(params);
      setMatches(res.data?.items ?? []);
      setPagination(res.pagination ?? null);
    } catch (err: any) {
      setError(err.message || "Failed to load matches");
      setMatches([]);
    } finally {
      setLoading(false);
    }
  }, [page, deckFilter, resultFilter]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Match History</h1>
        <p className="text-sm text-muted-foreground">Browse and filter your recorded matches</p>
      </div>

      <div className="flex flex-wrap items-end gap-3 rounded-lg border border-border bg-card p-4">
        <div className="flex-1 min-w-[180px]">
          <label className="text-xs text-muted-foreground mb-1 block">My Deck</label>
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input value={deckFilter} onChange={(e) => setDeckFilter(e.target.value)} placeholder="Filter by deck…" className="pl-8 h-9 text-sm" />
          </div>
        </div>
        <div className="min-w-[130px]">
          <label className="text-xs text-muted-foreground mb-1 block">Result</label>
          <Select value={resultFilter} onValueChange={setResultFilter}>
            <SelectTrigger className="h-9 text-sm"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="win">Win</SelectItem>
              <SelectItem value="loss">Loss</SelectItem>
              <SelectItem value="unknown">Unknown</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button variant="outline" size="sm" onClick={() => { setDeckFilter(""); setResultFilter("all"); setPage(1); }}>
          Clear
        </Button>
      </div>

      {error ? (
        <ApiError message={error} onRetry={load} />
      ) : matches.length === 0 && !loading ? (
        <EmptyState message="No matches found. Parse and save a battle log to get started." />
      ) : (
        <div className="rounded-lg border border-border bg-card">
          <MatchTable matches={matches} onRowClick={(m) => navigate(`/match/${m.match_id}`)} />
        </div>
      )}

      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Button>
          <span className="text-sm text-muted-foreground">Page {page} of {pagination.total_pages}</span>
          <Button variant="outline" size="sm" disabled={page >= pagination.total_pages} onClick={() => setPage(page + 1)}>Next</Button>
        </div>
      )}
    </div>
  );
}
