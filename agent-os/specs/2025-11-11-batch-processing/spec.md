# Specification: Batch Processing

## Goal
Enable content creators to upload and process multiple videos simultaneously with shared settings, manage queued jobs, and export multiple videos in bulk to dramatically reduce time spent on repetitive video processing tasks.

## User Stories
- As a content creator, I want to upload multiple videos at once so that I can process an entire series or event recording without uploading each video individually
- As a podcaster, I want to apply the same transcription and silence removal settings to all episodes so that I maintain consistent editing across my series
- As a YouTuber, I want to queue up 10 videos for processing overnight so that they're ready for review in the morning
- As a user, I want to see the progress of all videos in my batch so that I can monitor the overall completion status
- As a user, I want to retry failed videos in a batch so that I don't have to restart the entire batch if one video fails
- As a user, I want to export all processed videos at once so that I can download them as a single ZIP file
- As a team member, I want to cancel a batch job if I uploaded the wrong files so that I can save processing time and costs
- As a user, I want to pause and resume batch processing so that I can manage my processing quota

## Specific Requirements

### Batch Job Model & Database
- Create BatchJob model with user_id (foreign key), name (string, max 100 chars), description (optional text)
- Job configuration: settings (JSONB storing shared processing settings)
- Settings include: transcribe (boolean), remove_silence (boolean), detect_highlights (boolean), silence_threshold (float), highlight_sensitivity (string), export_format (string), export_quality (string)
- Status tracking: status enum ('pending', 'processing', 'paused', 'completed', 'failed', 'cancelled')
- Progress metrics: total_videos (integer), completed_videos (integer), failed_videos (integer), cancelled_videos (integer)
- Statistics: total_duration_seconds (float), processed_duration_seconds (float), estimated_time_remaining (integer in seconds)
- Timing: created_at, started_at (nullable), completed_at (nullable), updated_at
- Constraints: priority (integer, 0-10, default 5 for normal users, higher for premium)
- Create database migration with indexes on user_id, status, created_at DESC, priority DESC

### Batch Video Model & Database
- Create BatchVideo model with batch_job_id (foreign key), video_id (foreign key), position (integer, order in batch)
- Status: status enum ('pending', 'uploading', 'processing', 'completed', 'failed', 'cancelled')
- Progress: progress_percentage (integer 0-100), current_stage (string: 'uploading', 'transcribing', 'removing_silence', 'detecting_highlights', 'exporting')
- Error tracking: error_message (text, nullable), retry_count (integer, default 0), max_retries (integer, default 3)
- Results: processing_result (JSONB, stores output details), output_video_url (string, nullable)
- Timestamps: created_at, started_at (nullable), completed_at (nullable), updated_at
- Create database migration with indexes on batch_job_id, status, position, video_id
- Unique constraint on (batch_job_id, video_id) to prevent duplicate videos in same batch

### Batch Upload Service
- Multi-file upload handler supporting 5-50 videos per batch
- Generate presigned S3 URLs for each video in parallel
- Track individual upload progress for each file
- Validate file formats (MP4, MOV, AVI, WebM) and sizes (max 2GB per file)
- Create Video records for each file
- Create BatchJob and BatchVideo records
- Calculate total batch size and duration estimates
- Support resumable uploads using multipart upload for large files
- Handle upload failures with automatic retry (3 attempts)
- Emit upload progress events for real-time UI updates
- Enforce user quota limits (free: 3 videos, creator: 20 videos, pro: 50 videos per batch)

### Batch Processing Service
- Orchestrate processing of all videos in a batch with shared settings
- Process videos sequentially to manage resource usage (configurable concurrency: 1-5 depending on tier)
- Apply consistent settings from BatchJob to each video:
  - Transcription settings (language, model)
  - Silence removal settings (threshold, min duration)
  - Highlight detection settings (sensitivity, keywords)
  - Export settings (format, quality, resolution)
