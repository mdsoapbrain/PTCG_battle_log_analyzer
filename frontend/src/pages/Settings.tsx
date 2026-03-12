import { useAuth } from "@/contexts/AuthContext";
import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, XCircle, User, Shield, Wifi } from "lucide-react";

export default function SettingsPage() {
  const { user, isAuthenticated } = useAuth();
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const apiBase = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8001").replace(/\/+$/, "");

  useEffect(() => {
    fetch(`${apiBase}/health`)
      .then((r) => setBackendStatus(r.ok ? "online" : "offline"))
      .catch(() => setBackendStatus("offline"));
  }, [apiBase]);

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Settings</h1>
        <p className="text-sm text-muted-foreground">Profile and configuration</p>
      </div>

      {/* User info */}
      <div className="rounded-lg border border-border bg-card p-5 space-y-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-secondary flex items-center justify-center">
            <User className="h-5 w-5 text-muted-foreground" />
          </div>
          <div>
            <p className="font-medium text-foreground">{user?.name || user?.email || "Guest"}</p>
            <p className="text-sm text-muted-foreground">{user?.email}</p>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="rounded-lg border border-border bg-card p-5 space-y-3">
        <h2 className="font-display font-semibold text-foreground">Status</h2>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Authentication</span>
          </div>
          <Badge variant={isAuthenticated ? "default" : "secondary"} className={isAuthenticated ? "bg-win/15 text-win border-0" : ""}>
            {isAuthenticated ? "Authenticated" : "Not signed in"}
          </Badge>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <Wifi className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Backend API</span>
          </div>
          <div className="flex items-center gap-1.5">
            {backendStatus === "checking" && <span className="text-xs text-muted-foreground">Checking…</span>}
            {backendStatus === "online" && <><CheckCircle className="h-3.5 w-3.5 text-win" /><span className="text-xs text-win">Online</span></>}
            {backendStatus === "offline" && <><XCircle className="h-3.5 w-3.5 text-loss" /><span className="text-xs text-loss">Offline</span></>}
          </div>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <Wifi className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">API Base URL</span>
          </div>
          <span className="text-xs text-muted-foreground truncate max-w-[260px]">{apiBase}</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Auth Mode</span>
          </div>
          <Badge variant="secondary">Stub</Badge>
        </div>
      </div>

      {/* Future */}
      <div className="rounded-lg border border-dashed border-border bg-card/50 p-5">
        <h2 className="font-display font-semibold text-muted-foreground mb-2">Coming Soon</h2>
        <ul className="text-sm text-muted-foreground space-y-1.5">
          <li>• Data export (CSV, JSON)</li>
          <li>• Supabase JWT authentication</li>
          <li>• Premium analytics features</li>
          <li>• Deck archetype auto-detection</li>
        </ul>
      </div>
    </div>
  );
}
