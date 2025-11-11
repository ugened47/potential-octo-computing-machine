// TypeScript type definitions for Advanced Editor feature

// ==================== Enums ====================

export type ProjectStatus = 'draft' | 'rendering' | 'completed' | 'error';

export type TrackType = 'video' | 'audio' | 'image' | 'text' | 'overlay';

export type ItemType = 'video_clip' | 'audio_clip' | 'image' | 'text' | 'shape';

export type SourceType = 'video' | 'asset' | 'text' | 'generated';

export type AssetType = 'image' | 'audio' | 'font' | 'graphic' | 'template';

export type TransitionType = 'fade' | 'dissolve' | 'slide' | 'wipe' | 'zoom' | 'blur' | 'custom';

export type TransitionDirection = 'in' | 'out';

export type EffectType = 'filter' | 'color' | 'blur' | 'sharpen' | 'distort' | 'custom';

export type BlendMode = 'normal' | 'multiply' | 'screen' | 'overlay';

export type RenderQuality = 'low' | 'medium' | 'high' | 'max';

export type RenderFormat = 'mp4' | 'mov' | 'webm';

export type RenderStatus = 'queued' | 'processing' | 'completed' | 'error';

export type TextAlignment = 'left' | 'center' | 'right';

// ==================== Interfaces ====================

// Project
export interface Project {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  video_id?: string;
  width: number;
  height: number;
  frame_rate: number;
  duration_seconds: number;
  background_color: string;
  canvas_settings?: Record<string, any>;
  export_settings?: Record<string, any>;
  thumbnail_url?: string;
  status: ProjectStatus;
  last_rendered_at?: string;
  render_output_url?: string;
  created_at: string;
  updated_at: string;
  tracks?: Track[];
}

// Track
export interface Track {
  id: string;
  project_id: string;
  track_type: TrackType;
  name: string;
  z_index: number;
  is_locked: boolean;
  is_visible: boolean;
  is_muted: boolean;
  volume: number;
  opacity: number;
  blend_mode: BlendMode;
  track_order: number;
  created_at: string;
  updated_at: string;
  items?: TrackItem[];
}

// TrackItem
export interface TrackItem {
  id: string;
  track_id: string;
  item_type: ItemType;
  source_type: SourceType;
  source_id?: string;
  source_url?: string;
  start_time: number;
  end_time: number;
  duration: number;
  trim_start: number;
  trim_end: number;
  position_x: number;
  position_y: number;
  scale_x: number;
  scale_y: number;
  rotation: number;
  crop_settings?: CropSettings;
  transform_settings?: TransformSettings;
  text_content?: string;
  text_style?: TextStyle;
  effects?: any[];
  transition_in?: string;
  transition_out?: string;
  created_at: string;
  updated_at: string;
}

// Asset
export interface Asset {
  id: string;
  user_id: string;
  asset_type: AssetType;
  name: string;
  file_url: string;
  file_size: number;
  mime_type: string;
  width?: number;
  height?: number;
  duration_seconds?: number;
  metadata?: Record<string, any>;
  thumbnail_url?: string;
  is_public: boolean;
  tags: string[];
  usage_count: number;
  created_at: string;
  updated_at: string;
}