- Track progress for each video and overall batch
- Update BatchVideo.status and BatchVideo.progress_percentage in real-time
- Update BatchJob.completed_videos, BatchJob.failed_videos counters
- Calculate and update estimated_time_remaining based on average processing time
- Handle individual video failures without stopping entire batch
- Support pause/resume functionality (store state in Redis)
- Support cancellation (clean up partial results, release resources)
- Retry failed videos automatically (up to max_retries)
- Mark batch as 'completed' when all videos are done (including failed ones)
- Store processing results in BatchVideo.processing_result
- Generate batch summary report with statistics

### Batch Queue Management Service
- ARQ task: process_batch_job(batch_job_id: str, concurrency: int = 1)
- Enqueue batch jobs with priority based on user tier
- Manage processing queue with fair scheduling (round-robin across users)
- Track active batch jobs in Redis (prevent exceeding concurrency limits)
- Support pause operation: set status to 'paused', stop processing new videos
- Support resume operation: set status to 'processing', continue from last completed video
- Support cancel operation: set status to 'cancelled', stop all processing, clean up
- Retry mechanism for failed videos with exponential backoff
- Job timeout: 6 hours for large batches (configurable)
- Store job state in Redis for quick recovery after worker restart
- Emit real-time progress events via WebSocket or SSE
- Handle worker failures gracefully (job continues on another worker)

### Batch Export Service
- Generate export package for all completed videos in batch
- Export formats: individual files (ZIP), merged video, or playlist
- For ZIP export:
  - Collect all output_video_url from BatchVideo records
  - Download videos from S3 in parallel (5 concurrent downloads)
  - Create ZIP archive with numbered filenames (001_video_name.mp4, etc.)
  - Upload ZIP to S3 with expiring presigned URL (24 hours)
  - Track ZIP creation progress
- For merged video export:
  - Concatenate videos in position order using FFmpeg
  - Apply consistent encoding settings
  - Upload merged video to S3
- For playlist export:
  - Generate M3U8 playlist file with all video URLs
  - Include metadata (titles, durations)
- Cache export results for 24 hours (avoid regenerating)
- Clean up temporary files after export
- Support export customization: include/exclude failed videos, custom naming

### Batch Processing API Endpoints
- POST /api/batch-jobs: Create new batch job
  - Body: {name, description, settings: {transcribe, remove_silence, detect_highlights, ...}, video_count}
  - Returns batch_job_id and upload_urls for each video
  - Validates settings and user quota
- POST /api/batch-jobs/{id}/videos: Add videos to existing batch (before starting)
  - Body: {video_ids: string[]}
  - Updates total_videos count
  - Returns updated BatchJob
- POST /api/batch-jobs/{id}/start: Start processing batch
  - Enqueues ARQ job, returns job_id
  - Prevents starting if already processing
  - Validates all videos are uploaded
- GET /api/batch-jobs: List all batch jobs for user
  - Query params: status, limit, offset, sort (created_at, priority)
  - Returns paginated list with summary stats
  - Include progress_percentage for each batch
- GET /api/batch-jobs/{id}: Get batch job details
  - Returns full BatchJob object with settings
  - Include all BatchVideo records with status and progress
  - Include real-time progress updates
- POST /api/batch-jobs/{id}/pause: Pause batch processing
  - Sets status to 'paused'
  - Returns updated BatchJob
- POST /api/batch-jobs/{id}/resume: Resume batch processing
  - Sets status to 'processing', re-enqueues job
  - Returns updated BatchJob
- POST /api/batch-jobs/{id}/cancel: Cancel batch processing
  - Sets status to 'cancelled', stops all processing
  - Returns updated BatchJob
- POST /api/batch-jobs/{id}/retry-failed: Retry all failed videos
  - Resets failed videos to 'pending', increments retry_count
  - Re-enqueues processing
  - Returns updated BatchJob
- DELETE /api/batch-jobs/{id}: Delete batch job
  - Soft delete (mark as deleted) or hard delete based on settings
  - Clean up associated videos and S3 files
  - Requires batch to be completed or cancelled
- GET /api/batch-jobs/{id}/progress: Get real-time progress (SSE endpoint)
  - Returns stream of progress events
  - Events: {type: 'progress', batch_id, video_id, progress, current_stage}
