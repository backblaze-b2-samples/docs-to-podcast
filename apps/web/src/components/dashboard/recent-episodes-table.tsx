"use client";

import Link from "next/link";
import { ArrowRight, Inbox } from "lucide-react";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useRecentEpisodes } from "@/lib/queries";
import { formatDate } from "@/lib/utils";
import {
  EpisodeStatusBadge,
  formatDuration,
} from "@/components/shows/episode-status-badge";

export function RecentEpisodesTable() {
  const { data: episodes = [], isLoading, error, refetch } = useRecentEpisodes(10);

  return (
    <Card>
      <CardHeader className="border-b border-border py-4 px-5">
        <CardTitle className="card-title">Recent Episodes</CardTitle>
        <CardAction className="self-center">
          <Link
            href="/shows"
            className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            View all
            <ArrowRight className="h-3 w-3" />
          </Link>
        </CardAction>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : episodes.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="No episodes yet"
            description="Head to Studio to create your first episode."
          />
        ) : (
          <Table className="table-fixed">
            <TableHeader>
              <TableRow className="bg-muted/40 hover:bg-muted/40">
                <TableHead className="w-[32%] text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Episode
                </TableHead>
                <TableHead className="w-[24%] text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Show
                </TableHead>
                <TableHead className="w-[12%] text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Length
                </TableHead>
                <TableHead className="w-[16%] text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Created
                </TableHead>
                <TableHead className="w-[16%] text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Status
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {episodes.map((ep) => (
                <TableRow key={ep.episode_id} className="table-row-hover">
                  <TableCell className="font-medium">
                    <Link
                      href={`/shows/${ep.show_id}`}
                      className="truncate hover:underline"
                    >
                      {ep.episode_title}
                    </Link>
                  </TableCell>
                  <TableCell className="text-muted-foreground truncate">
                    {ep.show_title}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground tabular-nums whitespace-nowrap">
                    {formatDuration(ep.duration_seconds)}
                  </TableCell>
                  <TableCell className="text-muted-foreground whitespace-nowrap">
                    {formatDate(ep.created_at)}
                  </TableCell>
                  <TableCell className="whitespace-nowrap">
                    <EpisodeStatusBadge status={ep.status} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
