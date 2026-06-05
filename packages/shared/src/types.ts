export type FileStatus = "uploading" | "complete" | "error";

export interface FileMetadata {
  key: string;
  filename: string;
  folder: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
}

export interface FileMetadataDetail {
  filename: string;
  size_bytes: number;
  size_human: string;
  mime_type: string;
  extension: string;
  md5: string;
  sha256: string;
  uploaded_at: string;
  // Image-specific
  image_width: number | null;
  image_height: number | null;
  exif: Record<string, string> | null;
  // PDF-specific
  pdf_pages: number | null;
  pdf_author: string | null;
  pdf_title: string | null;
  // Audio/Video
  duration_seconds: number | null;
  codec: string | null;
  bitrate: number | null;
}

export interface FileUploadResponse {
  key: string;
  filename: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
  metadata: FileMetadataDetail | null;
}

export interface DailyUploadCount {
  date: string;
  uploads: number;
}

export interface UploadStats {
  total_files: number;
  total_size_bytes: number;
  total_size_human: string;
  uploads_today: number;
  total_downloads: number;
}

// --- Docs to Podcast: shows, episodes, generation ---

export type EpisodeStatus = "pending" | "generating" | "ready" | "failed";

export interface ScriptLine {
  speaker: "A" | "B";
  text: string;
}

export interface SourceRef {
  key: string;
  filename: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
}

export interface Episode {
  id: string;
  show_id: string;
  title: string;
  status: EpisodeStatus;
  created_at: string;
  updated_at: string;
  host_a_name: string;
  host_b_name: string;
  voice_host_a: string;
  voice_host_b: string;
  line_count: number;
  duration_seconds: number | null;
  audio_key: string | null;
  transcript_key: string | null;
  error: string | null;
}

export interface Show {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  sources: SourceRef[];
  episode_ids: string[];
}

export interface ShowSummary {
  id: string;
  title: string;
  created_at: string;
  source_count: number;
  episode_count: number;
}

export interface ShowDetail {
  show: Show;
  episodes: Episode[];
}

export interface EpisodeDetail {
  episode: Episode;
  audio_url: string | null;
  transcript_url: string | null;
  lines: ScriptLine[];
}

export interface PodcastStats {
  total_shows: number;
  total_episodes: number;
  total_listening_minutes: number;
  total_size_bytes: number;
  total_size_human: string;
}

export interface DailyEpisodeCount {
  date: string;
  episodes: number;
}

export interface RecentEpisode {
  show_id: string;
  episode_id: string;
  show_title: string;
  episode_title: string;
  status: EpisodeStatus;
  created_at: string;
  duration_seconds: number | null;
}

export interface PublicConfig {
  host_a_name: string;
  host_b_name: string;
  voice_host_a: string;
  voice_host_b: string;
  llm_model: string;
  tts_model: string;
}
