# Task Breakdown: Video Export (Complete Implementation)

## Overview
Total Tasks: 6 task groups, 60+ sub-tasks

## Task List

### Database Layer

#### Task Group 1: Export Model and Migrations
**Dependencies:** Video Upload (Task Group 1)

- [ ] 1.0 Complete database layer
  - [ ] 1.1 Write 2-8 focused tests for Export model functionality
    - Test Export model creation with required fields (video_id, user_id, export_type, resolution, format, quality_preset)
    - Test Export model validation (status enum, export_type enum, resolution enum)
    - Test Export model relationships with Video and User
    - Test Export model segment_selections JSONB field storage and retrieval
    - Test Export model timestamps (created_at, updated_at, started_at, completed_at)
    - Test Export model progress_percentage constraints (0-100)
    - Test Export model file_size_bytes and output_url storage
  - [ ] 1.2 Create Export model with validations
    - Fields: id (UUID), video_id (foreign key), user_id (foreign key)
    - export_type enum ('single', 'combined', 'clips')
    - resolution enum ('720p', '1080p', '4k'), format enum ('mp4', 'mov', 'webm')
    - quality_preset enum ('high', 'medium', 'low')
    - output_s3_key (string), output_url (string), file_size_bytes (bigint)
    - status enum ('pending', 'processing', 'completed', 'failed', 'cancelled')
    - progress_percentage (integer, default 0, check constraint 0-100)
    - segment_selections (JSONB array), total_duration_seconds (integer)
    - error_message (text, nullable)
    - Timestamps: created_at, updated_at, started_at, completed_at
    - Reuse pattern from: Video model in `backend/app/models/video.py`
  - [ ] 1.3 Create migration for exports table
    - Add indexes on user_id, video_id, status, created_at for fast lookups
    - Foreign key relationships to videos and users tables
    - Add status enum type (pending, processing, completed, failed, cancelled)
    - Add export_type enum type (single, combined, clips)
    - Add resolution, format, quality_preset enum types
    - JSONB column for segment_selections
    - Check constraint for progress_percentage (0-100)
  - [ ] 1.4 Set up associations
    - Export belongs_to Video (video_id foreign key)
    - Export belongs_to User (user_id foreign key)
    - Video has_many Exports
    - User has_many Exports
  - [ ] 1.5 Ensure database layer tests pass
    - Run ONLY the 2-8 tests written in 1.1
    - Verify migrations run successfully
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1 pass
- Export model passes validation tests
- Migrations run successfully
- Associations work correctly
- Indexes are created and optimized

### Backend API Layer

#### Task Group 2: Export Service and Core Processing
**Dependencies:** Task Group 1, ARQ Worker setup, FFmpeg/PyAV installed

- [ ] 2.0 Complete export service layer
  - [ ] 2.1 Write 2-8 focused tests for export service functions
    - Test video segment extraction for single clip
    - Test segment concatenation for combined export
    - Test multiple clip processing for clips export
    - Test resolution scaling (720p, 1080p, 4k)
    - Test quality preset application (high, medium, low)
    - Test format conversion (mp4, mov, webm)
    - Test audio-video sync maintenance
    - Test error handling for invalid segments
  - [ ] 2.2 Create FFmpeg/PyAV integration service
    - FFmpeg wrapper functions for video processing
    - Resolution scaling: 720p (1280x720), 1080p (1920x1080), 4k (3840x2160)
    - Quality presets: High (CRF 18, 8Mbps), Medium (CRF 23, 4Mbps), Low (CRF 28, 2Mbps)
    - Format conversion: MP4 (H.264/AAC), MOV (H.264/AAC), WebM (VP9/Opus)
    - Hardware acceleration detection and usage (NVENC, VideoToolbox)
    - Progress callback integration for real-time updates
    - Reuse pattern from: `backend/app/services/video_processing.py` (if exists)
  - [ ] 2.3 Create segment extraction service
    - Extract single segment using FFmpeg -ss and -t flags
    - Extract multiple segments for combined export
    - Create FFmpeg concat demuxer file for seamless concatenation
    - Handle edge cases (segments at video start/end)
    - Validate segment times are within video duration
    - Optimize extraction (avoid re-encoding when possible)
  - [ ] 2.4 Create export processing service
    - Orchestrate full export workflow
    - Download source video from S3
    - Process segments based on export_type (single, combined, clips)
    - Apply resolution, quality, format settings
    - Generate output file(s)
    - Upload to S3 with organized folder structure
    - Generate CloudFront URLs
    - Create ZIP archive for clips exports
    - Calculate output file sizes
  - [ ] 2.5 Implement progress tracking
    - Track progress in Redis with key: export_progress:{export_id}
    - Update progress at key stages: downloading (0-10%), processing (10-90%), uploading (90-100%)
    - Calculate estimated time remaining based on processing speed
    - Store current processing stage ('downloading', 'processing', 'uploading', 'complete')
    - Update Export model progress_percentage in database periodically
  - [ ] 2.6 Ensure export service tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify FFmpeg integration works with test video files
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- Export service can process single clips, combined videos, and bulk clips
- FFmpeg integration works with all supported formats and resolutions
- Progress tracking accurately reflects processing state
- Error handling covers FFmpeg failures and invalid inputs

