# Specification: Video Export

## Goal
Enable users to export edited videos in multiple resolutions and quality settings, supporting both individual clips and combined videos from selected segments.

## User Stories
- As a content creator, I want to export my edited video in 1080p so that I can use it for high-quality content
- As a user, I want to export multiple clips at once so that I can batch process highlights

## Specific Requirements

**Export Model & Database**
- Create Export model with UUID primary key, video_id foreign key, user_id
- Store export settings: resolution (720p, 1080p), quality preset (high, medium, low), format (MP4)
- Track output_url (S3 key), status enum (queued, processing, completed, failed), progress (0-100%)
- Store file_size, estimated_time_remaining, segments array (for combined exports)
- Add timestamps: created_at, updated_at, completed_at
- Create database migration with indexes on video_id, user_id, and status

**Export Service**
- Combine selected segments from timeline into single video using FFmpeg/PyAV
- Re-encode video with specified resolution and quality settings
- Quality presets: High (CRF 18), Medium (CRF 23), Low (CRF 28)
- Maintain aspect ratio, handle resolution upscaling/downscaling
- Upload exported video to S3, generate download URL
- Support exporting individual clips or combined video from segments
- Generate ZIP file for multiple clip exports

**Background Job Processing**
- Create ARQ task: export_video(export_id: str) for async export processing
- Download source video(s) from S3, process segments
- Combine segments, re-encode with settings, upload to S3
- Track progress in Redis (0-100%) with detailed status updates
- Calculate estimated time remaining based on video duration and processing speed
- Handle errors gracefully with retry logic (max 2 attempts for long exports)

**Export API Endpoints**
- POST /api/videos/{id}/export: Create export job with settings (resolution, quality, segments)
- GET /api/exports/{id}: Get export status, progress, and download URL when complete
- GET /api/exports/{id}/download: Generate presigned download URL (expires in 1 hour)
- GET /api/exports: List user's exports with filtering and pagination
- DELETE /api/exports/{id}: Delete export record and S3 file

**Export Modal UI**
- Resolution selector: 720p or 1080p radio buttons
- Quality preset selector: High, Medium, Low dropdown with descriptions
- Export options: Single combined video or Multiple clips (checkbox)
- Segment selection display showing what will be exported
- Estimated file size and processing time display
- Export button triggers background job

**Export Progress Tracking**
- Progress bar component showing percentage (0-100%)
- Real-time updates via Server-Sent Events (SSE) or polling every 2 seconds
- Display current processing stage: "Combining segments...", "Encoding...", "Uploading..."
- Estimated time remaining calculation and display
- Cancel export button (if possible during processing)

**Download Functionality**
- Download button appears when export completes
- Single video: Direct download link
- Multiple clips: Download as ZIP file containing all clips
- Copy shareable link button (if CloudFront URL available)
- Download link expiration handling (regenerate if expired)

**Export Settings**
- Resolution options: 720p (1280x720), 1080p (1920x1080)
- Quality presets with bitrate/CRF values:
  - High: CRF 18, ~8-12 Mbps bitrate
  - Medium: CRF 23, ~4-6 Mbps bitrate  
  - Low: CRF 28, ~2-3 Mbps bitrate
- Format: MP4 (H.264 video, AAC audio) only
- Maintain original aspect ratio, letterbox/pillarbox if needed

**Export History**
- List of past exports with status, date, resolution, quality
- Filter by status (completed, failed, processing)
- Re-download completed exports
- Delete old exports to free storage

**Frontend Component Specifications**

**ExportModal Component (Client Component)**
- Props: videoId (string), segments (Segment[]), isOpen (boolean), onClose (function), onExport (function)
- State: resolution ('720p' | '1080p'), quality ('high' | 'medium' | 'low'), exportType ('single' | 'multiple'), isExporting (boolean)
- Features: Shadcn/ui Dialog, resolution radio buttons, quality dropdown, export type checkbox, estimated file size display
- Validation: Validates settings before allowing export
- API: Calls createExport with settings

