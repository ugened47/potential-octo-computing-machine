/** Transcript types. */

export interface WordTimestamp {
  word: string
  start: number
  end: number
  confidence?: number
}

export type TranscriptStatus = 'processing' | 'completed' | 'failed'

export interface Transcript {
  id: string
  video_id: string
  full_text: string
  word_timestamps: {
    words: WordTimestamp[]
  }
  language?: string
  status: TranscriptStatus
  accuracy_score?: number
  created_at: string
  updated_at: string
  completed_at?: string
}

export interface TranscriptProgress {
  video_id: string
  progress: number
  status: string
  estimated_time_remaining?: number
}