- POST /api/batch-jobs/{id}/export: Generate batch export
  - Body: {format: 'zip' | 'merged' | 'playlist', include_failed: false}
  - Enqueues export job, returns export_job_id
  - Returns presigned download URL when ready
- GET /api/batch-jobs/{id}/export/{export_id}: Get export status and download URL
  - Returns {status, progress, download_url, expires_at}

### BatchUploadModal Component
- Client component for multi-file upload interface
- Props: onComplete (function), defaultSettings (BatchSettings, optional)
- File selection: Drag-and-drop zone supporting multiple files
- File list: Display all selected files with size, duration estimate, remove button
- Settings panel:
  - Batch name input (required)
  - Description textarea (optional)
  - Processing settings checkboxes: Transcribe, Remove Silence, Detect Highlights
  - Advanced settings collapse:
    - Silence threshold slider (-60dB to -20dB)
    - Highlight sensitivity radio (low, medium, high)
    - Export format select (MP4, MOV, WebM)
    - Export quality select (720p, 1080p, 4K)
- Validation: Check file formats, total size, user quota limits
- Upload button: Triggers batch creation and multi-file upload
- Progress tracking:
  - Individual file upload progress bars
  - Overall upload progress (percentage)
  - Upload speed and estimated time remaining
- Error handling: Display errors per file, allow retry individual files
- Success state: Show batch created confirmation with "Start Processing" button
- Shadcn components: Dialog, Button, Input, Textarea, Checkbox, RadioGroup, Select, Progress, ScrollArea
- Create file: `frontend/src/components/batch/BatchUploadModal.tsx`

### BatchJobsList Component
- Client component displaying all batch jobs for user
- Props: userId (string, optional for filtering), onJobClick (function, optional)
- Fetch batch jobs on mount using getBatchJobs
- Display as table or card grid with sorting and filtering
- Table columns:
  - Name and description
  - Status badge (color-coded: pending, processing, paused, completed, failed, cancelled)
  - Progress bar (completed_videos / total_videos)
  - Progress percentage (0-100%)
  - Created date
  - Actions dropdown
- Each row/card shows:
  - Batch name (clickable to view details)
  - Status badge with icon
  - Progress: "15/20 videos (75%)" with progress bar
  - Settings summary: "Transcribe, Remove Silence, 1080p"
  - Created: "2 hours ago"
  - Actions: View Details, Pause/Resume, Cancel, Retry Failed, Export, Delete
- Sorting: By created date, status, progress, name
- Filtering: By status (all, pending, processing, completed, failed)
- Empty state: "No batch jobs yet" with "Create Batch" button
- Loading state: Skeleton loaders for rows
- Auto-refresh: Poll for updates every 5 seconds if any batch is processing
- Pagination: 20 items per page
- Shadcn components: Table, Badge, Progress, Button, DropdownMenu, Skeleton, Select
- Create file: `frontend/src/components/batch/BatchJobsList.tsx`

### BatchJobDetails Component
- Client component showing detailed batch job information
- Props: batchJobId (string)
- Fetch batch job details on mount using getBatchJob
- Layout: Two sections (header and videos list)
- Header section:
  - Batch name and description
  - Overall status badge
  - Overall progress: Large progress bar with percentage
  - Statistics cards:
    - Total videos
    - Completed videos (green)
    - Failed videos (red)
    - Pending videos (gray)
  - Time info: Created, Started, Estimated completion
  - Action buttons: Pause/Resume, Cancel, Retry Failed, Export, Delete
- Settings display (expandable):
  - All applied settings shown as read-only
  - Processing options: Transcribe, Remove Silence, Detect Highlights
  - Export options: Format, Quality
- Videos list section:
  - Table or card grid of all BatchVideo records
  - Columns: Position, Video name, Status, Progress, Current stage, Duration, Actions
  - Status colors: pending (gray), uploading (blue), processing (yellow), completed (green), failed (red)
  - Progress bar for each video
  - Current stage label (e.g., "Transcribing...", "Removing silence...")
  - Actions per video: View Video, Retry (if failed), Remove (if pending), View Error (if failed)
