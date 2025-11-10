// Timeline API client (waveform, segments, silence detection)
import { tokenStorage } from "./token-storage";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface WaveformData {
  id: string;
  video_id: string;
  samples: number[];
  sample_rate: number;
  duration: number;
  channels: number;
  created_at: string;
}

export interface WaveformParams {
  resolution?: number; // Number of samples to return (default: 1000)
  normalize?: boolean; // Normalize amplitude to 0-1 range (default: true)
}

export type SegmentType =
  | "speech"
  | "silence"
  | "music"
  | "noise"
  | "highlight";

export interface Segment {
  id: string;
  video_id: string;
  type: SegmentType;
  start: number;
  end: number;
  duration: number;
  confidence?: number;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface SilenceDetectionParams {
  threshold?: number; // Silence threshold in dB (default: -40)
  min_duration?: number; // Minimum silence duration in seconds (default: 0.5)
}

export interface SilenceRemovalParams {
  threshold?: number; // Silence threshold in dB (default: -40)
  min_duration?: number; // Minimum silence duration in seconds (default: 0.5)
  padding?: number; // Padding around speech in seconds (default: 0.1)
}

export interface SegmentCreateData {
  video_id: string;
  type: SegmentType;
  start: number;
  end: number;
  metadata?: Record<string, any>;
}

export interface SegmentUpdateData {
  type?: SegmentType;
  start?: number;
  end?: number;
  metadata?: Record<string, any>;
}

export interface AudioAnalysis {
  duration: number;
  sample_rate: number;
  channels: number;
  loudness_lufs?: number; // Integrated loudness (LUFS)
  peak_db?: number; // Peak level in dB
  dynamic_range?: number; // Dynamic range in dB
}

class TimelineAPI {
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

  // ==================== Waveform APIs ====================

  /**
   * Generate waveform data for a video
   * @param videoId - Video ID
   * @param params - Waveform generation parameters
   * @returns Waveform data
   */
  async generateWaveform(
    videoId: string,
    params?: WaveformParams,
  ): Promise<WaveformData> {
    const queryParams = new URLSearchParams();
    if (params?.resolution)
      queryParams.append("resolution", params.resolution.toString());
    if (params?.normalize !== undefined)
      queryParams.append("normalize", params.normalize.toString());

    const queryString = queryParams.toString();
    const endpoint = queryString
      ? `/api/videos/${videoId}/waveform?${queryString}`
      : `/api/videos/${videoId}/waveform`;

    return this.request<WaveformData>(endpoint, { method: "POST" });
  }

  /**
   * Get waveform data for a video
   * @param videoId - Video ID
   * @param params - Query parameters for waveform resolution
   * @returns Waveform data
   */
  async getWaveform(
    videoId: string,
    params?: WaveformParams,
  ): Promise<WaveformData> {
    const queryParams = new URLSearchParams();
    if (params?.resolution)
      queryParams.append("resolution", params.resolution.toString());
    if (params?.normalize !== undefined)
      queryParams.append("normalize", params.normalize.toString());

    const queryString = queryParams.toString();
    const endpoint = queryString
      ? `/api/videos/${videoId}/waveform?${queryString}`
      : `/api/videos/${videoId}/waveform`;

    return this.request<WaveformData>(endpoint);
  }

  /**
   * Delete waveform data
   * @param videoId - Video ID
   */
  async deleteWaveform(videoId: string): Promise<void> {
    await this.request(`/api/videos/${videoId}/waveform`, { method: "DELETE" });
  }

  // ==================== Segment APIs ====================

  /**
   * Get all segments for a video
   * @param videoId - Video ID
   * @param type - Optional filter by segment type
   * @returns Array of segments
   */
  async getSegments(videoId: string, type?: SegmentType): Promise<Segment[]> {
    const endpoint = type
      ? `/api/videos/${videoId}/segments?type=${type}`
      : `/api/videos/${videoId}/segments`;

    return this.request<Segment[]>(endpoint);
  }

