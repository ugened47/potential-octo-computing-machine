// Clip API client (keyword search, clip generation, exports)
import { tokenStorage } from './token-storage';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type ClipStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Clip {
  id: string;
  video_id: string;
  title: string;
  start: number;
  end: number;
  duration: number;
  status: ClipStatus;
  output_url?: string;
  thumbnail_url?: string;
  keywords?: string[];
  created_at: string;
  updated_at: string;
}

export interface ClipCreateData {
  video_id: string;
  title: string;
  start: number;
  end: number;
  keywords?: string[];
}

export interface ClipUpdateData {
  title?: string;
  start?: number;
  end?: number;
  keywords?: string[];
}

export interface KeywordSearchParams {
  keywords: string[];
  context_seconds?: number; // Seconds of context around keyword (default: 2)
  min_clip_duration?: number; // Minimum clip duration in seconds (default: 3)
  max_clip_duration?: number; // Maximum clip duration in seconds (default: 60)
  merge_nearby?: boolean; // Merge clips that are close together (default: true)
  merge_threshold?: number; // Seconds threshold for merging (default: 2)
}

export interface KeywordSearchResult {
  keyword: string;
  occurrences: number;
  clips: Array<{
    start: number;
    end: number;
    duration: number;
    text: string;
    confidence: number;
  }>;
}

export interface KeywordSearchResponse {
  video_id: string;
  results: KeywordSearchResult[];
  total_clips: number;
}

export interface ClipExportParams {
  format?: 'mp4' | 'webm' | 'mov'; // Output format (default: mp4)
  resolution?: '720p' | '1080p' | 'original'; // Output resolution (default: original)
  quality?: 'low' | 'medium' | 'high'; // Output quality (default: high)
  include_subtitles?: boolean; // Burn subtitles into video (default: false)
}

export interface BatchClipCreateData {
  video_id: string;
  clips: Array<{
    title: string;
    start: number;
    end: number;
    keywords?: string[];
  }>;
}

export interface ClipListParams {
  page?: number;
  limit?: number;
  video_id?: string;
  status?: ClipStatus;
  search?: string;
  sort?: 'created_at' | 'title' | 'duration';
  order?: 'asc' | 'desc';
}

