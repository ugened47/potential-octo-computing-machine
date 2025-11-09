/** Timeline API client for waveform and segments. */

import { apiGet, apiPost, apiDelete } from './api-client'
import type { WaveformData, WaveformStatus, Segment, SegmentCreate } from '@/types/timeline'

/**
 * Get waveform data for a video.
 * @param videoId - Video ID
 * @returns Waveform data with peaks, duration, and sample rate
 */
export async function getWaveform(videoId: string): Promise<WaveformData> {
  return apiGet<WaveformData>(`/videos/${videoId}/timeline/waveform`)
}

/**
 * Trigger waveform generation for a video.
 * @param videoId - Video ID
 * @returns Waveform generation status
 */
export async function generateWaveform(videoId: string): Promise<WaveformStatus> {
  return apiPost<WaveformStatus>(`/videos/${videoId}/timeline/waveform`)
}

/**
 * Get waveform generation status.
 * @param videoId - Video ID
 * @returns Current status of waveform generation
 */
export async function getWaveformStatus(videoId: string): Promise<WaveformStatus> {
  return apiGet<WaveformStatus>(`/videos/${videoId}/timeline/waveform/status`)
}

/**
 * Save timeline segments for a video.
 * @param videoId - Video ID
 * @param segments - Segments to save
 * @returns Saved segments
 */
export async function saveSegments(
  videoId: string,
  segments: SegmentCreate[]
): Promise<Segment[]> {
  return apiPost<Segment[]>(`/videos/${videoId}/timeline/segments`, segments)
}

/**
 * Get saved timeline segments for a video.
 * @param videoId - Video ID
 * @returns List of segments
 */
export async function getSegments(videoId: string): Promise<Segment[]> {
  return apiGet<Segment[]>(`/videos/${videoId}/timeline/segments`)
}

/**
 * Clear all timeline segments for a video.
 * @param videoId - Video ID
 */
export async function deleteSegments(videoId: string): Promise<void> {
  return apiDelete(`/videos/${videoId}/timeline/segments`)
}
