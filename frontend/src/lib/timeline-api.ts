/** API client for timeline and waveform operations. */

import { apiRequest } from "./api-client";
import type { WaveformData } from "@/types/timeline";

interface WaveformStatus {
  status: "pending" | "processing" | "completed" | "failed";
  progress?: number;
  message?: string;
}

/**
 * Get waveform data for a video.
 */
export async function getWaveform(videoId: string): Promise<WaveformData> {
  return apiRequest<WaveformData>(`/api/v1/videos/${videoId}/waveform`, {
    method: "GET",
  });
}

/**
 * Generate waveform for a video.
 */
export async function generateWaveform(videoId: string): Promise<void> {
  return apiRequest<void>(`/api/v1/videos/${videoId}/waveform/generate`, {
    method: "POST",
  });
}

/**
 * Get waveform generation status.
 */
export async function getWaveformStatus(
  videoId: string,
): Promise<WaveformStatus> {
  return apiRequest<WaveformStatus>(
    `/api/v1/videos/${videoId}/waveform/status`,
    {
      method: "GET",
    },
  );
}
