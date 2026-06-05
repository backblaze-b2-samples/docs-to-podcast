"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { usePublicConfig } from "@/lib/queries";

// Read-only view of the podcast generation defaults. These come from the
// backend env (HOST_*_NAME, TTS_VOICE_*, LLM_MODEL, TTS_MODEL). No secrets
// are ever returned by /config, so nothing sensitive is rendered here.
export function PodcastDefaults() {
  const { data: config, isLoading } = usePublicConfig();

  const rows: { label: string; value: string | undefined }[] = [
    { label: "Host A", value: config && `${config.host_a_name} (${config.voice_host_a})` },
    { label: "Host B", value: config && `${config.host_b_name} (${config.voice_host_b})` },
    { label: "Script model", value: config?.llm_model },
    { label: "Voice model", value: config?.tts_model },
  ];

  return (
    <Card>
      <CardHeader className="border-b border-border py-4 px-5">
        <CardTitle className="card-title">Podcast defaults</CardTitle>
      </CardHeader>
      <CardContent className="p-5 space-y-3">
        <p className="text-xs text-muted-foreground">
          Read-only. Change these by editing the corresponding values in your
          <code className="font-mono text-xs"> .env </code>
          and restarting the API.
        </p>
        <dl className="divide-y divide-border rounded-md border border-border">
          {rows.map((row) => (
            <div key={row.label} className="flex items-center justify-between px-3 py-2">
              <dt className="text-sm text-muted-foreground">{row.label}</dt>
              <dd className="text-sm font-mono tabular-nums">
                {isLoading ? <Skeleton className="h-4 w-32" /> : row.value ?? "—"}
              </dd>
            </div>
          ))}
        </dl>
      </CardContent>
    </Card>
  );
}
