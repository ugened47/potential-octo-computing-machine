# Specification: Video Export (Complete Implementation)

## Goal
Implement comprehensive video export functionality allowing users to export edited videos with multiple resolution options, quality presets, and support for both single clips and combined videos.

## User Stories
- As a content creator, I want to export my edited video in different resolutions (720p, 1080p) so that I can optimize for different platforms
- As a user, I want to see real-time export progress so that I know how long the export will take
- As a user, I want to export individual clips or combine them into a single video so that I have flexibility in my output
- As a user, I want to download my exported videos directly or get shareable links so that I can share my content easily
- As a user, I want to export clips in bulk as a ZIP file so that I can efficiently download multiple videos

## Specific Requirements

### Export Model & Database
- Create Export model with video_id (foreign key), user_id (foreign key), export_type ('single' | 'combined' | 'clips')
- Fields: resolution ('720p' | '1080p' | '4k'), format ('mp4' | 'mov' | 'webm'), quality_preset ('high' | 'medium' | 'low')
- Output data: output_s3_key (string), output_url (string, CloudFront URL), file_size_bytes (bigint)
- Processing: status enum ('pending', 'processing', 'completed', 'failed'), progress_percentage (integer 0-100)
- Metadata: segment_selections (JSONB array with start/end times), total_duration_seconds (integer), error_message (text, nullable)
- Timestamps: created_at, updated_at, started_at, completed_at
- Create database migration with indexes on user_id, video_id, status, created_at

### Export Service - Video Processing
- FFmpeg-based video processing with PyAV for Python integration
- Support multiple resolution outputs: 720p (1280x720), 1080p (1920x1080), 4k (3840x2160)
- Quality presets: High (CRF 18, bitrate 8Mbps), Medium (CRF 23, bitrate 4Mbps), Low (CRF 28, bitrate 2Mbps)
- Format support: MP4 (H.264/AAC), MOV (H.264/AAC), WebM (VP9/Opus)
- Segment processing: Extract and combine selected time ranges from source video
- Audio sync: Maintain perfect audio-video synchronization during processing
- Metadata preservation: Copy relevant metadata (creation date, duration) to output
- Optimization: Use hardware acceleration (NVENC, VideoToolbox) when available

### Export Service - Segment Handling
- Accept segment selections as array of {start_time, end_time, clip_id} objects
- Single clip export: Extract one time range to output file
- Combined export: Concatenate multiple time ranges into single output file
- Individual clips export: Process each segment separately, create multiple output files
- Transition handling: Add seamless transitions between concatenated segments (optional crossfade)
- Audio normalization: Normalize audio levels across all segments for consistent volume

### Background Job Processing
- ARQ task: export_video(export_id: str) for async processing with timeout (30 minutes max)
- Fetch export record, validate parameters, download source video from S3
- Extract segments using FFmpeg/PyAV based on start/end times
- Apply resolution scaling, quality settings, and format conversion
- For combined exports: concatenate segments using FFmpeg concat demuxer
- For clips exports: process each segment separately, create ZIP archive
- Upload output file(s) to S3, generate CloudFront URLs
- Update export record with output URLs, file size, completion status
- Track progress in Redis (0-100%) with estimated time remaining
- Error handling: capture FFmpeg errors, update status to 'failed', store error message
- Resource cleanup: delete temporary files after successful upload

### Export API Endpoints
- POST /api/videos/{id}/export: Create new export job
  - Body: {resolution, format, quality, export_type, segments: [{start, end, clip_id}]}
  - Validates segment selections, creates Export record, enqueues ARQ job
  - Returns export_id and initial status
- GET /api/exports/{id}: Get export details and status
  - Returns Export object with current status, progress, output_url (if completed)
- GET /api/exports/{id}/progress: Get real-time progress updates
  - Returns {progress, status, estimated_time_remaining, current_stage}
  - Suitable for SSE (Server-Sent Events) streaming
- GET /api/exports/{id}/download: Generate download URL for completed export
  - Returns S3 presigned URL (expires in 1 hour) for secure download
  - For clips exports: returns presigned URL for ZIP file
- DELETE /api/exports/{id}: Cancel in-progress export or delete completed export
  - Cancels ARQ job if processing, deletes S3 files, marks export as deleted
- GET /api/videos/{id}/exports: List all exports for a video
  - Returns paginated list of exports with status, created dates, file sizes

### ExportModal Component
- Client component for configuring and initiating video export
- Props: videoId (string), segments (Segment[], optional), isOpen (boolean), onClose (function)
- Resolution selector: Radio group or select for 720p, 1080p, 4k (with size estimates)
- Quality preset selector: Radio group for High, Medium, Low (with quality descriptions)
- Format selector: Radio group for MP4, MOV, WebM (with compatibility info)
- Export type selector: Radio group for 'Combined Video', 'Individual Clips' (conditional on segments)
- Segment preview: Display selected segments with durations, total output duration
- Size estimation: Real-time calculation of approximate output file size based on settings
- Export button: Triggers createExport API call, validates selections, handles errors
- Cost estimation: Display estimated processing time and cost (if applicable)
- Validation: Ensure at least one segment selected for clips export, format compatibility checks
- Loading state: Disable inputs during export creation, show spinner on export button

### ExportProgress Component
- Client component displaying real-time export progress with polling
- Props: exportId (string), onComplete (function, optional), pollInterval (number, default 2000ms)
- Progress bar: Visual progress indicator (0-100%) using Shadcn Progress component
- Status display: Current processing stage ('Downloading', 'Processing', 'Uploading', 'Complete')
- Time estimates: Display estimated time remaining, elapsed time
- Stage indicators: Show current stage with icons (Download, Settings, Upload, CheckCircle)
- Error handling: Display error messages with retry option, allow cancellation
- Polling mechanism: Fetch progress every pollInterval, stop when complete or failed
- Completion callback: Call onComplete when export reaches 100% and status is 'completed'
- Cancel button: Allow user to cancel in-progress export, confirm cancellation
- Preview: Show thumbnail or video preview when export completes

