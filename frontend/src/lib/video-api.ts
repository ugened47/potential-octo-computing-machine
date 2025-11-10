// Video management API client
import { tokenStorage } from "./token-storage";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type VideoStatus = "uploaded" | "processing" | "completed" | "failed";

export interface Video {
  id: string;
  title: string;
  description?: string;
  filename: string;
  duration?: number;
  resolution?: string;
  format?: string;
  size: number;
  thumbnail_url?: string;
  video_url?: string;
  status: VideoStatus;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface VideoListParams {
  page?: number;
  limit?: number;
  status?: VideoStatus;
  search?: string;
  sort?: "created_at" | "title" | "duration" | "size";
  order?: "asc" | "desc";
}

export interface VideoListResponse {
  videos: Video[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface PresignedUrlResponse {
  upload_url: string;
  video_id: string;
  fields?: Record<string, string>;
}

export interface VideoCreateData {
  video_id: string;
  title: string;
  description?: string;
  filename: string;
  size: number;
  format?: string;
}

export interface VideoUpdateData {
  title?: string;
  description?: string;
}

export interface VideoStats {
  total_videos: number;
  total_size: number;
  by_status: Record<VideoStatus, number>;
  recent_uploads: number; // Last 7 days
}

class VideoAPI {
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
   * Get a presigned URL for uploading a video to S3
   * @param filename - Original filename
   * @param contentType - MIME type of the video
   * @param size - File size in bytes
   * @returns Presigned URL data
   */
  async getPresignedUrl(
    filename: string,
    contentType: string,
    size: number,
  ): Promise<PresignedUrlResponse> {
    return this.request<PresignedUrlResponse>("/api/upload/presigned-url", {
      method: "POST",
      body: JSON.stringify({ filename, content_type: contentType, size }),
    });
  }

  /**
   * Upload a video file directly to S3 using presigned URL
   * @param presignedUrl - Presigned URL from getPresignedUrl()
   * @param file - Video file to upload
   * @param onProgress - Progress callback (0-100)
   * @returns Promise that resolves when upload completes
   */
  async uploadToS3(
    presignedUrl: string,
    file: File,
    onProgress?: (progress: number) => void,
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable && onProgress) {
          const progress = (e.loaded / e.total) * 100;
          onProgress(Math.round(progress));
        }
      });

      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`));
        }
      });

      xhr.addEventListener("error", () => reject(new Error("Upload failed")));
      xhr.addEventListener("abort", () => reject(new Error("Upload aborted")));

      xhr.open("PUT", presignedUrl);
      xhr.setRequestHeader("Content-Type", file.type);
      xhr.send(file);
    });
  }

  /**
   * Create a video record after uploading to S3
   * @param data - Video metadata
   * @returns Created video object
   */
  async createVideo(data: VideoCreateData): Promise<Video> {
    return this.request<Video>("/api/videos", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * Complete video upload workflow (presigned URL + S3 upload + create record)
   * @param file - Video file to upload
   * @param title - Video title
   * @param description - Optional video description
   * @param onProgress - Progress callback (0-100)
   * @returns Created video object
   */
  async uploadVideo(
    file: File,
    title: string,
    description?: string,
    onProgress?: (progress: number) => void,
  ): Promise<Video> {
    // Step 1: Get presigned URL (10% progress)
    onProgress?.(10);
    const { upload_url, video_id } = await this.getPresignedUrl(
      file.name,
      file.type,
      file.size,
    );

    // Step 2: Upload to S3 (10-90% progress)
    await this.uploadToS3(upload_url, file, (uploadProgress) => {
      // Map 0-100 to 10-90
      const mappedProgress = 10 + uploadProgress * 0.8;
      onProgress?.(Math.round(mappedProgress));
    });

    // Step 3: Create video record (90-100% progress)
    onProgress?.(95);
    const video = await this.createVideo({
      video_id,
      title,
      description,
      filename: file.name,
      size: file.size,
      format: file.type,
    });

    onProgress?.(100);
    return video;
  }

  /**
   * Get a list of videos
   * @param params - Query parameters for filtering, sorting, pagination
   * @returns Paginated list of videos
   */
  async getVideos(params: VideoListParams = {}): Promise<VideoListResponse> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, value.toString());
      }
    });

    const queryString = queryParams.toString();
    const endpoint = queryString ? `/api/videos?${queryString}` : "/api/videos";

    return this.request<VideoListResponse>(endpoint);
  }

  /**
   * Get a single video by ID
   * @param id - Video ID
   * @returns Video object
   */
  async getVideo(id: string): Promise<Video> {
    return this.request<Video>(`/api/videos/${id}`);
  }

  /**
   * Update video metadata
   * @param id - Video ID
   * @param data - Fields to update (title, description)
   * @returns Updated video object
   */
  async updateVideo(id: string, data: VideoUpdateData): Promise<Video> {
    return this.request<Video>(`/api/videos/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  /**
   * Delete a video
   * @param id - Video ID
   */
  async deleteVideo(id: string): Promise<void> {
    await this.request(`/api/videos/${id}`, { method: "DELETE" });
  }

  /**
   * Get a presigned playback URL for streaming a video
   * @param id - Video ID
   * @returns Playback URL (valid for limited time)
   */
  async getPlaybackUrl(
    id: string,
  ): Promise<{ url: string; expires_in: number }> {
    return this.request<{ url: string; expires_in: number }>(
      `/api/videos/${id}/playback-url`,
    );
  }

  /**
   * Get thumbnail URL for a video
   * @param id - Video ID
   * @returns Thumbnail URL
   */
  async getThumbnailUrl(id: string): Promise<{ url: string }> {
    return this.request<{ url: string }>(`/api/videos/${id}/thumbnail`);
  }

  /**
   * Get video statistics for the current user
   * @returns Video statistics
   */
  async getStats(): Promise<VideoStats> {
    return this.request<VideoStats>("/api/videos/stats");
  }

  /**
   * Retry processing a failed video
   * @param id - Video ID
   * @returns Updated video object
   */
  async retryProcessing(id: string): Promise<Video> {
    return this.request<Video>(`/api/videos/${id}/retry`, {
      method: "POST",
    });
  }

  /**
   * Download a processed video
   * @param id - Video ID
   * @returns Download URL
   */
  async getDownloadUrl(id: string): Promise<{ url: string }> {
    return this.request<{ url: string }>(`/api/videos/${id}/download`);
  }
}

export const videoAPI = new VideoAPI();
