// Advanced Editor API client
import { tokenStorage } from "./token-storage";
import type {
  Project,
  ProjectConfig,
  ProjectsResponse,
  ProjectsQueryParams,
  ProjectUpdate,
  Track,
  TrackConfig,
  TrackUpdate,
  TrackItem,
  TrackItemConfig,
  TrackItemUpdate,
  Asset,
  AssetType,
  AssetsResponse,
  AssetsQueryParams,
  AssetUpdate,
  Transition,
  TransitionsResponse,
  TransitionsQueryParams,
  RenderConfig,
  RenderJobResponse,
  RenderProgress,
  ValidationResult,
  SplitItemResponse,
  DeleteResponse,
} from "@/types/advancedEditor";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class AdvancedEditorAPI {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const token = tokenStorage.getAccessToken();
    const headers: Record<string, string> = {
      ...((options.headers as Record<string, string>) || {}),
    };

    // Only set Content-Type if not already set (for multipart/form-data)
    if (!headers["Content-Type"] && !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

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

    // Handle image responses
    if (response.headers.get("content-type")?.startsWith("image/")) {
      const blob = await response.blob();
      return URL.createObjectURL(blob) as T;
    }

    return response.json();
  }

  // ==================== Project Endpoints ====================

  /**
   * Create a new project
   */
  async createProject(config: ProjectConfig): Promise<Project> {
    return this.request<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify(config),
    });
  }

  /**
   * Get list of user's projects
   */
  async getProjects(params?: ProjectsQueryParams): Promise<ProjectsResponse> {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append("status", params.status);
    if (params?.limit) queryParams.append("limit", params.limit.toString());
    if (params?.offset) queryParams.append("offset", params.offset.toString());
    if (params?.sort) queryParams.append("sort", params.sort);

    const query = queryParams.toString();
    return this.request<ProjectsResponse>(
      `/api/projects${query ? `?${query}` : ""}`,
    );
  }

  /**
   * Get project details with all tracks and items
   */
  async getProject(projectId: string): Promise<Project> {
    return this.request<Project>(`/api/projects/${projectId}`);
  }

  /**
   * Update project settings
   */
  async updateProject(
    projectId: string,
    updates: ProjectUpdate,
  ): Promise<Project> {
    return this.request<Project>(`/api/projects/${projectId}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    });
  }

  /**
   * Delete project
   */
  async deleteProject(projectId: string): Promise<DeleteResponse> {
    return this.request<DeleteResponse>(`/api/projects/${projectId}`, {
      method: "DELETE",
    });
  }

  /**
   * Duplicate project
   */
  async duplicateProject(projectId: string): Promise<Project> {
    return this.request<Project>(`/api/projects/${projectId}/duplicate`, {
      method: "POST",
    });
  }

  /**
   * Trigger project rendering
   */
  async renderProject(
    projectId: string,
    config: RenderConfig,
  ): Promise<RenderJobResponse> {
    return this.request<RenderJobResponse>(
      `/api/projects/${projectId}/render`,
      {
        method: "POST",
        body: JSON.stringify(config),
      },
    );
  }

  /**
   * Get render progress
   */
  async getRenderProgress(projectId: string): Promise<RenderProgress> {
    return this.request<RenderProgress>(
      `/api/projects/${projectId}/render/progress`,
    );
  }

  /**
   * Cancel ongoing render
   */
  async cancelRender(projectId: string): Promise<DeleteResponse> {
    return this.request<DeleteResponse>(
      `/api/projects/${projectId}/render/cancel`,
      {
        method: "POST",
      },
    );
  }

  /**
   * Get preview frame at specific time
   */
  async getProjectPreview(projectId: string, time: number): Promise<string> {
    return this.request<string>(
      `/api/projects/${projectId}/preview?time=${time}`,
    );
  }

  /**
   * Validate project before render
   */
  async validateProject(projectId: string): Promise<ValidationResult> {
    return this.request<ValidationResult>(`/api/projects/${projectId}/validate`);
  }

  // ==================== Track Endpoints ====================

  /**
   * Add track to project
   */
  async addTrack(projectId: string, config: TrackConfig): Promise<Track> {
    return this.request<Track>(`/api/projects/${projectId}/tracks`, {
      method: "POST",
      body: JSON.stringify(config),
    });
  }

  /**
   * Get track details
   */
  async getTrack(trackId: string): Promise<Track> {
    return this.request<Track>(`/api/tracks/${trackId}`);
  }

  /**
   * Update track
   */
  async updateTrack(trackId: string, updates: TrackUpdate): Promise<Track> {
    return this.request<Track>(`/api/tracks/${trackId}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    });
  }

  /**
   * Delete track
   */
  async deleteTrack(trackId: string): Promise<DeleteResponse> {
    return this.request<DeleteResponse>(`/api/tracks/${trackId}`, {
      method: "DELETE",
    });
  }

  /**
   * Duplicate track
   */
  async duplicateTrack(trackId: string): Promise<Track> {
    return this.request<Track>(`/api/tracks/${trackId}/duplicate`, {
      method: "POST",
    });
  }

  /**
   * Reorder track in list
   */
  async reorderTrack(
    trackId: string,
    newOrder: number,
  ): Promise<DeleteResponse> {
    return this.request<DeleteResponse>(`/api/tracks/${trackId}/reorder`, {
      method: "POST",
      body: JSON.stringify({ new_order: newOrder }),
    });
  }

  // ==================== TrackItem Endpoints ====================

  /**
   * Add item to track
   */
  async addTrackItem(
    trackId: string,
    config: TrackItemConfig,
  ): Promise<TrackItem> {
    return this.request<TrackItem>(`/api/tracks/${trackId}/items`, {
      method: "POST",
      body: JSON.stringify(config),
    });
  }

  /**
   * Get item details
   */
  async getTrackItem(itemId: string): Promise<TrackItem> {
    return this.request<TrackItem>(`/api/items/${itemId}`);
  }

  /**
   * Update track item
   */
  async updateTrackItem(
    itemId: string,
    updates: TrackItemUpdate,
  ): Promise<TrackItem> {
    return this.request<TrackItem>(`/api/items/${itemId}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    });
  }

  /**
   * Delete track item
   */
  async deleteTrackItem(itemId: string): Promise<DeleteResponse> {
    return this.request<DeleteResponse>(`/api/items/${itemId}`, {
      method: "DELETE",
    });
  }

  /**
   * Duplicate track item
   */
  async duplicateTrackItem(itemId: string): Promise<TrackItem> {
    return this.request<TrackItem>(`/api/items/${itemId}/duplicate`, {
      method: "POST",
    });
  }

  /**
   * Split item at time
   */
  async splitTrackItem(
    itemId: string,
    splitTime: number,
  ): Promise<SplitItemResponse> {
    return this.request<SplitItemResponse>(`/api/items/${itemId}/split`, {
      method: "POST",
      body: JSON.stringify({ split_time: splitTime }),
    });
  }

  // ==================== Asset Endpoints ====================

  /**
   * Upload asset to library
   */
  async uploadAsset(
    file: File,
    config: {
      asset_type: AssetType;
      name: string;
      tags: string[];
    },
  ): Promise<Asset> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("asset_type", config.asset_type);
    formData.append("name", config.name);
    config.tags.forEach((tag) => formData.append("tags[]", tag));

    return this.request<Asset>("/api/assets/upload", {
      method: "POST",
      body: formData,
      headers: {}, // Let browser set Content-Type for multipart/form-data
    });
  }

  /**
   * Get list of user's assets
   */
  async getAssets(params?: AssetsQueryParams): Promise<AssetsResponse> {
    const queryParams = new URLSearchParams();
    if (params?.asset_type) queryParams.append("asset_type", params.asset_type);
    if (params?.tags?.length) {
      params.tags.forEach((tag) => queryParams.append("tags", tag));
    }
    if (params?.limit) queryParams.append("limit", params.limit.toString());
    if (params?.offset) queryParams.append("offset", params.offset.toString());
    if (params?.search) queryParams.append("search", params.search);

    const query = queryParams.toString();
    return this.request<AssetsResponse>(
      `/api/assets${query ? `?${query}` : ""}`,
    );
  }

  /**
   * Get asset details
   */
  async getAsset(assetId: string): Promise<Asset> {
    return this.request<Asset>(`/api/assets/${assetId}`);
  }

  /**
   * Update asset metadata
   */
  async updateAsset(assetId: string, updates: AssetUpdate): Promise<Asset> {
    return this.request<Asset>(`/api/assets/${assetId}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    });
  }

  /**
   * Delete asset
   */
  async deleteAsset(assetId: string): Promise<DeleteResponse> {
    return this.request<DeleteResponse>(`/api/assets/${assetId}`, {
      method: "DELETE",
    });
  }

  /**
   * Search assets
   */
  async searchAssets(
    query: string,
    params?: Pick<AssetsQueryParams, "asset_type" | "tags">,
  ): Promise<AssetsResponse> {
    const queryParams = new URLSearchParams();
    queryParams.append("q", query);
    if (params?.asset_type) queryParams.append("asset_type", params.asset_type);
    if (params?.tags?.length) {
      params.tags.forEach((tag) => queryParams.append("tags", tag));
    }

    return this.request<AssetsResponse>(`/api/assets/search?${queryParams.toString()}`);
  }

  // ==================== Transition Endpoints ====================

  /**
   * Get list of available transitions
   */
  async getTransitions(
    params?: TransitionsQueryParams,
  ): Promise<TransitionsResponse> {
    const queryParams = new URLSearchParams();
    if (params?.transition_type)
      queryParams.append("transition_type", params.transition_type);
    if (params?.is_public !== undefined)
      queryParams.append("is_public", params.is_public.toString());

    const query = queryParams.toString();
    return this.request<TransitionsResponse>(
      `/api/transitions${query ? `?${query}` : ""}`,
    );
  }

  /**
   * Get transition details
   */
  async getTransition(transitionId: string): Promise<Transition> {
    return this.request<Transition>(`/api/transitions/${transitionId}`);
  }

  /**
   * Create custom transition (future feature)
   */
  async createTransition(config: Partial<Transition>): Promise<Transition> {
    return this.request<Transition>("/api/transitions", {
      method: "POST",
      body: JSON.stringify(config),
    });
  }
}

// Export singleton instance
export const advancedEditorAPI = new AdvancedEditorAPI();