#### Task Group 3: Export API Endpoints
**Dependencies:** Task Group 2

- [ ] 3.0 Complete API endpoints
  - [ ] 3.1 Write 2-8 focused tests for export endpoints
    - Test POST /api/videos/{id}/export creates export and enqueues job
    - Test POST /api/videos/{id}/export validates segment selections
    - Test POST /api/videos/{id}/export requires authentication
    - Test GET /api/exports/{id} returns export details
    - Test GET /api/exports/{id}/progress returns real-time progress
    - Test GET /api/exports/{id}/download generates presigned URL
    - Test DELETE /api/exports/{id} cancels and deletes export
    - Test GET /api/videos/{id}/exports lists all exports for video
  - [ ] 3.2 Create export API routes file
    - POST /api/videos/{video_id}/export: Create new export
      - Request body validation (resolution, format, quality, export_type, segments)
      - Create Export record in database
      - Enqueue export_video ARQ job
      - Return export_id and initial status
    - GET /api/exports/{export_id}: Get export details
      - Return Export object with all fields
      - Include output_url if status is 'completed'
    - GET /api/exports/{export_id}/progress: Get real-time progress
      - Fetch progress from Redis
      - Return {progress, status, estimated_time_remaining, current_stage}
    - GET /api/exports/{export_id}/download: Generate download URL
      - Verify export is completed
      - Generate S3 presigned URL (1 hour expiration)
      - Return {url: string, expires_at: datetime}
    - DELETE /api/exports/{export_id}: Cancel or delete export
      - Cancel ARQ job if status is 'processing'
      - Delete S3 files
      - Mark export as 'cancelled' or delete record
    - GET /api/videos/{video_id}/exports: List video exports
      - Support pagination (page, limit)
      - Support filtering (status, export_type)
      - Support sorting (created_at, file_size)
      - Return {exports: Export[], total: number}
    - Follow pattern from: `backend/app/api/routes/export.py`
  - [ ] 3.3 Create Pydantic schemas for validation
    - ExportCreateRequest schema (resolution, format, quality, export_type, segments)
    - ExportSegmentInput schema (start_time, end_time, clip_id optional)
    - ExportResponse schema (all Export model fields)
    - ExportProgressResponse schema (progress, status, estimated_time_remaining, current_stage)
    - ExportDownloadResponse schema (url, expires_at)
    - ExportListResponse schema (exports, total, page, limit)
    - Enum classes for ExportType, Resolution, Format, QualityPreset
    - Reuse pattern from: `backend/app/schemas/export.py`
  - [ ] 3.4 Implement authentication and authorization
    - Use get_current_user dependency on all endpoints
    - Verify user owns source video before creating export
    - Verify user owns export before accessing/deleting
    - Rate limiting: 10 exports per hour per user
  - [ ] 3.5 Add error handling and validation
    - Validate segment times are within video duration
    - Validate video exists and is in 'completed' status
    - Handle missing exports (404 Not Found)
    - Handle invalid export states (e.g., download before complete)
    - Return appropriate HTTP status codes and error messages
  - [ ] 3.6 Ensure API endpoint tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify all endpoints work with authentication
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 3.1 pass
- All API endpoints work correctly with proper validation
- Authentication and authorization are enforced
- Error handling covers all edge cases
- Rate limiting prevents abuse

