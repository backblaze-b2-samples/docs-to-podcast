import type { EpisodeStatus } from "@docs-to-podcast/shared";

// Single source of truth for how an episode status is rendered, reused by the
// dashboard table, the Shows library, and the Studio screen.
const STATUS_META: Record<
  EpisodeStatus,
  { label: string; dot: string; text: string }
> = {
  pending: { label: "Pending", dot: "bg-muted-foreground", text: "text-muted-foreground" },
  generating: { label: "Generating", dot: "bg-[var(--blaze-amber)]", text: "text-muted-foreground" },
  ready: { label: "Ready", dot: "bg-[var(--success)]", text: "text-muted-foreground" },
  failed: { label: "Failed", dot: "bg-[#e42c39]", text: "text-[#e42c39]" },
};

export function formatDuration(seconds: number | null): string {
  if (!seconds || seconds <= 0) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function EpisodeStatusBadge({ status }: { status: EpisodeStatus }) {
  const meta = STATUS_META[status];
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs ${meta.text}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />
      {meta.label}
    </span>
  );
}
