"use client";

import Link from "next/link";
import { ArrowLeft, FileText, Library } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useShow } from "@/lib/queries";
import { formatDate } from "@/lib/utils";
import { EpisodeCard } from "./episode-card";

export function ShowDetail({ showId }: { showId: string }) {
  const { data: detail, isLoading, error, refetch } = useShow(showId);

  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5">
        <Link
          href="/shows"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mb-2"
        >
          <ArrowLeft className="h-3 w-3" />
          All shows
        </Link>
        <h1 className="page-title">{detail?.show.title ?? "Show"}</h1>
        {detail && (
          <p className="text-sm text-muted-foreground mt-1.5">
            Created {formatDate(detail.show.created_at)} ·{" "}
            {detail.show.sources.length} sources · {detail.episodes.length} episodes
          </p>
        )}
      </div>

      {error ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : isLoading ? (
        <Skeleton className="h-40 w-full" />
      ) : !detail ? (
        <EmptyState icon={Library} title="Show not found" description="" />
      ) : (
        <div className="space-y-8">
          <Card>
            <CardHeader className="border-b border-border py-4 px-5">
              <CardTitle className="card-title">Sources</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {detail.show.sources.length === 0 ? (
                <EmptyState
                  icon={FileText}
                  title="No sources"
                  description="Add documents in the Studio."
                />
              ) : (
                <ul className="divide-y divide-border">
                  {detail.show.sources.map((s) => (
                    <li
                      key={s.key}
                      className="flex items-center gap-2 px-5 py-3 text-sm"
                    >
                      <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                      <span className="truncate flex-1">{s.filename}</span>
                      <span className="font-mono text-xs text-muted-foreground tabular-nums">
                        {s.size_human}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <div className="space-y-4">
            <h2 className="card-title">Episodes</h2>
            {detail.episodes.length === 0 ? (
              <EmptyState
                icon={Library}
                title="No episodes yet"
                description="Generate one in the Studio."
              />
            ) : (
              detail.episodes.map((ep) => (
                <EpisodeCard key={ep.id} showId={showId} episodeId={ep.id} />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