### Background Jobs

#### Task Group 4: ARQ Worker Task for Export Processing
**Dependencies:** Task Group 2, Task Group 3

- [ ] 4.0 Complete worker task implementation
  - [ ] 4.1 Write 2-8 focused tests for export worker task
    - Test export_video task completes successfully for single clip
    - Test export_video task completes for combined export
    - Test export_video task completes for clips export (with ZIP)
    - Test export_video task updates progress in Redis
    - Test export_video task handles FFmpeg errors gracefully
    - Test export_video task handles S3 upload failures with retries
    - Test export_video task cleans up temporary files
    - Test export_video task can be cancelled mid-processing
  - [ ] 4.2 Create export_video ARQ task
    - Task signature: async def export_video(ctx, export_id: str)
    - Fetch Export record from database
    - Fetch source Video record, download from S3
    - Extract audio and video streams using PyAV
    - Process segments based on export_type
      - Single: Extract one segment
      - Combined: Concatenate multiple segments
      - Clips: Process each segment separately
    - Apply resolution, quality, format settings
    - Update progress in Redis throughout processing
    - Upload output file(s) to S3 (folder: exports/{user_id}/{export_id}/)
    - For clips export: Create ZIP archive of all clips
    - Generate CloudFront URLs for outputs
    - Update Export record: output_s3_key, output_url, file_size_bytes, status, completed_at
    - Clean up temporary files (source video, intermediate files, output files)
    - Handle errors: Update Export status to 'failed', store error_message
    - Register task in worker.py WorkerSettings
  - [ ] 4.3 Implement progress tracking in worker
    - Update progress at each stage:
      - 0%: Task started
      - 10%: Video downloaded
      - 20%: Segments extracted
      - 30-80%: Processing (update based on FFmpeg progress)
      - 90%: Uploading to S3
      - 100%: Complete
    - Store progress in Redis: export_progress:{export_id}
    - Update Export.progress_percentage in database every 10%
    - Calculate estimated_time_remaining based on elapsed time and progress
  - [ ] 4.4 Implement cancellation support
    - Check for cancellation signal periodically during processing
    - Use Redis key: export_cancel:{export_id}
    - Terminate FFmpeg process gracefully if cancelled
    - Update Export status to 'cancelled'
    - Clean up partial output files
  - [ ] 4.5 Implement resource management
    - Set maximum concurrent export jobs (e.g., 5 globally, 2 per user)
    - Use temporary directories for processing (auto-cleanup on completion)
    - Monitor memory usage, fail gracefully if exceeds limits
    - Set job timeout (30 minutes max)
    - Implement exponential backoff for S3 upload retries (max 3 attempts)
  - [ ] 4.6 Ensure worker task tests pass
    - Run ONLY the 2-8 tests written in 4.1
    - Verify task completes successfully in test environment
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 4.1 pass
- ARQ task processes exports successfully for all export types
- Progress tracking works accurately in Redis
- Cancellation mechanism works correctly
- Resource management prevents system overload
- Error handling and retries work as expected

### Frontend Components

#### Task Group 5: Export UI Components
**Dependencies:** Task Group 3

