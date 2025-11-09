/** Transcript API client. */

import { apiGet, apiPost } from './api-client'

export interface TranscriptSegment {
  id: string
  start: number
  end: number
  text: string
  confidence?: number
}

export interface Transcript {
  id: string
  video_id: string
  segments: TranscriptSegment[]
  language?: string
  created_at: string
}

export interface TranscriptionStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress?: number
  error?: string
}

export interface TranscriptionProgress {
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  current_step?: string
  error?: string
}

export type TranscriptFormat = 'srt' | 'vtt' | 'txt' | 'json'

/**
 * Get transcript for a video.
 * @param videoId - Video ID
 * @returns Transcript data
 */
export async function getTranscript(videoId: string): Promise<Transcript> {
  return apiGet<Transcript>(`/videos/${videoId}/transcript`)
}

/**
 * Trigger transcription for a video.
 * @param videoId - Video ID
 * @returns Transcription status
 */
export async function triggerTranscription(videoId: string): Promise<TranscriptionStatus> {
  return apiPost<TranscriptionStatus>(`/videos/${videoId}/transcribe`)
}

/**
 * Get transcription progress.
 * @param videoId - Video ID
 * @returns Transcription progress
 */
export async function getTranscriptionProgress(videoId: string): Promise<TranscriptionProgress> {
  return apiGet<TranscriptionProgress>(`/videos/${videoId}/transcription/progress`)
}

/**
 * Export transcript in specified format.
 * @param videoId - Video ID
 * @param format - Export format (srt, vtt, txt, json)
 * @returns Transcript file as Blob
 */
export async function exportTranscript(
  videoId: string,
  format: TranscriptFormat
): Promise<Blob> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/videos/${videoId}/transcript/export?format=${format}`,
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
      },
    }
  )

  if (!response.ok) {
    throw new Error('Export failed')
  }

  return response.blob()
}

/**
 * Download transcript in specified format.
 * @param videoId - Video ID
 * @param format - Export format (srt, vtt, txt, json)
 * @param filename - Optional custom filename
 */
export async function downloadTranscript(
  videoId: string,
  format: TranscriptFormat,
  filename?: string
): Promise<void> {
  const blob = await exportTranscript(videoId, format)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename || `transcript-${videoId}.${format}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
