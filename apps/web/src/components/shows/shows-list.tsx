"use client";

import Link from "next/link";
import { Library, FileText, Mic } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useShows } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

export function ShowsList() {
  const { data: shows = [], isLoading, error, refetch } = useShows();

  if (error) return <ErrorState error={error} onRetry={() => refetch()} />;

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full" />
        ))}
      </div>
    );
  }

  if (shows.length === 0) {
    return (
      <EmptyState
        icon={Library}
        title="No shows yet"
        description="Create your first show in the Studio."
      />
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {shows.map((show) => (
        <Link key={show.id} href={`/shows/${show.id}`}>
          <Card className="card-hover h-full">
            <CardContent className="p-5 space-y-3">
              <div className="flex items-center gap-2">
                <div className="stat-icon-wrap">
                  <Library className="h-4 w-4" />
                </div>
                <h3 className="font-semibold truncate">{show.title}</h3>
              </div>
              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <span className="inline-flex items-center gap-1">
                  <FileText className="h-3.5 w-3.5" />
                  {show.source_count} sources
                </span>
                <span className="inline-flex items-center gap-1">
                  <Mic className="h-3.5 w-3.5" />
                  {show.episode_count} episodes
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Created {formatDate(show.created_at)}
              </p>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}