// Transition
export interface Transition {
  id: string;
  name: string;
  transition_type: TransitionType;
  direction?: TransitionDirection;
  default_duration: number;
  parameters?: Record<string, any>;
  preview_url?: string;
  is_builtin: boolean;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

// CompositionEffect
export interface CompositionEffect {
  id: string;
  name: string;
  effect_type: EffectType;
  parameters: Record<string, any>;
  ffmpeg_filter?: string;
  is_builtin: boolean;
  preview_url?: string;
  created_at: string;
}

// ==================== Configuration Interfaces ====================

// ProjectConfig
export interface ProjectConfig {
  name: string;
  description?: string;
  video_id?: string;
  width: number;
  height: number;
  frame_rate: number;
  duration: number;
}

// TrackConfig
export interface TrackConfig {
  track_type: TrackType;
  name: string;
  z_index?: number;
  volume?: number;
  opacity?: number;
}

// TrackItemConfig
export interface TrackItemConfig {
  item_type: ItemType;
  source_type: SourceType;
  source_id?: string;
  source_url?: string;
  start_time: number;
  end_time: number;
  position_x?: number;
  position_y?: number;
  scale_x?: number;
  scale_y?: number;
  rotation?: number;
  text_content?: string;
  text_style?: TextStyle;
  transition_in?: string;
  transition_out?: string;
}

// RenderConfig
export interface RenderConfig {
  quality: RenderQuality;
  format: RenderFormat;
  resolution?: {
    width: number;
    height: number;
  };
  codec?: string;
  bitrate?: number;
  audio_codec?: string;
  audio_bitrate?: number;
}

// RenderProgress
export interface RenderProgress {
  progress: number; // 0-100
  stage: string;
  status: RenderStatus;
  estimated_remaining: number; // seconds
}

// ValidationResult
export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

// ==================== Nested Property Interfaces ====================

// TextStyle
export interface TextStyle {
  font_family: string;
  font_size: number;
  color: string;
  alignment: TextAlignment;
  bold: boolean;
  italic: boolean;
  underline: boolean;
  shadow: boolean;
  outline: boolean;
}

// CropSettings
export interface CropSettings {
  top: number; // pixels
  bottom: number; // pixels
  left: number; // pixels
  right: number; // pixels
}

// TransformSettings
export interface TransformSettings {
  skew_x?: number;
  skew_y?: number;
  flip_horizontal?: boolean;
  flip_vertical?: boolean;
}

// ==================== Response Interfaces ====================

// API response wrappers
export interface ProjectsResponse {
  projects: Project[];
  total: number;
}

export interface AssetsResponse {
  assets: Asset[];
  total: number;
}

export interface TransitionsResponse {
  transitions: Transition[];
}

export interface RenderJobResponse {
  job_id: string;
  estimated_time: number;
}

export interface SplitItemResponse {
  item1: TrackItem;
  item2: TrackItem;
}

export interface DeleteResponse {
  message: string;
}

// ==================== Resolution Presets ====================

export interface ResolutionPreset {
  name: string;
  width: number;
  height: number;
  description: string;
}

export const RESOLUTION_PRESETS: ResolutionPreset[] = [
  { name: '1080p (Full HD)', width: 1920, height: 1080, description: 'Standard HD video' },
  { name: '720p (HD)', width: 1280, height: 720, description: 'HD video, smaller file size' },
  { name: '4K (Ultra HD)', width: 3840, height: 2160, description: 'Ultra high definition' },
  { name: 'Vertical (9:16)', width: 1080, height: 1920, description: 'For Instagram Stories, TikTok' },
  { name: 'Square (1:1)', width: 1080, height: 1080, description: 'For Instagram Feed' },
  { name: 'Custom', width: 0, height: 0, description: 'Custom resolution' },
];

// ==================== Quality Presets ====================

export interface QualityPreset {
  name: RenderQuality;
  label: string;
  resolution: string;
  bitrate: string;
  description: string;
}

export const QUALITY_PRESETS: QualityPreset[] = [
  { name: 'low', label: 'Low', resolution: '720p', bitrate: '2 Mbps', description: 'Fast export, smaller file size' },
  { name: 'medium', label: 'Medium', resolution: '1080p', bitrate: '5 Mbps', description: 'Balanced quality and size' },
  { name: 'high', label: 'High', resolution: '1080p', bitrate: '10 Mbps', description: 'High quality, larger file' },
  { name: 'max', label: 'Maximum', resolution: '4K', bitrate: '20 Mbps', description: 'Best quality, very large file' },
];

// ==================== Utility Types ====================

// For partial updates
export type ProjectUpdate = Partial<Omit<Project, 'id' | 'user_id' | 'created_at' | 'updated_at'>>;
export type TrackUpdate = Partial<Omit<Track, 'id' | 'project_id' | 'created_at' | 'updated_at'>>;
export type TrackItemUpdate = Partial<Omit<TrackItem, 'id' | 'track_id' | 'created_at' | 'updated_at'>>;
export type AssetUpdate = Partial<Pick<Asset, 'name' | 'tags'>>;

// For query parameters
export interface ProjectsQueryParams {
  status?: ProjectStatus;
  limit?: number;
  offset?: number;
  sort?: string;
}

export interface AssetsQueryParams {
  asset_type?: AssetType;
  tags?: string[];
  limit?: number;
  offset?: number;
  search?: string;
}

export interface TransitionsQueryParams {
  transition_type?: TransitionType;
  is_public?: boolean;
}
