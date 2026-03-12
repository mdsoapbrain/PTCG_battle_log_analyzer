import { Match } from "@/types/api";
import { cn } from "@/lib/utils";
import { format } from "date-fns";

interface MatchTableProps {
  matches: Match[];
  onRowClick?: (match: Match) => void;
  compact?: boolean;
}

export function MatchTable({ matches, onRowClick, compact }: MatchTableProps) {
  if (matches.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-sm">No matches found.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-muted-foreground">
            <th className="text-left py-3 px-3 font-medium">Result</th>
            <th className="text-left py-3 px-3 font-medium">My Deck</th>
            <th className="text-left py-3 px-3 font-medium">Opponent</th>
            {!compact && <th className="text-left py-3 px-3 font-medium">Opp. Deck</th>}
            <th className="text-center py-3 px-3 font-medium">1st</th>
            <th className="text-center py-3 px-3 font-medium">Prizes</th>
            {!compact && <th className="text-center py-3 px-3 font-medium">Turns</th>}
            <th className="text-right py-3 px-3 font-medium">Date</th>
          </tr>
        </thead>
        <tbody>
          {matches.map((m) => (
            <tr
              key={m.match_id}
              onClick={() => onRowClick?.(m)}
              className={cn(
                "border-b border-border/50 transition-colors",
                onRowClick && "cursor-pointer hover:bg-secondary/50",
              )}
            >
              <td className="py-3 px-3">
                <span className={cn(
                  "inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider",
                  m.result === "win" && "bg-win/15 text-win",
                  m.result === "loss" && "bg-loss/15 text-loss",
                  m.result === "unknown" && "bg-draw/15 text-draw",
                )}>
                  {m.result}
                </span>
              </td>
              <td className="py-3 px-3 font-medium text-foreground">{m.player_deck || "—"}</td>
              <td className="py-3 px-3 text-muted-foreground">{m.opponent_name}</td>
              {!compact && <td className="py-3 px-3 text-muted-foreground">{m.opponent_deck || "—"}</td>}
              <td className="py-3 px-3 text-center">
                <span className={cn("text-xs", m.went_first === true ? "text-primary" : "text-muted-foreground")}>
                  {m.went_first === true ? "Yes" : m.went_first === false ? "No" : "-"}
                </span>
              </td>
              <td className="py-3 px-3 text-center font-mono text-xs">
                <span className="text-win">{m.prizes_taken}</span>
                <span className="text-muted-foreground">–</span>
                <span className="text-loss">{m.prizes_lost}</span>
              </td>
              {!compact && <td className="py-3 px-3 text-center font-mono text-xs">{m.turn_count}</td>}
              <td className="py-3 px-3 text-right text-xs text-muted-foreground">
                {format(new Date(m.created_at), "MMM d, HH:mm")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
