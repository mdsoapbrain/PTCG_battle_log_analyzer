import { useState } from "react";
import { api } from "@/lib/api";
import type { ParsedLog } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ResultBadge } from "@/components/ui/result-badge";
import { FileText, Loader2, Check, AlertCircle } from "lucide-react";
import { toast } from "sonner";

type Status = "idle" | "parsing" | "parsed" | "saving" | "saved" | "error";

export default function ParseLog() {
  const [rawLog, setRawLog] = useState("");
  const [playerName, setPlayerName] = useState(localStorage.getItem("player_name") || "Neurologist2024");
  const [parsed, setParsed] = useState<ParsedLog | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [errorMsg, setErrorMsg] = useState("");

  // Metadata
  const [myDeck, setMyDeck] = useState("");
  const [oppDeck, setOppDeck] = useState("");
  const [notes, setNotes] = useState("");

  const handleParse = async () => {
    if (!rawLog.trim()) return;
    setStatus("parsing");
    setErrorMsg("");
    try {
      localStorage.setItem("player_name", playerName);
      const res = await api.parseLog(rawLog, playerName || undefined);
      if (res.data) {
        setParsed(res.data);
        setStatus("parsed");
        toast.success("Log parsed successfully");
      }
    } catch (err: any) {
      setStatus("error");
      setErrorMsg(err.message || "Failed to parse log");
      toast.error("Parse failed");
    }
  };

  const handleSave = async () => {
    if (!parsed) return;
    setStatus("saving");
    try {
      await api.saveMatch({
        raw_log: rawLog,
        player_name: playerName || undefined,
        player_deck: myDeck || undefined,
        opponent_deck: oppDeck || undefined,
        notes: notes || undefined,
      });
      setStatus("saved");
      toast.success("Match saved!");
    } catch (err: any) {
      setStatus("error");
      setErrorMsg(err.message || "Failed to save match");
      toast.error("Save failed");
    }
  };

  const reset = () => {
    setRawLog("");
    setParsed(null);
    setStatus("idle");
    setMyDeck("");
    setOppDeck("");
    setNotes("");
    setErrorMsg("");
  };

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Parse Battle Log</h1>
        <p className="text-sm text-muted-foreground">Paste your raw PTCG Live battle log below</p>
      </div>

      {/* Input area */}
      <div className="rounded-lg border border-border bg-card p-5">
        <Label htmlFor="playername">Player Name</Label>
        <Input
          id="playername"
          value={playerName}
          onChange={(e) => setPlayerName(e.target.value)}
          placeholder="Neurologist2024"
          className="mt-2 mb-4"
          disabled={status === "parsing" || status === "saved"}
        />

        <Label htmlFor="rawlog">Raw Battle Log</Label>
        <Textarea
          id="rawlog"
          value={rawLog}
          onChange={(e) => setRawLog(e.target.value)}
          placeholder="Paste your full battle log here..."
          className="mt-2 min-h-[200px] font-mono text-xs"
          disabled={status === "parsing" || status === "saved"}
        />
        <div className="flex items-center gap-3 mt-4">
          <Button onClick={handleParse} disabled={!rawLog.trim() || status === "parsing" || status === "saved"}>
            {status === "parsing" ? <><Loader2 className="h-4 w-4 animate-spin" /> Parsing…</> : <><FileText className="h-4 w-4" /> Parse Log</>}
          </Button>
          {(status === "parsed" || status === "saved") && (
            <Button variant="outline" onClick={reset}>Parse Another</Button>
          )}
        </div>
      </div>

      {/* Error */}
      {status === "error" && (
        <div className="flex items-center gap-2 rounded-lg border border-loss/30 bg-loss/5 p-4 text-sm text-loss">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {errorMsg}
        </div>
      )}

      {/* Parsed preview */}
      {parsed && (
        <div className="rounded-lg border border-primary/20 bg-card p-5 space-y-5 animate-fade-in">
          <h2 className="font-display font-semibold text-foreground">Parsed Result</h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Player</span>
              <p className="font-medium text-foreground">{parsed.player_name}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Opponent</span>
              <p className="font-medium text-foreground">{parsed.opponent_name}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Result</span>
              <p><ResultBadge result={parsed.winner === "You" ? "win" : parsed.winner === "Opp" ? "loss" : "unknown"} /></p>
            </div>
            <div>
              <span className="text-muted-foreground">Went First</span>
              <p className="font-medium text-foreground">{parsed.went_first === null ? "Unknown" : parsed.went_first ? "Yes" : "No"}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Turns</span>
              <p className="font-mono font-medium text-foreground">{parsed.total_turns}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Prizes</span>
              <p className="font-mono font-medium">
                <span className="text-win">{parsed.prizes_taken}</span>
                <span className="text-muted-foreground"> – </span>
                <span className="text-loss">{parsed.prizes_lost}</span>
              </p>
            </div>
            <div>
              <span className="text-muted-foreground">First KO</span>
              <p className="font-medium text-foreground">{parsed.first_ko_by || "—"}</p>
            </div>
          </div>

          {parsed.timeline_markdown && (
            <div className="rounded border border-border bg-secondary/30 p-4">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Turn Timeline</h3>
              <pre className="text-xs text-foreground whitespace-pre-wrap font-mono leading-relaxed">{parsed.timeline_markdown}</pre>
            </div>
          )}

          {parsed.prize_table_markdown && (
            <div className="rounded border border-border bg-secondary/30 p-4">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">KO + Prize Tracker</h3>
              <pre className="text-xs text-foreground whitespace-pre-wrap font-mono leading-relaxed">{parsed.prize_table_markdown}</pre>
            </div>
          )}

          {parsed.competitive_summary_markdown && (
            <div className="rounded border border-border bg-secondary/30 p-4">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Competitive Summary</h3>
              <pre className="text-xs text-foreground whitespace-pre-wrap font-mono leading-relaxed">{parsed.competitive_summary_markdown}</pre>
            </div>
          )}

          {/* Metadata */}
          <div className="border-t border-border pt-5">
            <h3 className="font-display font-semibold text-foreground mb-3">Add Metadata</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="mydeck">My Deck</Label>
                <Input id="mydeck" value={myDeck} onChange={(e) => setMyDeck(e.target.value)} placeholder="e.g., Charizard ex" className="mt-1" />
              </div>
              <div>
                <Label htmlFor="oppdeck">Opponent Deck</Label>
                <Input id="oppdeck" value={oppDeck} onChange={(e) => setOppDeck(e.target.value)} placeholder="e.g., Lugia VSTAR" className="mt-1" />
              </div>
              <div>
                <Label htmlFor="notes">Notes</Label>
                <Input id="notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Any observations…" className="mt-1" />
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button onClick={handleSave} disabled={status === "saving" || status === "saved"} className="gradient-primary">
              {status === "saving" ? <><Loader2 className="h-4 w-4 animate-spin" /> Saving…</> : status === "saved" ? <><Check className="h-4 w-4" /> Saved!</> : "Save Match"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
