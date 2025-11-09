/** API client for silence removal operations. */

import { apiRequest } from "./api-client";

export interface SilenceSegment {
  start: number;
  end: number;
  duration: number;
}

export interface DetectSilenceRequest {
  threshold_db?: number;
  min_duration?: number;
}

export interface DetectSilenceResponse {
  segments: SilenceSegment[];
  total_silence_duration: number;
  total_duration: number;
}

export interface RemoveSilenceRequest {
  threshold_db?: number;
  min_duration?: number;
}

export interface RemoveSilenceResponse {
  job_id: string;
  status: string;
}

export interface SilenceProgressResponse {
  status: "pending" | "processing" | "completed" | "failed";
  progress: number;
  message?: string;
  output_video_id?: string;
}

/**
 * Detect silence segments in a video.
 */
export async function detectSilence(
  videoId: string,
  params: DetectSilenceRequest = {},
): Promise<DetectSilenceResponse> {
  const queryParams = new URLSearchParams();

  if (params.threshold_db !== undefined) {
    queryParams.append("threshold_db", params.threshold_db.toString());
  }
  if (params.min_duration !== undefined) {
    queryParams.append("min_duration", params.min_duration.toString());
  }

  const query = queryParams.toString() ? `?${queryParams.toString()}` : "";

  return apiRequest<DetectSilenceResponse>(
    `/api/v1/videos/${videoId}/silence/detect${query}`,
    { method: "GET" },
  );
}

/**
 * Remove silence from a video.
 */
export async function removeSilence(
  videoId: string,
  params: RemoveSilenceRequest = {},
): Promise<RemoveSilenceResponse> {
  return apiRequest<RemoveSilenceResponse>(
    `/api/v1/videos/${videoId}/silence/remove`,
    {
      method: "POST",
      body: JSON.stringify(params),
    },
  );
}

/**
 * Get silence removal progress.
 */
export async function getSilenceProgress(
  videoId: string,
  jobId: string,
): Promise<SilenceProgressResponse> {
  return apiRequest<SilenceProgressResponse>(
    `/api/v1/videos/${videoId}/silence/progress/${jobId}`,
    { method: "GET" },
  );
}
