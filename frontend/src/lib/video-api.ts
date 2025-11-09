/** Video API client. */

import { apiGet, apiPost, apiPut, apiDelete, apiUploadFile } from './api-client'
import type {
  Video,
  VideoCreate,
  VideoUpdate,
  VideoListParams,
  PresignedUrlRequest,
  PresignedUrlResponse,
  DashboardStats,
} from '@/types/video'

/**
 * Get presigned URL for video playback.
 * @param videoId - Video ID
 * @returns Presigned playback URL
 */
export async function getVideoPlaybackUrl(videoId: string): Promise<string> {
  const response = await apiGet<{ url: string }>(`/videos/${videoId}/playback-url`)
  return response.url
}

/**
 * Get list of videos.
 * @param params - Query parameters for filtering and pagination
 * @returns List of videos
 */
export async function getVideos(params?: VideoListParams): Promise<Video[]> {
  return apiGet<Video[]>('/videos', {
    params: params as Record<string, string | number | boolean | undefined>
  })
}

/**
 * Get a single video by ID.
 * @param videoId - Video ID
 * @returns Video details
 */
export async function getVideo(videoId: string): Promise<Video> {
  return apiGet<Video>(`/videos/${videoId}`)
}

/**
 * Update video metadata.
 * @param videoId - Video ID
 * @param data - Fields to update
 * @returns Updated video
 */
export async function updateVideo(videoId: string, data: VideoUpdate): Promise<Video> {
  return apiPut<Video>(`/videos/${videoId}`, data)
}

/**
 * Delete a video.
 * @param videoId - Video ID
 */
export async function deleteVideo(videoId: string): Promise<void> {
  return apiDelete(`/videos/${videoId}`)
}

/**
 * Generate presigned URL for video upload.
 * @param request - Upload request details
 * @returns Presigned URL and video metadata
 */
export async function generatePresignedUrl(
  request: PresignedUrlRequest
): Promise<PresignedUrlResponse> {
  return apiPost<PresignedUrlResponse>('/videos/presigned-url', request)
}

/**
 * Create video record in database.
 * @param data - Video creation data
 * @returns Created video
 */
export async function createVideo(data: VideoCreate): Promise<Video> {
  return apiPost<Video>('/videos', data)
}

/**
 * Upload video file to S3 using presigned URL.
 * @param presignedUrl - Presigned URL from generatePresignedUrl
 * @param file - Video file to upload
 * @param onProgress - Progress callback (0-100)
 */
export async function uploadVideoFile(
  presignedUrl: string,
  file: File,
  onProgress?: (progress: number) => void
): Promise<void> {
  return apiUploadFile(presignedUrl, file, onProgress)
}

/**
 * Get dashboard statistics.
 * @returns Dashboard stats
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  return apiGet<DashboardStats>('/videos/stats')
}
