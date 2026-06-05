"use client";

import { useState } from "react";
import { Download, FileText } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { GeneratingLoader } from "@/components/ui/generating-loader";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useEpisode } from "@/lib/queries";
import { formatDate } from "@/lib/utils";
import { EpisodeStatusBadge, formatDuration } from "./episode-status-badge";

interface Props {
  showId: string;
  episodeId: string;
}

export function EpisodeCard({ showId, episodeId }: Props) {
  const [showTranscript, setShowTranscript] = useState(false);
  const { data: detail } = useEpisode(showId, episodeId);

  if (!detail) {
    return (
      <Card>
        <CardContent className="p-5">
          <GeneratingLoader size="sm" label="Loading…" />
        </CardContent>
      </Card>
    );
  }

  const { episode, audio_url, transcript_url, lines } = detail;
  const isWorking = episode.status === "pending" || episode.status === "generating";

  return (
    <Card>
      <CardHeader className="border-b border-border py-4 px-5 flex flex-row items-center justify-between gap-3">
        <div>
          <CardTitle className="card-title">{episode.title}</CardTitle>
          <p className="text-xs text-muted-foreground mt-1">
            {formatDate(episode.created_at)} · {episode.host_a_name} &amp;{" "}
            {episode.host_b_name} · {formatDuration(episode.duration_seconds)}
          </p>
        </div>
        <EpisodeStatusBadge status={episode.status} />
      </CardHeader>
      <CardContent className="p-5 space-y-4">
        {isWorking && (
          <div className="flex justify-center py-4">
            <GeneratingLoader size="md" variant="stars" label="Generating…" />
          </div>
        )}

        {episode.status === "failed" && (
          <div className="rounded-md border border-[#e42c39]/40 bg-[#e42c39]/5 p-3 text-sm text-[#e42c39]">
            {episode.error ?? "Generation failed"}
          </div>
        )}

        {episode.status === "ready" && (
          <>
            {audio_url && (
              <audio controls src={audio_url} className="w-full">
                <track kind="captions" />
              </audio>
            )}

            <div className="flex flex-wrap gap-2">
              {audio_url && (
                <Button asChild variant="outline" size="sm">
                  <a href={audio_url} download={`${episode.title}.mp3`}>
                    <Download className="h-3.5 w-3.5" />
                    Audio
                  </a>
                </Button>
              )}
              {transcript_url && (
                <Button asChild variant="outline" size="sm">
                  <a href={transcript_url}>
                    <FileText className="h-3.5 w-3.5" />
                    Transcript JSON
                  </a>
                </Button>
              )}
            </div>

            {lines.length > 0 && (
              <Collapsible open={showTranscript} onOpenChange={setShowTranscript}>
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" size="sm">
                    {showTranscript ? "Hide transcript" : "Read transcript"}
                  </Button>
                </CollapsibleTrigger>
                <CollapsibleContent className="mt-3 space-y-3">
                  {lines.map((line, i) => (
                    <p key={i} className="text-sm">
                      <span className="font-semibold text-primary">
                        {line.speaker === "A" ? episode.host_a_name : episode.host_b_name}:
                      </span>{" "}
                      <span className="text-muted-foreground">{line.text}</span>
                    </p>
                  ))}
                </CollapsibleContent>
              </Collapsible>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
