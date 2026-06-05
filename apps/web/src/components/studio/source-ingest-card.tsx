"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";
import type { FileRejection } from "react-dropzone";
import { FileText, X } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dropzone } from "@/components/upload/dropzone";
import { UploadProgress, type UploadItem } from "@/components/upload/upload-progress";
import { useShow, useUploadShowSource } from "@/lib/queries";
import { humanizeBytes } from "@/lib/utils";

interface Props {
  showId: string;
}

// Reuses the kept generic dropzone + progress components for show-scoped
// ingestion. Source docs land under `shows/{id}/sources/` (the backend
// restricts the type allowlist to PDF / text / markdown).
export function SourceIngestCard({ showId }: Props) {
  const [items, setItems] = useState<UploadItem[]>([]);
  const { data: detail } = useShow(showId);
  const uploadSource = useUploadShowSource(showId);

  const handleRejected = useCallback((rejections: FileRejection[]) => {
    for (const rejection of rejections) {
      const errors = rejection.errors.map((e) =>
        e.code === "file-too-large"
          ? `exceeds 100MB limit (${humanizeBytes(rejection.file.size)})`
          : e.message,
      );
      toast.error(`${rejection.file.name}: ${errors.join(", ")}`);
    }
  }, []);

  const handleSelected = useCallback(
    (files: File[]) => {
      const newItems: UploadItem[] = files.map((file) => ({
        id: `${file.name}-${Date.now()}-${Math.random()}`,
        file,
        progress: 0,
        status: "uploading" as const,
      }));
      setItems((prev) => [...prev, ...newItems]);

      const run = async () => {
        for (const item of newItems) {
          try {
            await uploadSource.mutateAsync({
              file: item.file,
              onProgress: (percent) =>
                setItems((prev) =>
                  prev.map((i) => (i.id === item.id ? { ...i, progress: percent } : i)),
                ),
            });
            setItems((prev) =>
              prev.map((i) =>
                i.id === item.id ? { ...i, status: "complete", progress: 100 } : i,
              ),
            );
            toast.success(`${item.file.name} added`);
          } catch (err) {
            const message = err instanceof Error ? err.message : "Upload failed";
            setItems((prev) =>
              prev.map((i) =>
                i.id === item.id ? { ...i, status: "error", error: message } : i,
              ),
            );
            toast.error(`Failed to add ${item.file.name}: ${message}`);
          }
        }
      };
      run().catch(console.error);
    },
    [uploadSource],
  );

  const sources = detail?.show.sources ?? [];

  return (
    <Card>
      <CardHeader className="border-b border-border py-4 px-5">
        <CardTitle className="card-title">2. Add source documents</CardTitle>
      </CardHeader>
      <CardContent className="p-5 space-y-4">
        <p className="text-xs text-muted-foreground">
          PDF, plain text, or Markdown. The LLM reads these to write the script.
        </p>
        <Dropzone onFilesSelected={handleSelected} onFilesRejected={handleRejected} />
        <UploadProgress items={items} />

        {sources.length > 0 && (
          <ul className="divide-y divide-border rounded-md border border-border">
            {sources.map((s) => (
              <li key={s.key} className="flex items-center gap-2 px-3 py-2 text-sm">
                <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                <span className="truncate flex-1">{s.filename}</span>
                <span className="font-mono text-xs text-muted-foreground tabular-nums">
                  {s.size_human}
                </span>
              </li>
            ))}
          </ul>
        )}

        {sources.length === 0 && (
          <p className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
            <X className="h-3.5 w-3.5" />
            No sources yet — add at least one before generating.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