- [ ] 5.0 Complete export UI components
  - [ ] 5.1 Write 2-8 focused tests for export components
    - Test ExportModal renders with all configuration options
    - Test ExportModal validates segment selections
    - Test ExportModal creates export on submit
    - Test ExportProgress polls and displays progress correctly
    - Test ExportProgress handles completion callback
    - Test ExportsList displays exports with correct statuses
    - Test ExportsList download and delete actions work
    - Test ExportSettings saves and loads user preferences
  - [ ] 5.2 Create TypeScript type definitions
    - Export interface (id, video_id, user_id, export_type, resolution, format, quality_preset, output_url, status, progress_percentage, etc.)
    - ExportStatus type: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
    - ExportType type: 'single' | 'combined' | 'clips'
    - Resolution type: '720p' | '1080p' | '4k'
    - Format type: 'mp4' | 'mov' | 'webm'
    - QualityPreset type: 'high' | 'medium' | 'low'
    - ExportProgress interface (progress, status, estimated_time_remaining, current_stage, elapsed_time)
    - ExportConfig interface (resolution, format, quality, export_type, segments)
    - ExportSegment interface (start_time, end_time, clip_id optional)
    - ExportSettings interface (default_resolution, default_format, default_quality, custom_presets)
    - Create file: `frontend/src/types/export.ts`
  - [ ] 5.3 Create frontend API client functions
    - createExport(videoId, config): Creates export, returns Promise<Export>
    - getExport(exportId): Fetches export details, returns Promise<Export>
    - getExportProgress(exportId): Fetches progress, returns Promise<ExportProgress>
    - getExportDownloadUrl(exportId): Gets download URL, returns Promise<{url: string, expires_at: string}>
    - cancelExport(exportId): Cancels export, returns Promise<void>
    - deleteExport(exportId): Deletes export, returns Promise<void>
    - getVideoExports(videoId, params): Lists exports, returns Promise<{exports: Export[], total: number}>
    - downloadExport(exportId): Triggers browser download, returns Promise<void>
    - All functions use apiClient with proper error handling and TypeScript types
    - Create or update: `frontend/src/lib/api/export.ts`
  - [ ] 5.4 Create ExportModal component
    - Client component ('use client') for export configuration
    - Props: videoId, segments (optional), isOpen, onClose, onExportCreated (optional)
    - Resolution selector: Radio group with 720p, 1080p, 4k options
    - Quality preset selector: Radio group with High, Medium, Low options
    - Format selector: Radio group with MP4, MOV, WebM options
    - Export type selector: Radio group with 'Combined Video', 'Individual Clips'
    - Segment preview: Display selected segments with durations, show total duration
    - Size estimation: Calculate and display estimated file size based on settings
    - Form validation: Ensure valid selections, at least one segment for clips export
    - Submit handler: Call createExport API, handle success/error, close modal
    - Loading states: Disable form during submission
    - Shadcn components: Dialog, RadioGroup, Button, Label, Alert
    - Create file: `frontend/src/components/export/ExportModal.tsx`
  - [ ] 5.5 Create ExportProgress component
    - Client component ('use client') for displaying export progress
    - Props: exportId, onComplete (optional), pollInterval (default 2000ms)
    - Polling mechanism: Call getExportProgress every pollInterval ms
    - Progress display: Shadcn Progress bar (0-100%), percentage text
    - Stage indicators: Display current stage with icons (Download, Settings, Upload, CheckCircle)
    - Time display: Show estimated time remaining, elapsed time
    - Status display: Show current status text (Processing, Complete, Failed)
    - Error handling: Display error messages, provide retry button
    - Cancel button: Allow user to cancel in-progress export with confirmation
    - Completion handling: Stop polling when complete, call onComplete callback
    - Preview: Show thumbnail or video preview when complete
    - Shadcn components: Progress, Button, Card, AlertCircle, CheckCircle icons
    - Create file: `frontend/src/components/export/ExportProgress.tsx`
  - [ ] 5.6 Create ExportsList component
    - Client component displaying all exports for a video
    - Props: videoId, className (optional)
    - Fetch exports on mount using getVideoExports
    - Table or card layout with export details:
      - Created date, export type, resolution, format, quality
      - File size, status badge, progress (if processing)
    - Status badges: Color-coded with Shadcn Badge (pending: gray, processing: blue, completed: green, failed: red)
    - Action buttons:
      - Download (completed exports only)
      - Delete (with confirmation dialog)
      - View details (expand row or open modal)
    - Sorting: Sort by date, status, file size
    - Filtering: Filter by status, export type
    - Pagination: 10 exports per page
    - Empty state: "No exports yet" with icon and create button
    - Loading state: Skeleton loaders for table rows
    - Auto-refresh: Refresh list when export completes
    - Shadcn components: Table, Button, Badge, Dialog, Skeleton
    - Create file: `frontend/src/components/export/ExportsList.tsx`
  - [ ] 5.7 Create ExportSettings component
    - Client component for managing export preferences
    - Props: onSave, initialSettings (optional)
    - Default settings form:
      - Default resolution select
      - Default format select
      - Default quality select
    - Custom presets section:
      - List of saved presets
      - Add preset button (opens modal)
      - Edit/delete buttons for each preset
    - Preset modal: Form to create/edit preset (name, settings)
    - Quality recommendations: Display recommended settings for different platforms
    - Save button: Save settings to backend or localStorage
    - Reset button: Reset to factory defaults
    - Shadcn components: Form, Input, Select, Button, Card, Dialog
    - Create file: `frontend/src/components/export/ExportSettings.tsx`
  - [ ] 5.8 Integrate export components into existing UI
    - Add Export button to Timeline Editor toolbar
    - Add Export option to Video Editor menu
    - Add Quick Export action to Dashboard video cards
    - Add Export tab to Video details page with ExportsList
    - Add Export settings page to user Settings
  - [ ] 5.9 Ensure frontend component tests pass
    - Run ONLY the 2-8 tests written in 5.1
    - Verify components render correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 5.1 pass