- Real-time updates: Subscribe to SSE endpoint for progress updates
- Error display: Show error messages for failed videos with retry button
- Batch actions: Select multiple videos, bulk retry, bulk remove
- Export section (when batch completed):
  - Export format selector
  - "Export All" button
  - Download link (when ready)
  - Export history (previous exports)
- Shadcn components: Card, Badge, Progress, Button, Table, Separator, Collapsible, Dialog
- Create file: `frontend/src/components/batch/BatchJobDetails.tsx`

### BatchProgressPanel Component
- Client component for real-time batch processing progress
- Props: batchJobId (string), compact (boolean, default false)
- Subscribe to SSE endpoint for live updates
- Display modes:
  - Compact: Mini progress bar with percentage (for dashboard widget)
  - Full: Detailed progress with all videos
- Compact mode shows:
  - Batch name
  - Overall progress bar
  - "X of Y videos completed" text
  - Estimated time remaining
  - Expand button to show details
- Full mode shows:
  - Overall progress section (same as compact)
  - Current video being processed:
    - Video name
    - Current stage label
    - Progress bar for current stage
  - Recent activity log:
    - "Video 1: Transcription completed"
    - "Video 2: Silence removal in progress"
    - Timestamps for each event
  - Videos queue preview:
    - List of upcoming videos (next 5)
    - List of completed videos (last 5)
- Live updates: Real-time progress bar animation
- Notifications: Show toast when videos complete or fail
- Pause/Resume button integrated in panel
- Shadcn components: Card, Progress, Button, Badge, ScrollArea, Separator
- Create file: `frontend/src/components/batch/BatchProgressPanel.tsx`

### BatchSettingsForm Component
- Reusable client component for batch processing settings
- Props: initialSettings (BatchSettings, optional), onChange (function)
- Form sections:
  - Transcription settings:
    - Enable transcription checkbox
    - Language select (if enabled)
  - Silence removal settings:
    - Enable silence removal checkbox
    - Threshold slider (-60dB to -20dB)
    - Minimum duration input (0.5s to 5s)
  - Highlight detection settings:
    - Enable highlight detection checkbox
    - Sensitivity radio (low, medium, high, max)
    - Custom keywords input (comma-separated)
  - Export settings:
    - Format select (MP4, MOV, WebM)
    - Quality select (720p, 1080p, 4K)
    - Resolution select (based on quality)
- Real-time validation: Show warnings for invalid settings
- Settings preview: Display summary of selected settings
- Save as template: Allow users to save settings for future batches
- Load template: Select from saved templates
- Reset to defaults button
- Controlled form: onChange fired on every change
- Shadcn components: Form, Checkbox, Select, Slider, Input, RadioGroup, Button, Label, Separator
- Create file: `frontend/src/components/batch/BatchSettingsForm.tsx`

### BatchVideoRow Component
- Client component displaying individual video in batch
- Props: batchVideo (BatchVideo), onAction (function)
- Display format: Table row or card
- Shows:
  - Position number (e.g., "#1", "#2")
  - Video thumbnail (if available)
  - Video name and duration
  - Status badge (pending, uploading, processing, completed, failed, cancelled)
  - Progress bar (0-100%)
  - Current stage label (e.g., "Transcribing 45%")
  - Error icon (if failed, with tooltip showing error message)
  - Actions dropdown: View Video, Retry, Remove, Download (if completed)
- Status colors:
  - Pending: gray
  - Uploading: blue with upload icon
  - Processing: yellow with spinner
  - Completed: green with checkmark
  - Failed: red with error icon
  - Cancelled: gray with X icon
- Progress visualization:
  - Progress bar with percentage
  - Stage indicator (icons for transcribe, silence, highlights, export)
  - Animated spinner for current stage
- Error state:
  - Red border for failed videos
  - Error message tooltip
  - Retry button prominent
  - Show retry count (e.g., "Retry 2/3")
- Completed state:
  - Green border
  - Download button
  - "View Video" link
  - Processing time shown
- Interactive actions:
  - Click row to expand details
  - Hover to show quick actions
  - Drag to reorder (if batch not started)
- Shadcn components: Badge, Progress, Button, DropdownMenu, Tooltip, AlertDialog
- Create file: `frontend/src/components/batch/BatchVideoRow.tsx`

