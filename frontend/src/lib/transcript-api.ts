// Transcript API client
import { tokenStorage } from "./token-storage";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type TranscriptStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed";

export interface TranscriptWord {
  word: string;
  start: number;
  end: number;
  confidence?: number;
}

export interface TranscriptSegment {
  id: string;
  text: string;
  start: number;
  end: number;
  words?: TranscriptWord[];
  speaker?: string;
}

export interface Transcript {
  id: string;
  video_id: string;
  status: TranscriptStatus;
  language?: string;
  segments: TranscriptSegment[];
  full_text?: string;
  word_count?: number;
  duration?: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface TranscriptCreateData {
  video_id: string;
  language?: string;
}

export interface TranscriptSearchParams {
  query: string;
  case_sensitive?: boolean;
  whole_word?: boolean;
}

export interface TranscriptSearchResult {
  segment_id: string;
  text: string;
  start: number;
  end: number;
  match_positions: Array<{ start: number; end: number }>;
}

export interface TranscriptExportFormat {
  format: "srt" | "vtt" | "txt" | "json";
}

class TranscriptAPI {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const token = tokenStorage.getAccessToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) || {}),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ message: response.statusText }));
      throw new Error(error.message || error.detail || "API request failed");
    }

    // Handle 204 No Content responses
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  /**
   * Create a transcription job for a video
   * @param data - Transcription request data
   * @returns Transcript object with pending status
   */
  async createTranscript(data: TranscriptCreateData): Promise<Transcript> {
    return this.request<Transcript>("/api/transcripts", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * Get transcript by video ID
   * @param videoId - Video ID
   * @returns Transcript object or null if not found
   */
  async getTranscriptByVideoId(videoId: string): Promise<Transcript | null> {
    try {
      return await this.request<Transcript>(
        `/api/transcripts/video/${videoId}`,
      );
    } catch (error) {
      // Return null if transcript doesn't exist
      if (error instanceof Error && error.message.includes("404")) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Get transcript by transcript ID
   * @param id - Transcript ID
   * @returns Transcript object
   */
  async getTranscript(id: string): Promise<Transcript> {
    return this.request<Transcript>(`/api/transcripts/${id}`);
  }

  /**
   * Search within a transcript
   * @param id - Transcript ID
   * @param params - Search parameters
   * @returns Array of search results
   */
  async searchTranscript(
    id: string,
    params: TranscriptSearchParams,
  ): Promise<TranscriptSearchResult[]> {
    return this.request<TranscriptSearchResult[]>(
      `/api/transcripts/${id}/search`,
      {
        method: "POST",
        body: JSON.stringify(params),
      },
    );
  }

  /**
   * Update transcript segment text (manual editing)
   * @param id - Transcript ID
   * @param segmentId - Segment ID to update
   * @param text - New text for the segment
   * @returns Updated transcript
   */
  async updateSegment(
    id: string,
    segmentId: string,
    text: string,
  ): Promise<Transcript> {
    return this.request<Transcript>(
      `/api/transcripts/${id}/segments/${segmentId}`,
      {
        method: "PATCH",
        body: JSON.stringify({ text }),
      },
    );
  }

  /**
   * Export transcript in various formats
   * @param id - Transcript ID
   * @param format - Export format (srt, vtt, txt, json)
   * @returns Blob containing the exported file
   */
  async exportTranscript(
    id: string,
    format: "srt" | "vtt" | "txt" | "json",
  ): Promise<Blob> {
    const token = tokenStorage.getAccessToken();
    const headers: Record<string, string> = {};

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(
      `${API_URL}/api/transcripts/${id}/export?format=${format}`,
      {
        headers,
      },
    );

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ message: response.statusText }));
      throw new Error(error.message || "Export failed");
    }

    return response.blob();
  }

  /**
   * Download transcript export
   * @param id - Transcript ID
   * @param format - Export format
   * @param filename - Optional custom filename
   */
  async downloadTranscript(
    id: string,
    format: "srt" | "vtt" | "txt" | "json",
    filename?: string,
  ): Promise<void> {
    const blob = await this.exportTranscript(id, format);
    const url = window.URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = filename || `transcript-${id}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    window.URL.revokeObjectURL(url);
  }

  /**
   * Delete a transcript
   * @param id - Transcript ID
   */
  async deleteTranscript(id: string): Promise<void> {
    await this.request(`/api/transcripts/${id}`, { method: "DELETE" });
  }

  /**
   * Retry transcription for a failed job
   * @param id - Transcript ID
   * @returns Updated transcript object
   */
  async retryTranscription(id: string): Promise<Transcript> {
    return this.request<Transcript>(`/api/transcripts/${id}/retry`, {
      method: "POST",
    });
  }

  /**
   * Get transcript statistics
   * @param id - Transcript ID
   * @returns Statistics about the transcript
   */
  async getTranscriptStats(id: string): Promise<{
    word_count: number;
    segment_count: number;
    duration: number;
    language?: string;
    average_confidence?: number;
  }> {
    return this.request(`/api/transcripts/${id}/stats`);
  }

  /**
   * Poll transcript status until completion or failure
   * @param id - Transcript ID
   * @param onProgress - Progress callback
   * @param pollInterval - Polling interval in milliseconds (default: 2000)
   * @param maxAttempts - Maximum polling attempts (default: 150 = 5 minutes)
   * @returns Completed transcript
   */
  async pollTranscriptStatus(
    id: string,
    onProgress?: (transcript: Transcript) => void,
    pollInterval: number = 2000,
    maxAttempts: number = 150,
  ): Promise<Transcript> {
    let attempts = 0;

    while (attempts < maxAttempts) {
      const transcript = await this.getTranscript(id);
      onProgress?.(transcript);

      if (transcript.status === "completed") {
        return transcript;
      }

      if (transcript.status === "failed") {
        throw new Error(transcript.error_message || "Transcription failed");
      }

      await new Promise((resolve) => setTimeout(resolve, pollInterval));
      attempts++;
    }

    throw new Error("Transcription timeout: Maximum polling attempts reached");
  }

  /**
   * Get word-level timing for a specific time range
   * @param id - Transcript ID
   * @param startTime - Start time in seconds
   * @param endTime - End time in seconds
   * @returns Array of words in the time range
   */
  async getWordsByTimeRange(
    id: string,
    startTime: number,
    endTime: number,
  ): Promise<TranscriptWord[]> {
    return this.request<TranscriptWord[]>(
      `/api/transcripts/${id}/words?start=${startTime}&end=${endTime}`,
    );
  }

  /**
   * Update transcript language
   * @param id - Transcript ID
   * @param language - Language code (e.g., 'en', 'es', 'fr')
   * @returns Updated transcript
   */
  async updateLanguage(id: string, language: string): Promise<Transcript> {
    return this.request<Transcript>(`/api/transcripts/${id}/language`, {
      method: "PATCH",
      body: JSON.stringify({ language }),
    });
  }
}

export const transcriptAPI = new TranscriptAPI();