### ExportsList Component
- Client component displaying list of all exports for a video
- Props: videoId (string), className (string, optional)
- List rendering: Display exports in table or card format with key information
- Export details: Show resolution, format, quality, file size, created date, status
- Actions: Download button, delete button, view details button for each export
- Status badges: Color-coded badges for pending, processing, completed, failed, cancelled
- Sorting: Allow sorting by date, status, file size (descending/ascending)
- Filtering: Filter by status, export type, resolution
- Empty state: Show message when no exports exist, prompt to create first export
- Loading state: Skeleton loaders while fetching exports list
- Pagination: Client-side pagination for large export lists (10 per page)

### ExportSettings Component
- Client component for managing user export preferences and presets
- Props: onSave (function), initialSettings (ExportSettings, optional)
- Default settings: Allow users to set default resolution, format, quality
- Custom presets: Create and save custom export configurations (name, settings)
- Preset management: Edit, delete, duplicate custom presets
- Quality recommendations: Show recommended settings for different use cases (YouTube, Instagram, etc.)
- Storage: Save preferences to backend user settings or localStorage
- Form validation: Validate custom preset names, settings combinations
- Reset option: Reset to default factory settings

### Frontend API Client Functions
- createExport(videoId, config): Creates export job, returns Promise<Export>
  - Config: {resolution, format, quality, export_type, segments}
- getExport(exportId): Fetches export details, returns Promise<Export>
- getExportProgress(exportId): Fetches progress data, returns Promise<ExportProgress>
- getExportDownloadUrl(exportId): Gets presigned download URL, returns Promise<{url: string}>
- cancelExport(exportId): Cancels export, returns Promise<void>
- deleteExport(exportId): Deletes export and files, returns Promise<void>
- getVideoExports(videoId, params): Lists exports for video, returns Promise<{exports: Export[], total: number}>
  - Params: {page, limit, status, sort}
- downloadExport(exportId): Triggers browser download using presigned URL
- All functions use apiClient with proper error handling and TypeScript types

### TypeScript Type Definitions
- Export interface: id, video_id, user_id, export_type, resolution, format, quality_preset
- ExportStatus type: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
- ExportType type: 'single' | 'combined' | 'clips'
- Resolution type: '720p' | '1080p' | '4k'
- Format type: 'mp4' | 'mov' | 'webm'
- QualityPreset type: 'high' | 'medium' | 'low'
- ExportProgress interface: progress, status, estimated_time_remaining, current_stage, elapsed_time
- ExportConfig interface: resolution, format, quality, export_type, segments
- ExportSegment interface: start_time, end_time, clip_id (optional)
- ExportSettings interface: default_resolution, default_format, default_quality, custom_presets

### Testing Requirements
- Backend unit tests: Test export service functions (segment extraction, concatenation, format conversion)
- Backend integration tests: Test API endpoints with mocked FFmpeg/S3
- Worker tests: Test ARQ task with mock video processing, verify progress tracking
- Frontend component tests: Test ExportModal form validation, ExportProgress polling, ExportsList rendering
- E2E tests: Full export workflow (configure, export, monitor progress, download)
- Performance tests: Test export speed for different resolutions, verify resource usage
- Error handling tests: Test FFmpeg failures, S3 upload failures, cancellation scenarios

### Performance Considerations
- Parallel processing: Process multiple segments in parallel when possible
- Streaming: Use streaming for large video processing to minimize memory usage
- Caching: Cache export configurations for quick re-exports with same settings
- Progress accuracy: Update progress based on actual processing stages (not just time estimates)
- Resource limits: Set max concurrent exports per user (e.g., 3) to prevent resource exhaustion
- Cleanup: Automatically delete temp files and old exports (> 30 days) to save storage

### Security Considerations
- User ownership: Verify user owns source video before allowing export
- Rate limiting: Limit exports per user per hour (e.g., 10 per hour)
- File size limits: Enforce max export file size (e.g., 5GB) to prevent abuse
- URL expiration: S3 presigned URLs expire after 1 hour for security
- Input validation: Validate segment times are within video duration
- Cost control: Track export processing time and costs per user

### Error Handling
- FFmpeg errors: Capture and parse FFmpeg stderr, provide user-friendly error messages
- S3 failures: Retry S3 uploads with exponential backoff (max 3 attempts)
- Invalid segments: Validate segment times before processing, return 400 Bad Request
- Insufficient storage: Check S3 storage quota before export, return 507 Insufficient Storage
- Timeout handling: Handle long-running exports, provide option to extend timeout
- Cancellation: Gracefully stop FFmpeg process, clean up partial files

### Integration Points
- Timeline Editor: Export button in timeline toolbar, passes selected segments
- Video Editor: Export option in editor menu, includes all applied edits
- Dashboard: Quick export action on video cards, uses default settings
- Clips List: Export individual clips or selected clips in bulk
- Settings: User export preferences, default quality settings

## Success Criteria
- Users can export videos in multiple resolutions (720p, 1080p, 4k) and formats
- Export progress is displayed in real-time with accurate time estimates
- Single clips, combined videos, and bulk clip exports all work correctly
- Exported videos maintain perfect audio-video sync and quality
- Users can download exports directly or get shareable links
- Export processing is reliable with proper error handling and retry logic
- Export API endpoints have comprehensive test coverage (>90%)
