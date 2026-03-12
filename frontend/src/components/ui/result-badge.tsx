import { cn } from "@/lib/utils";

type Result = "win" | "loss" | "unknown";

interface ResultBadgeProps {
  result: Result;
  className?: string;
}

export function ResultBadge({ result, className }: ResultBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold uppercase tracking-wider",
        result === "win" && "bg-win/15 text-win",
        result === "loss" && "bg-loss/15 text-loss",
        result === "unknown" && "bg-draw/15 text-draw",
        className,
      )}
    >
      {result}
    </span>
  );
}
