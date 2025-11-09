/** API client for video operations. */

import { apiRequest, uploadFile } from "./api-client";
import type {
  Video,
  PresignedUrlRequest,
  PresignedUrlResponse,
  VideoCreate,
  VideoUpdate,
  VideoListParams,
  DashboardStats,
} from "@/types/video";

/**
 * Get presigned URL for video upload.
 */
export async function getPresignedUrl(
  data: PresignedUrlRequest,
): Promise<PresignedUrlResponse> {
  return apiRequest<PresignedUrlResponse>("/api/v1/videos/presigned-url", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Upload video to S3 using presigned URL.
 */
export async function uploadToS3(
  presignedUrl: string,
  file: File,
  onProgress?: (progress: number) => void,
): Promise<void> {
  return uploadFile(presignedUrl, file, onProgress);
}

/**
 * Create video record after upload.
 */
export async function createVideoRecord(data: VideoCreate): Promise<Video> {
  return apiRequest<Video>("/api/v1/videos", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Get video by ID.
 */
export async function getVideo(videoId: string): Promise<Video> {
  return apiRequest<Video>(`/api/v1/videos/${videoId}`, {
    method: "GET",
  });
}

/**
 * Get video playback URL.
 */
export async function getVideoPlaybackUrl(videoId: string): Promise<string> {
  const video = await getVideo(videoId);
  return video.cloudfront_url || "";
}

/**
 * Update video.
 */
export async function updateVideo(
  videoId: string,
  data: VideoUpdate,
): Promise<Video> {
  return apiRequest<Video>(`/api/v1/videos/${videoId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Delete video.
 */
export async function deleteVideo(videoId: string): Promise<void> {
  return apiRequest<void>(`/api/v1/videos/${videoId}`, {
    method: "DELETE",
  });
}

/**
 * List videos.
 */
export async function listVideos(
  params?: VideoListParams,
): Promise<{ videos: Video[]; total: number }> {
  const searchParams = new URLSearchParams();

  if (params?.status) searchParams.append("status", params.status);
  if (params?.search) searchParams.append("search", params.search);
  if (params?.sort_by) searchParams.append("sort_by", params.sort_by);
  if (params?.sort_order) searchParams.append("sort_order", params.sort_order);
  if (params?.limit) searchParams.append("limit", params.limit.toString());
  if (params?.offset) searchParams.append("offset", params.offset.toString());

  const query = searchParams.toString() ? `?${searchParams.toString()}` : "";

  return apiRequest<{ videos: Video[]; total: number }>(
    `/api/v1/videos${query}`,
    {
      method: "GET",
    },
  );
}

/**
 * Get dashboard stats.
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  return apiRequest<DashboardStats>("/api/v1/videos/stats", {
    method: "GET",
  });
}
