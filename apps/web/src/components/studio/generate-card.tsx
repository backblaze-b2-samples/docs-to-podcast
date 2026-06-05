"use client";

import { useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Mic, ArrowRight } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { GeneratingLoader } from "@/components/ui/generating-loader";
import { ErrorState } from "@/components/ui/error-state";
import { useCreateEpisode, useEpisode, useShow } from "@/lib/queries";

interface Props {
  showId: string;
}

export function GenerateCard({ showId }: Props) {
  const [episodeId, setEpisodeId] = useState<string | undefined>(undefined);
  const { data: detail } = useShow(showId);
  const createEpisode = useCreateEpisode(showId);
  const { data: episodeDetail, error } = useEpisode(showId, episodeId);

  const hasSources = (detail?.show.sources.length ?? 0) > 0;
  const status = episodeDetail?.episode.status;
  const isWorking = status === "pending" || status === "generating";

  const handleGenerate = async () => {
    try {
      const created = await createEpisode.mutateAsync(undefined);
      setEpisodeId(created.episode.id);
      toast.success("Generation started");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to start generation");
    }
  };

  return (
    <Card>
      <CardHeader className="border-b border-border py-4 px-5">
        <CardTitle className="card-title">3. Generate episode</CardTitle>
      </CardHeader>
      <CardContent className="p-5 space-y-4">
        {!episodeId && (
          <Button
            onClick={handleGenerate}
            disabled={!hasSources || createEpisode.isPending}
          >
            <Mic className="h-4 w-4" />
            {createEpisode.isPending ? "Starting..." : "Generate episode"}
          </Button>
        )}

        {error && <ErrorState error={error} />}

        {isWorking && (
          <div className="flex flex-col items-center gap-3 py-6">
            <GeneratingLoader size="lg" variant="stars" label="Writing script & synthesizing audio…" />
          </div>
        )}

        {status === "failed" && (
          <div className="rounded-md border border-[#e42c39]/40 bg-[#e42c39]/5 p-3 text-sm text-[#e42c39]">
            Generation failed: {episodeDetail?.episode.error ?? "unknown error"}
          </div>
        )}

        {status === "ready" && (
          <div className="space-y-3">
            <p className="text-sm font-medium text-[var(--success)]">
              Episode ready.
            </p>
            {episodeDetail?.audio_url && (
              <audio controls src={episodeDetail.audio_url} className="w-full">
                <track kind="captions" />
              </audio>
            )}
            <Button asChild variant="outline" size="sm">
              <Link href={`/shows/${showId}`}>
                Open in Shows
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
