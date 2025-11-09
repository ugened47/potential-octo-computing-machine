/**
 * Frontend API Integration Layer
 *
 * This module exports all API clients and utilities for communicating
 * with the backend API.
 */

// API Clients
export { authAPI } from './auth-api';
export type { RegisterData, LoginData, User, AuthResponse } from './auth-api';

export { videoAPI } from './video-api';
export type {
  Video,
  VideoStatus,
  VideoListParams,
  VideoListResponse,
  VideoCreateData,
  VideoUpdateData,
  VideoStats,
} from './video-api';

export { transcriptAPI } from './transcript-api';
export type {
  Transcript,
  TranscriptStatus,
  TranscriptWord,
  TranscriptSegment,
  TranscriptCreateData,
  TranscriptSearchParams,
  TranscriptSearchResult,
} from './transcript-api';

export { timelineAPI } from './timeline-api';
export type {
  WaveformData,
  WaveformParams,
  Segment,
  SegmentType,
  SegmentCreateData,
  SegmentUpdateData,
  SilenceDetectionParams,
  SilenceRemovalParams,
  AudioAnalysis,
} from './timeline-api';

export { clipAPI } from './clip-api';
export type {
  Clip,
  ClipStatus,
  ClipCreateData,
  ClipUpdateData,
  KeywordSearchParams,
  KeywordSearchResult,
  KeywordSearchResponse,
  ClipExportParams,
  ClipListParams,
  ClipListResponse,
} from './clip-api';

// Utilities
export {
  cn,
  formatFileSize,
  formatDuration,
  formatRelativeTime,
  formatTimestamp,
  debounce,
  throttle,
  sleep,
  generateId,
  downloadFile,
  copyToClipboard,
} from './utils';

// Validation
export {
  validateEmail,
  getEmailError,
  validatePassword,
  getPasswordError,
  validatePasswordConfirm,
  getPasswordConfirmError,
  validateVideoFormat,
  getVideoFormatError,
  validateVideoSize,
  validateVideoTitle,
  getVideoTitleError,
  validateVideoDescription,
  getVideoDescriptionError,
  validateKeyword,
  getKeywordError,
  validateFullName,
  getFullNameError,
  validateUrl,
  getUrlError,
  SUPPORTED_VIDEO_FORMATS,
  SUPPORTED_VIDEO_EXTENSIONS,
  MAX_VIDEO_SIZE,
} from './validation';

// Token Storage
export { tokenStorage } from './token-storage';