### BatchExportDialog Component
- Client component for configuring and downloading batch export
- Props: batchJobId (string), onClose (function)
- Export configuration:
  - Format radio group:
    - Individual files (ZIP) - default
    - Merged video (single file)
    - Playlist (M3U8)
  - Options checkboxes:
    - Include failed videos
    - Use original filenames
    - Add batch name prefix
  - Custom naming pattern input (for ZIP)
- Export preview:
  - Estimated file size
  - Number of videos to be included
  - Export format details
- Export button: Triggers export job
- Progress section (shown during export):
  - Progress bar with percentage
  - Current operation (e.g., "Downloading video 5/20")
  - Estimated time remaining
  - Cancel button
- Download section (shown when ready):
  - Download URL with expiration timer
  - "Download ZIP" button (or appropriate format)
  - File size displayed
  - Option to generate new export with different settings
- Error handling: Display export errors with retry option
- Export history:
  - List of previous exports
  - Each shows: Format, created date, size, download button (if not expired)
- Shadcn components: Dialog, RadioGroup, Checkbox, Button, Progress, Alert, Separator, Badge
- Create file: `frontend/src/components/batch/BatchExportDialog.tsx`

### Frontend API Client Functions
- createBatchJob(data): Creates batch job, returns Promise<{batch_job: BatchJob, upload_urls: string[]}>
  - Data: {name, description, settings, video_count}
- addVideosToBatch(batchJobId, videoIds): Adds videos to batch, returns Promise<BatchJob>
- startBatchProcessing(batchJobId): Starts processing, returns Promise<{job_id: string}>
- getBatchJobs(params): Fetches batch jobs, returns Promise<{batch_jobs: BatchJob[], total: number}>
  - Params: {status, limit, offset, sort}
- getBatchJob(batchJobId): Fetches batch job details, returns Promise<BatchJob>
- pauseBatchJob(batchJobId): Pauses batch, returns Promise<BatchJob>
- resumeBatchJob(batchJobId): Resumes batch, returns Promise<BatchJob>
- cancelBatchJob(batchJobId): Cancels batch, returns Promise<BatchJob>
- retryFailedVideos(batchJobId): Retries failed videos, returns Promise<BatchJob>
- deleteBatchJob(batchJobId): Deletes batch, returns Promise<void>
- subscribeToBatchProgress(batchJobId, callback): Subscribe to SSE progress, returns unsubscribe function
- exportBatch(batchJobId, config): Generates export, returns Promise<{export_job_id: string}>
  - Config: {format, include_failed}
- getExportStatus(batchJobId, exportId): Gets export status, returns Promise<BatchExport>
- uploadBatchVideos(batchJobId, files, onProgress): Uploads multiple files, returns Promise<{uploaded_videos: Video[]}>
  - onProgress: callback (fileIndex, progress) for tracking individual uploads
- All functions use apiClient with proper error handling and TypeScript types

### TypeScript Type Definitions
- BatchJob interface: id, user_id, name, description, settings, status, total_videos, completed_videos, failed_videos, cancelled_videos, total_duration_seconds, processed_duration_seconds, estimated_time_remaining, priority, created_at, started_at, completed_at, updated_at
- BatchVideo interface: id, batch_job_id, video_id, position, status, progress_percentage, current_stage, error_message, retry_count, max_retries, processing_result, output_video_url, created_at, started_at, completed_at, updated_at
- BatchSettings interface: transcribe, remove_silence, detect_highlights, silence_threshold, highlight_sensitivity, export_format, export_quality, language, keywords
- BatchJobStatus type: 'pending' | 'processing' | 'paused' | 'completed' | 'failed' | 'cancelled'
- BatchVideoStatus type: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed' | 'cancelled'
- ProcessingStage type: 'uploading' | 'transcribing' | 'removing_silence' | 'detecting_highlights' | 'exporting'
- BatchExport interface: id, batch_job_id, format, status, progress, download_url, file_size, expires_at, created_at
- BatchExportFormat type: 'zip' | 'merged' | 'playlist'
- BatchProgress interface: batch_job_id, progress_percentage, current_video_id, current_video_name, current_stage, completed_count, failed_count, pending_count, estimated_time_remaining
- UploadProgress interface: file_index, file_name, progress, status, error