  /**
   * Create a new segment
   * @param data - Segment data
   * @returns Created segment
   */
  async createSegment(data: SegmentCreateData): Promise<Segment> {
    return this.request<Segment>("/api/segments", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * Get a single segment by ID
   * @param id - Segment ID
   * @returns Segment object
   */
  async getSegment(id: string): Promise<Segment> {
    return this.request<Segment>(`/api/segments/${id}`);
  }

  /**
   * Update a segment
   * @param id - Segment ID
   * @param data - Fields to update
   * @returns Updated segment
   */
  async updateSegment(id: string, data: SegmentUpdateData): Promise<Segment> {
    return this.request<Segment>(`/api/segments/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  /**
   * Delete a segment
   * @param id - Segment ID
   */
  async deleteSegment(id: string): Promise<void> {
    await this.request(`/api/segments/${id}`, { method: "DELETE" });
  }

  /**
   * Delete all segments for a video
   * @param videoId - Video ID
   * @param type - Optional: only delete segments of this type
   */
  async deleteAllSegments(videoId: string, type?: SegmentType): Promise<void> {
    const endpoint = type
      ? `/api/videos/${videoId}/segments?type=${type}`
      : `/api/videos/${videoId}/segments`;

    await this.request(endpoint, { method: "DELETE" });
  }

  // ==================== Silence Detection APIs ====================

  /**
   * Detect silence segments in a video
   * @param videoId - Video ID
   * @param params - Silence detection parameters
   * @returns Array of silence segments
   */
  async detectSilence(
    videoId: string,
    params?: SilenceDetectionParams,
  ): Promise<Segment[]> {
    return this.request<Segment[]>(`/api/videos/${videoId}/detect-silence`, {
      method: "POST",
      body: JSON.stringify(params || {}),
    });
  }

  /**
   * Remove silence from a video (creates a new processed video)
   * @param videoId - Video ID
   * @param params - Silence removal parameters
   * @returns Job ID for tracking the processing
   */
  async removeSilence(
    videoId: string,
    params?: SilenceRemovalParams,
  ): Promise<{ job_id: string }> {
    return this.request<{ job_id: string }>(
      `/api/videos/${videoId}/remove-silence`,
      {
        method: "POST",
        body: JSON.stringify(params || {}),
      },
    );
  }

  // ==================== Audio Analysis APIs ====================

  /**
   * Analyze audio properties of a video
   * @param videoId - Video ID
   * @returns Audio analysis data
   */
  async analyzeAudio(videoId: string): Promise<AudioAnalysis> {
    return this.request<AudioAnalysis>(
      `/api/videos/${videoId}/audio-analysis`,
      {
        method: "POST",
      },
    );
  }

  /**
   * Get cached audio analysis
   * @param videoId - Video ID
   * @returns Audio analysis data
   */
  async getAudioAnalysis(videoId: string): Promise<AudioAnalysis> {
    return this.request<AudioAnalysis>(`/api/videos/${videoId}/audio-analysis`);
  }

  // ==================== Scene Detection APIs ====================

  /**
   * Detect scene changes in a video
   * @param videoId - Video ID
   * @param threshold - Scene change threshold (0-1, default: 0.3)
   * @returns Array of scene change segments
   */
  async detectScenes(videoId: string, threshold?: number): Promise<Segment[]> {
    const params = threshold !== undefined ? { threshold } : {};
    return this.request<Segment[]>(`/api/videos/${videoId}/detect-scenes`, {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // ==================== Highlight Detection APIs ====================

  /**
   * Detect highlight moments in a video (based on audio energy, transcript keywords, etc.)
   * @param videoId - Video ID
   * @returns Array of highlight segments
   */
  async detectHighlights(videoId: string): Promise<Segment[]> {
    return this.request<Segment[]>(`/api/videos/${videoId}/detect-highlights`, {
      method: "POST",
    });
  }

  // ==================== Utility APIs ====================

  /**
   * Get segments within a specific time range
   * @param videoId - Video ID
   * @param startTime - Start time in seconds
   * @param endTime - End time in seconds
   * @returns Array of segments in the time range
   */
  async getSegmentsByTimeRange(
    videoId: string,
    startTime: number,
    endTime: number,
  ): Promise<Segment[]> {
    return this.request<Segment[]>(
      `/api/videos/${videoId}/segments/range?start=${startTime}&end=${endTime}`,
    );
  }

  /**
   * Merge overlapping segments of the same type
   * @param videoId - Video ID
   * @param type - Segment type to merge
   * @returns Array of merged segments
   */
  async mergeSegments(videoId: string, type: SegmentType): Promise<Segment[]> {
    return this.request<Segment[]>(`/api/videos/${videoId}/segments/merge`, {
      method: "POST",
      body: JSON.stringify({ type }),
    });
  }
}

export const timelineAPI = new TimelineAPI();
