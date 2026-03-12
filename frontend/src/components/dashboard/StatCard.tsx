import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: "up" | "down" | "neutral";
  variant?: "default" | "win" | "loss" | "accent";
  className?: string;
}

const variantStyles = {
  default: "border-border",
  win: "border-win/30",
  loss: "border-loss/30",
  accent: "border-accent/30",
};

export function StatCard({ title, value, subtitle, icon: Icon, trend, variant = "default", className }: StatCardProps) {
  return (
    <div className={cn(
      "rounded-lg border bg-card p-5 animate-fade-in",
      variantStyles[variant],
      className,
    )}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-muted-foreground">{title}</span>
        {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold font-display tracking-tight text-foreground">{value}</span>
        {trend && (
          <span className={cn(
            "text-xs font-medium",
            trend === "up" && "text-win",
            trend === "down" && "text-loss",
            trend === "neutral" && "text-muted-foreground",
          )}>
            {trend === "up" ? "↑" : trend === "down" ? "↓" : "—"}
          </span>
        )}
      </div>
      {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
    </div>
  );
}