### Testing Requirements
- Backend unit tests: Test batch job creation, video addition, settings validation
- Backend integration tests: Test API endpoints with multiple videos, concurrent batches
- Worker tests: Test batch processing task, pause/resume, cancellation, retry logic
- Service tests: Test batch upload service, queue management, export generation
- Frontend component tests: Test BatchUploadModal, BatchJobsList, BatchJobDetails, BatchProgressPanel
- E2E tests: Full batch workflow (upload multiple videos, apply settings, monitor progress, export)
- Concurrency tests: Test multiple users running batches simultaneously
- Failure recovery tests: Test handling of video failures, worker crashes, network issues
- Performance tests: Test batch processing speed with 5, 10, 20, 50 videos
- Export tests: Test ZIP creation, merged video, playlist generation with various sizes

### Performance Considerations
- Upload optimization: Use parallel uploads with concurrency limit (5 concurrent)
- Presigned URL generation: Batch generate all URLs in single request
- Processing queue: Limit concurrent video processing (1-5 based on user tier)
- Progress tracking: Use Redis for fast progress updates, minimize database writes
- SSE connections: Implement connection pooling, automatic reconnection
- Export caching: Cache export results for 24 hours to avoid regeneration
- Database optimization: Use indexes on batch_job_id, status, created_at
- Bulk operations: Use batch database operations for creating BatchVideo records
- Memory management: Stream video files during export, don't load all in memory
- Cleanup jobs: Background task to delete old batch jobs and exports after 30 days

### Security Considerations
- Validation: Validate batch size limits based on user tier
- Rate limiting: Limit batch job creation (5 per hour for free, 20 for paid)
- Quota enforcement: Check user's remaining processing quota before starting batch
- File validation: Validate all uploaded files (format, size, content type)
- Authorization: Ensure users can only access their own batch jobs
- Presigned URLs: Use short expiration times (15 minutes for upload, 24 hours for download)
- Input sanitization: Sanitize batch names, descriptions to prevent XSS
- Cancellation: Ensure cancelled batches don't consume resources
- Resource limits: Set maximum batch size (50 videos for pro tier)
- Clean up: Delete uploaded files if batch is cancelled before processing

### Quality Considerations
- Progress accuracy: Ensure progress percentages are accurate and update in real-time
- Error messages: Provide clear, actionable error messages for each failure type
- Retry logic: Implement exponential backoff for retries to avoid overwhelming system
- State consistency: Ensure batch and video statuses are always in sync
- Pause/resume: Maintain exact state when pausing and resuming batches
- Export reliability: Verify all videos are included in exports, handle missing files gracefully
- User notifications: Send email notifications when large batches complete or fail
- Logging: Comprehensive logging for debugging batch processing issues
- Monitoring: Track batch job success rates, average processing times, failure rates

### Integration Points
- Dashboard: Show "Batch Jobs" section with active batches and quick stats
- Video Upload: "Upload Multiple Videos" option that opens BatchUploadModal
- Video List: Indicate which videos are part of batches with batch icon/badge
- Video Editor: Link to batch details from individual video editor
- Notifications: Show batch completion notifications in notification center
- Settings: Batch processing preferences (default settings, concurrency)
- Billing: Track batch processing usage for quota limits and billing
- Analytics: Dashboard showing batch job statistics, success rates, popular settings

## Success Criteria
- Batch upload of 20 videos completes in <5 minutes (upload only)
- Batch processing of 20 30-minute videos completes in <10 hours (sequential) or <2 hours (5 concurrent)
- Batch export (ZIP) of 20 videos generates in <10 minutes
- Real-time progress updates with <1 second latency
- Pause/resume functionality works without data loss or state corruption
- Failed video retry succeeds >80% of the time
- Users can manage 5+ concurrent batch jobs without performance degradation
- UI remains responsive during large batch operations
- Export downloads complete successfully >95% of the time
- Test coverage >85% for batch processing code
- User feedback: "Batch processing saves me 2+ hours per week"