**ExportProgress Component (Client Component)**
- Props: exportId (string), videoId (string), onComplete (function, optional)
- State: progress (ExportProgress | null), isPolling (boolean)
- Features: Progress bar, processing stage display, estimated time remaining, polling every 2s
- Pattern: Reuses TranscriptionProgress component pattern
- API: Polls getExportProgress

**ExportHistory Component (Client Component)**
- Props: videoId (string), exports (Export[]), onReDownload (function), onDelete (function)
- State: filterStatus (string), sortBy (string)
- Features: List of exports, filter by status, sort by date, re-download button, delete button
- Rendering: Table or card layout, status badges, date formatting

**DownloadButton Component (Client Component)**
- Props: exportId (string), exportUrl (string, optional), isMultiple (boolean)
- State: isDownloading (boolean)
- Features: Download button, handles single video or ZIP download, loading state
- API: Calls getExportDownload or downloadExport

**Frontend API Client Functions (TypeScript)**
- createExport(videoId: string, settings: ExportSettings): Promise<Export>
- getExport(exportId: string): Promise<Export>
- getExportDownload(exportId: string): Promise<Blob>
- getExports(videoId: string, filters?: ExportFilters): Promise<Export[]>
- deleteExport(exportId: string): Promise<void>
- getExportProgress(exportId: string): Promise<ExportProgress>
- All functions use apiClient with error handling

**TypeScript Type Definitions**
- Export: { id: string, video_id: string, resolution: string, quality: string, format: string, output_url?: string, status: ExportStatus, progress: number, file_size?: number, segments: Segment[], created_at: string, completed_at?: string }
- ExportSettings: { resolution: '720p' | '1080p', quality: 'high' | 'medium' | 'low', segments: Segment[], export_type: 'single' | 'multiple' }
- ExportProgress: { progress: number, status: string, stage: string, estimated_time_remaining?: number }
- ExportStatus: 'queued' | 'processing' | 'completed' | 'failed'
- Types defined in frontend/src/types/export.ts

**State Management**
- Export modal state: Local component state for settings
- Export progress state: Managed in ExportProgress component with polling
- Export history state: Managed in ExportHistory component, fetched on mount
- Integration: ExportModal triggers export, ExportProgress tracks progress, ExportHistory displays results

## Visual Design
No visual assets provided. Follow Shadcn/ui design system for modal, progress bar, and download components.

## Existing Code to Leverage

**Video Processing**
- Use PyAV/FFmpeg patterns from silence-removal and keyword-search-clipping specs
- Follow same S3 storage patterns from video-upload spec
- Reference background job patterns from transcription and silence removal

**Timeline Integration**
- Reference timeline-editor spec for segment selection
- Use segment data from timeline state for export
- Follow same video access patterns

**Background Job Pattern**
- Follow ARQ worker setup pattern from other specs
- Use Redis for progress tracking similar to other async tasks
- Follow same error handling and retry patterns

**API Route Structure**
- Follow FastAPI router pattern from existing routes
- Use get_current_user dependency for authenticated endpoints
- Implement same async/await patterns for database operations
- Use Pydantic schemas for request/response validation

**Database Patterns**
- Use SQLModel async patterns from existing models
- Follow same migration structure with Alembic
- Use JSONB field for segments array storage

**Configuration Management**
- Reference video processing settings from tech stack
- Use S3 and CloudFront patterns from video-upload spec

## Out of Scope
- Export in formats other than MP4 (AVI, MOV, etc.)
- Custom resolution input (preset resolutions only)
- Export with watermarks (post-MVP feature)
- Export with embedded subtitles (post-MVP feature)
- Export with custom bitrate settings (preset qualities only)
- Export audio-only files (video exports only)
- Export as animated GIF (video format only)
- Export with custom aspect ratios (maintain original)
- Export with transitions between segments (hard cuts only)
- Export scheduling or delayed exports (immediate processing only)
- Export to cloud storage destinations (S3 download only)
- Export with custom encoding profiles (preset qualities only)

