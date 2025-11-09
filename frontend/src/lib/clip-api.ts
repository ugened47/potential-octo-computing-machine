/** API client for clip management operations. */

import { apiRequest } from "./api-client";

export interface KeywordMatch {
  id: string;
  start: number;
  end: number;
  excerpt: string;
  confidence: number;
}

export interface SearchKeywordResponse {
  matches: KeywordMatch[];
  total_matches: number;
}

export interface Clip {
  id: string;
  video_id: string;
  title: string;
  start: number;
  end: number;
  duration: number;
  url: string;
  thumbnail_url?: string;
  created_at: string;
}

export interface CreateClipRequest {
  start: number;
  end: number;
  title?: string;
}

export interface CreateClipResponse {
  clip: Clip;
  job_id: string;
}

export interface ClipProgressResponse {
  status: "pending" | "processing" | "completed" | "failed";
  progress: number;
  message?: string;
  clip?: Clip;
}

/**
 * Search for keyword in video transcript.
 */
export async function searchKeyword(
  videoId: string,
  keyword: string,
  contextWindow: number = 5,
): Promise<SearchKeywordResponse> {
  const params = new URLSearchParams({
    keyword,
    context_window: contextWindow.toString(),
  });

  return apiRequest<SearchKeywordResponse>(
    `/api/v1/videos/${videoId}/clips/search?${params.toString()}`,
    { method: "GET" },
  );
}

/**
 * Create a new clip from video.
 */
export async function createClip(
  videoId: string,
  data: CreateClipRequest,
): Promise<CreateClipResponse> {
  return apiRequest<CreateClipResponse>(`/api/v1/videos/${videoId}/clips`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Get all clips for a video.
 */
export async function getClips(videoId: string): Promise<{ clips: Clip[] }> {
  return apiRequest<{ clips: Clip[] }>(`/api/v1/videos/${videoId}/clips`, {
    method: "GET",
  });
}

/**
 * Get a single clip by ID.
 */
export async function getClip(clipId: string): Promise<Clip> {
  return apiRequest<Clip>(`/api/v1/clips/${clipId}`, { method: "GET" });
}

/**
 * Delete a clip.
 */
export async function deleteClip(clipId: string): Promise<void> {
  return apiRequest<void>(`/api/v1/clips/${clipId}`, { method: "DELETE" });
}

/**
 * Get clip generation progress.
 */
export async function getClipProgress(
  videoId: string,
  jobId: string,
): Promise<ClipProgressResponse> {
  return apiRequest<ClipProgressResponse>(
    `/api/v1/videos/${videoId}/clips/progress/${jobId}`,
    { method: "GET" },
  );
}
