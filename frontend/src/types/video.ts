/** Video types. */

import type { VideoStatus } from './video-status'

export interface Video {
  id: string
  user_id: string
  title: string
  description: string | null
  file_size: number | null
  format: string | null
  duration: number | null // Duration in seconds
  resolution: string | null // e.g., "1920x1080"
  s3_key: string | null
  cloudfront_url: string | null
  thumbnail_url: string | null
  status: VideoStatus
  created_at: string
  updated_at: string
}

export interface PresignedUrlRequest {
  filename: string
  file_size: number
  content_type: string
}

export interface PresignedUrlResponse {
  presigned_url: string
  video_id: string
  s3_key: string
}

export interface VideoCreate {
  video_id: string
  title: string
  description?: string | null
  s3_key: string
}

export interface VideoUpdate {
  title?: string
  description?: string | null
}

export interface VideoListParams {
  status?: VideoStatus
  search?: string
  sort_by?: 'created_at' | 'title' | 'duration'
  sort_order?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

export interface DashboardStats {
  total_videos: number
  storage_used_gb: number
  processing_time_minutes: number
  recent_activity_count: number
}

