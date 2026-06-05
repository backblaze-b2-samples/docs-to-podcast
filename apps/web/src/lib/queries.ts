"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ApiError,
  createEpisode,
  createShow,
  deleteFile,
  getEpisode,
  getFiles,
  getFileStats,
  getGenerationActivity,
  getPodcastStats,
  getPublicConfig,
  getPreviewUrl,
  getRecentEpisodes,
  getShow,
  getShows,
  getUploadActivity,
  uploadShowSource,
} from "@/lib/api-client";
import type { EpisodeDetail, FileMetadata } from "@docs-to-podcast/shared";

// Single source of truth for query keys. Keep these tightly scoped so that
// invalidating "files" doesn't blow away unrelated caches, and so an IDE
// "find usages" of `qk.files` reveals every consumer.
export const qk = {
  all: ["b2"] as const,
  files: (prefix?: string, limit?: number) =>
    [...qk.all, "files", prefix ?? "", limit ?? 100] as const,
  stats: () => [...qk.all, "stats"] as const,
  uploadActivity: (days: number) =>
    [...qk.all, "stats", "activity", days] as const,
  preview: (key: string) => [...qk.all, "preview", key] as const,
  shows: () => [...qk.all, "shows"] as const,
  show: (id: string) => [...qk.all, "show", id] as const,
  episode: (showId: string, episodeId: string) =>
    [...qk.all, "episode", showId, episodeId] as const,
  podcastStats: () => [...qk.all, "dashboard", "stats"] as const,
  recentEpisodes: (limit: number) =>
    [...qk.all, "dashboard", "recent-episodes", limit] as const,
  generationActivity: (days: number) =>
    [...qk.all, "dashboard", "activity", days] as const,
  config: () => [...qk.all, "config"] as const,
};

export function useFiles(prefix = "", limit = 100) {
  return useQuery<FileMetadata[], ApiError>({
    queryKey: qk.files(prefix, limit),
    queryFn: () => getFiles(prefix, limit),
  });
}

export function useFileStats() {
  return useQuery({
    queryKey: qk.stats(),
    queryFn: getFileStats,
  });
}

export function useUploadActivity(days = 7) {
  return useQuery({
    queryKey: qk.uploadActivity(days),
    queryFn: () => getUploadActivity(days),
  });
}

// Presigned preview URL — only fetched when `enabled` is true (e.g., when
// the dialog opens for a specific file). Kept short-lived (60s) because
// the URL itself has a presigned expiry and is cheap to regenerate.
export function usePreviewUrl(key: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: qk.preview(key ?? ""),
    queryFn: () => getPreviewUrl(key as string),
    enabled: enabled && !!key,
    staleTime: 60_000,
  });
}

export function useDeleteFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fileKey: string) => deleteFile(fileKey),
    // After delete, blow away every cached file list + stats. Cheap and
    // correct — the dashboard re-fetches lazily as components remount.
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.all });
    },
  });
}

// --- Shows / episodes ---

export function useShows() {
  return useQuery({ queryKey: qk.shows(), queryFn: getShows });
}

export function useShow(showId: string | undefined) {
  return useQuery({
    queryKey: qk.show(showId ?? ""),
    queryFn: () => getShow(showId as string),
    enabled: !!showId,
  });
}

export function useCreateShow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (title: string) => createShow(title),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.shows() }),
  });
}

export function useUploadShowSource(showId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ file, onProgress }: { file: File; onProgress?: (p: number) => void }) =>
      uploadShowSource(showId, file, onProgress),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.show(showId) }),
  });
}

export function useCreateEpisode(showId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (title?: string) => createEpisode(showId, title),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.show(showId) });
      qc.invalidateQueries({ queryKey: qk.podcastStats() });
    },
  });
}

// Polls episode status while it is pending/generating, then stops. The UI
// shows the blaze generating-loader during the "generating" phase.
export function useEpisode(
  showId: string | undefined,
  episodeId: string | undefined,
) {
  return useQuery<EpisodeDetail, ApiError>({
    queryKey: qk.episode(showId ?? "", episodeId ?? ""),
    queryFn: () => getEpisode(showId as string, episodeId as string),
    enabled: !!showId && !!episodeId,
    refetchInterval: (query) => {
      const status = query.state.data?.episode.status;
      return status === "pending" || status === "generating" ? 2500 : false;
    },
  });
}

// --- Podcast dashboard ---

export function usePodcastStats() {
  return useQuery({ queryKey: qk.podcastStats(), queryFn: getPodcastStats });
}

export function useRecentEpisodes(limit = 10) {
  return useQuery({
    queryKey: qk.recentEpisodes(limit),
    queryFn: () => getRecentEpisodes(limit),
  });
}

export function useGenerationActivity(days = 7) {
  return useQuery({
    queryKey: qk.generationActivity(days),
    queryFn: () => getGenerationActivity(days),
  });
}

export function usePublicConfig() {
  return useQuery({ queryKey: qk.config(), queryFn: getPublicConfig });
}