- ExportModal allows configuration of all export options
- ExportProgress displays real-time progress accurately
- ExportsList shows all exports with correct statuses and actions
- ExportSettings allows customization of default preferences
- Export UI is integrated into existing pages/components
- All components follow Shadcn/ui design patterns

### Integration & Testing

#### Task Group 6: E2E Testing and Integration Verification
**Dependencies:** Task Group 4, Task Group 5

- [ ] 6.0 Complete integration testing
  - [ ] 6.1 Write E2E test: Complete export workflow
    - User opens export modal from timeline editor
    - User selects resolution, quality, format, export type
    - User submits export configuration
    - Export progress is displayed and updates in real-time
    - Export completes successfully
    - User downloads exported video
    - Verify downloaded file is valid and correct size
  - [ ] 6.2 Write E2E test: Bulk clips export
    - User selects multiple clips in clips list
    - User opens export modal, selects 'Individual Clips'
    - Export processes all clips
    - User downloads ZIP file
    - Verify ZIP contains all clips with correct filenames
  - [ ] 6.3 Write E2E test: Export cancellation
    - User starts export
    - User cancels export mid-processing
    - Verify export status becomes 'cancelled'
    - Verify partial files are cleaned up
  - [ ] 6.4 Write E2E test: Export error handling
    - Trigger export with invalid parameters
    - Verify error message is displayed
    - User corrects parameters and retries
    - Export completes successfully
  - [ ] 6.5 Performance test: Large video export
    - Export 1-hour video at 1080p high quality
    - Verify processing completes within expected time
    - Verify memory usage stays within limits
    - Verify output file quality matches expected
  - [ ] 6.6 Integration test: Multiple concurrent exports
    - Start 3 exports for same user simultaneously
    - Verify all exports process correctly
    - Verify concurrency limits are enforced
    - Verify no resource conflicts or deadlocks
  - [ ] 6.7 Verify all integration points
    - Timeline Editor → Export (with segments)
    - Video Editor → Export (full video)
    - Dashboard → Quick Export (default settings)
    - Clips List → Bulk Export
    - Settings → Export Preferences
  - [ ] 6.8 Run full test suite
    - Run all backend tests (pytest)
    - Run all frontend tests (Vitest)
    - Run E2E tests (Playwright)
    - Verify test coverage >90% for export feature
    - Fix any failing tests

**Acceptance Criteria:**
- All E2E tests pass successfully
- Export workflow is fully functional end-to-end
- Performance meets requirements (process 30-min video in <10 min)
- No integration issues with existing features
- Test coverage >90% for export code
- All edge cases and error scenarios are handled

## Implementation Strategy

### Phase 1: Foundation (Tasks 1.0 - 2.0)
- Set up database models and migrations
- Implement core export service with FFmpeg integration
- Test basic video segment extraction and processing

### Phase 2: API Layer (Tasks 3.0 - 4.0)
- Create API endpoints for export operations
- Implement ARQ worker task for background processing
- Set up progress tracking and cancellation

### Phase 3: Frontend (Tasks 5.0)
- Build export configuration modal
- Create progress display component
- Build exports list management UI
- Integrate into existing pages

### Phase 4: Testing & Polish (Tasks 6.0)
- Write comprehensive E2E tests
- Perform load and performance testing
- Fix bugs and optimize performance
- Update documentation

## Notes
- Use existing FFmpeg/PyAV patterns from silence removal and video processing
- Follow authentication patterns from existing API endpoints
- Follow UI patterns from existing Shadcn/ui components
- Ensure proper resource cleanup to prevent disk space issues
- Monitor S3 costs for large exports
- Consider implementing export queue priority for paid users