export interface ClipListResponse {
  clips: Clip[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

class ClipAPI {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = tokenStorage.getAccessToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(error.message || error.detail || 'API request failed');
    }

    // Handle 204 No Content responses
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // ==================== Keyword Search APIs ====================

  /**
   * Search for keywords in a video transcript
   * @param videoId - Video ID
   * @param params - Search parameters
   * @returns Search results with suggested clips
   */
  async searchKeywords(videoId: string, params: KeywordSearchParams): Promise<KeywordSearchResponse> {
    return this.request<KeywordSearchResponse>(`/api/videos/${videoId}/search-keywords`, {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  /**
   * Search for a single keyword in a video
   * @param videoId - Video ID
   * @param keyword - Keyword to search for
   * @param contextSeconds - Seconds of context around keyword
   * @returns Search results for the keyword
   */
  async searchKeyword(
    videoId: string,
    keyword: string,
    contextSeconds: number = 2
  ): Promise<KeywordSearchResult> {
    const response = await this.searchKeywords(videoId, {
      keywords: [keyword],
      context_seconds: contextSeconds,
    });
    return response.results[0];
  }

  // ==================== Clip CRUD APIs ====================

  /**
   * Create a new clip
   * @param data - Clip data
   * @returns Created clip
   */
  async createClip(data: ClipCreateData): Promise<Clip> {
    return this.request<Clip>('/api/clips', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Create multiple clips in a batch
   * @param data - Batch clip creation data
   * @returns Array of created clips
   */
  async createClipsBatch(data: BatchClipCreateData): Promise<Clip[]> {
    return this.request<Clip[]>('/api/clips/batch', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Get a list of clips
   * @param params - Query parameters
   * @returns Paginated list of clips
   */
  async getClips(params: ClipListParams = {}): Promise<ClipListResponse> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, value.toString());
      }
    });

    const queryString = queryParams.toString();
    const endpoint = queryString ? `/api/clips?${queryString}` : '/api/clips';

    return this.request<ClipListResponse>(endpoint);
  }

  /**
   * Get clips for a specific video
   * @param videoId - Video ID
   * @returns Array of clips for the video
   */
  async getClipsByVideo(videoId: string): Promise<Clip[]> {
    return this.request<Clip[]>(`/api/videos/${videoId}/clips`);
  }

  /**
   * Get a single clip by ID
   * @param id - Clip ID
   * @returns Clip object
   */
  async getClip(id: string): Promise<Clip> {
    return this.request<Clip>(`/api/clips/${id}`);
  }

  /**
   * Update a clip
   * @param id - Clip ID
   * @param data - Fields to update
   * @returns Updated clip
   */
  async updateClip(id: string, data: ClipUpdateData): Promise<Clip> {
    return this.request<Clip>(`/api/clips/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  /**
   * Delete a clip
   * @param id - Clip ID
   */
  async deleteClip(id: string): Promise<void> {
    await this.request(`/api/clips/${id}`, { method: 'DELETE' });
  }

  // ==================== Clip Processing APIs ====================

  /**
   * Generate/export a clip (starts processing job)
   * @param id - Clip ID
   * @param params - Export parameters
   * @returns Job ID for tracking
   */
  async exportClip(id: string, params?: ClipExportParams): Promise<{ job_id: string }> {
    return this.request<{ job_id: string }>(`/api/clips/${id}/export`, {
      method: 'POST',
      body: JSON.stringify(params || {}),
    });
  }

  /**
   * Get playback URL for a completed clip
   * @param id - Clip ID
   * @returns Playback URL
   */
  async getClipPlaybackUrl(id: string): Promise<{ url: string; expires_in: number }> {
    return this.request<{ url: string; expires_in: number }>(`/api/clips/${id}/playback-url`);
  }

  /**
   * Download a clip
   * @param id - Clip ID
   * @returns Download URL
   */
  async getClipDownloadUrl(id: string): Promise<{ url: string }> {
    return this.request<{ url: string }>(`/api/clips/${id}/download`);
  }

  /**
   * Poll clip status until completion or failure
   * @param id - Clip ID
   * @param onProgress - Progress callback
   * @param pollInterval - Polling interval in milliseconds (default: 2000)
   * @param maxAttempts - Maximum polling attempts (default: 150 = 5 minutes)
   * @returns Completed clip
   */
  async pollClipStatus(
    id: string,
    onProgress?: (clip: Clip) => void,
    pollInterval: number = 2000,
    maxAttempts: number = 150
  ): Promise<Clip> {
    let attempts = 0;

    while (attempts < maxAttempts) {
      const clip = await this.getClip(id);
      onProgress?.(clip);

      if (clip.status === 'completed') {
        return clip;
      }

      if (clip.status === 'failed') {
        throw new Error('Clip generation failed');
      }

      await new Promise((resolve) => setTimeout(resolve, pollInterval));
      attempts++;
    }

    throw new Error('Clip processing timeout: Maximum polling attempts reached');
  }

  /**
   * Retry processing a failed clip
   * @param id - Clip ID
   * @returns Updated clip
   */
  async retryClip(id: string): Promise<Clip> {
    return this.request<Clip>(`/api/clips/${id}/retry`, {
      method: 'POST',
    });
  }

  // ==================== Auto-generation APIs ====================

  /**
   * Auto-generate clips based on keywords
   * @param videoId - Video ID
   * @param keywords - Keywords to search for
   * @param params - Search and clip generation parameters
   * @returns Array of created clips
   */
  async autoGenerateClips(
    videoId: string,
    keywords: string[],
    params?: Partial<KeywordSearchParams>
  ): Promise<Clip[]> {
    const searchParams: KeywordSearchParams = {
      keywords,
      ...params,
    };

    return this.request<Clip[]>(`/api/videos/${videoId}/auto-generate-clips`, {
      method: 'POST',
      body: JSON.stringify(searchParams),
    });
  }

  /**
   * Generate highlight reel from detected highlights
   * @param videoId - Video ID
   * @param maxDuration - Maximum duration of the highlight reel in seconds
   * @returns Created clip for the highlight reel
   */
  async generateHighlightReel(videoId: string, maxDuration: number = 60): Promise<Clip> {
    return this.request<Clip>(`/api/videos/${videoId}/highlight-reel`, {
      method: 'POST',
      body: JSON.stringify({ max_duration: maxDuration }),
    });
  }

  // ==================== Utility APIs ====================

  /**
   * Get thumbnail for a clip at a specific timestamp
   * @param id - Clip ID
   * @param timestamp - Timestamp in seconds (relative to clip start)
   * @returns Thumbnail URL
   */
  async getClipThumbnail(id: string, timestamp: number = 0): Promise<{ url: string }> {
    return this.request<{ url: string }>(`/api/clips/${id}/thumbnail?timestamp=${timestamp}`);
  }

  /**
   * Validate clip time range
   * @param videoId - Video ID
   * @param start - Start time in seconds
   * @param end - End time in seconds
   * @returns Validation result
   */
  async validateClipRange(
    videoId: string,
    start: number,
    end: number
  ): Promise<{ valid: boolean; error?: string }> {
    return this.request<{ valid: boolean; error?: string }>(
      `/api/videos/${videoId}/validate-clip-range`,
      {
        method: 'POST',
        body: JSON.stringify({ start, end }),
      }
    );
  }

  /**
   * Get clip statistics for a video
   * @param videoId - Video ID
   * @returns Clip statistics
   */
  async getClipStats(videoId: string): Promise<{
    total_clips: number;
    total_duration: number;
    by_status: Record<ClipStatus, number>;
  }> {
    return this.request(`/api/videos/${videoId}/clip-stats`);
  }
}

export const clipAPI = new ClipAPI();
