/** Export types for video export functionality. */

export type ExportStatus = "pending" | "processing" | "completed" | "failed" | "cancelled";
export type ExportType = "single" | "combined" | "clips";
export type Resolution = "720p" | "1080p" | "4k";
export type Format = "mp4" | "mov" | "webm";
export type QualityPreset = "high" | "medium" | "low";

export interface ExportSegment {
  start_time: number;
  end_time: number;
  clip_id?: string | null;
}

export interface Export {
  id: string;
  video_id: string;
  user_id: string;
  export_type: ExportType;
  resolution: Resolution;
  format: Format;
  quality_preset: QualityPreset;
  segment_selections: ExportSegment[] | null;
  status: ExportStatus;
  progress_percentage: number;
  error_message: string | null;
  output_s3_key: string | null;
  output_url: string | null;
  file_size_bytes: number | null;
  total_duration_seconds: number | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface ExportCreateRequest {
  export_type: ExportType;
  resolution: Resolution;
  format: Format;
  quality_preset: QualityPreset;
  segments: ExportSegment[];
}

export interface ExportProgress {
  export_id: string;
  status: ExportStatus;
  progress_percentage: number;
  current_stage: string | null;
  estimated_time_remaining: number | null;
  elapsed_time: number | null;
}

export interface ExportDownloadResponse {
  url: string;
  expires_at: string;
  file_size_bytes: number | null;
}

export interface ExportListResponse {
  exports: Export[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

export interface ExportSettings {
  default_resolution: Resolution;
  default_format: Format;
  default_quality: QualityPreset;
  custom_presets?: ExportPreset[];
}

export interface ExportPreset {
  name: string;
  resolution: Resolution;
  format: Format;
  quality_preset: QualityPreset;
}
