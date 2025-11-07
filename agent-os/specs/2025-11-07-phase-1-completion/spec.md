# Specification: Phase 1 Completion

## Goal
Complete all remaining Phase 1 Foundation features including video upload to S3/MinIO, video API routes, dashboard implementation, and background metadata extraction to finish the MVP foundation stage.

## User Stories
- As a content creator, I want to upload videos with drag-and-drop so that I can quickly add content to the platform
- As a user, I want to see all my videos in a dashboard so that I can manage my content efficiently
- As a user, I want to see upload and processing progress so that I know when my videos are ready

## Specific Requirements

**S3/MinIO Storage Service**
- Create `backend/app/services/s3.py` with S3Service class using boto3 S3-compatible API
- Support both MinIO (local dev) and AWS S3 (production) via endpoint_url configuration
- Generate presigned URLs with PUT method and 15-minute expiration for direct browser uploads
- Store videos in path structure: `videos/{user_id}/{video_id}/{filename}.{ext}` using UUID filenames
- Configure CORS on MinIO/S3 bucket to allow direct browser uploads from frontend
- Generate CloudFront URLs for video delivery in production environment
- Use environment variables to switch between MinIO endpoint (`http://minio:9000`) and AWS S3

**Video API Routes**
- POST /api/upload/presigned-url: Validate file metadata, generate presigned URL, create video record with "uploaded" status, return URL and video_id
- POST /api/videos: Create video record after upload completes, accept video_id, title, description, S3 key
- GET /api/videos: List user's videos with pagination (limit/offset), filtering by status, sorting by date/name/duration
- GET /api/videos/{id}: Get video details including metadata, processing status, and S3 key
- PATCH /api/videos/{id}: Update video title and description, require user ownership
- DELETE /api/videos/{id}: Delete video record and S3 file, require user ownership, handle cascade deletion

**Video Validation Service**
- Validate file extension against allowed formats from config (MP4, MOV, AVI, WebM, MKV)
- Check file size against max_upload_size_mb setting (2GB default) before generating presigned URL
- Verify MIME type matches video format to prevent malicious file uploads
- Return clear, user-friendly error messages for validation failures
- Reject uploads that exceed size limit or have invalid formats immediately

**Background Metadata Extraction**
- Create ARQ background job `extract_video_metadata` to extract duration, resolution, format using ffprobe/ffmpeg
- Update video status flow: "uploaded" → "processing" → "completed" or "failed"
- Store metadata in Video model fields: duration (seconds), resolution (e.g., "1920x1080"), format
- Handle extraction failures gracefully with "failed" status and error logging
- Use Redis progress tracking similar to transcription progress pattern for real-time updates

**Upload Page (`/upload`)**
- Dedicated upload page with drag-and-drop zone using HTML5 drag-and-drop API
- File picker fallback button for browsers without drag-and-drop support
- Client-side validation before upload (file type, size) with immediate error display
- Display file name, size, format before upload starts
- Optional title and description input fields using Shadcn/ui Input components
- Upload progress component showing percentage, upload speed (MB/s), estimated time remaining
- Upload status indicators: preparing, uploading, processing, complete with visual badges
- Error handling with retry button that restarts upload flow from presigned URL request

**Dashboard Page (`/dashboard`)**
- Stats cards section: Total Videos, Storage Used (GB), Processing Time (minutes), Recent Activity (last 7 days)
- Video grid/list view toggle with preference stored in LocalStorage
- Search bar for finding videos by title with real-time filtering
- Prominent upload button linking to `/upload` page
- Processing queue section showing videos with "processing" status, auto-refresh every 5 seconds
- Filter by status: All, Uploaded, Processing, Completed, Failed with URL query parameters
- Sort by: Date (newest/oldest), Name (A-Z/Z-A), Duration (longest/shortest) with visual indicators
- Empty states for no videos, no processing queue, no search results with helpful messages

**Video List/Grid Components**
- Grid view: Card layout with video thumbnails (placeholder images initially), responsive grid (4 columns desktop, 2 mobile)
- List view: Table layout with sortable columns (thumbnail, title, duration, file size, upload date, status, actions)
- Video cards showing: title (truncated if long), duration, file size, upload date (relative time), status badge
- Action buttons: View (navigate to detail page), Edit (navigate to editor), Delete (with confirmation dialog)
- Click card to navigate to video detail page, hover effects for better UX

**Upload Progress Component**
- Real-time progress bar (0-100%) using Shadcn/ui Progress component
- Display upload speed (MB/s) and estimated time remaining calculated from upload rate
- Status text: preparing, uploading, processing, complete with appropriate icons
- Error display with clear error message and retry button that restarts upload
- Cancel button during upload that aborts XMLHttpRequest and cleans up state

**Video API Client Functions**
- getPresignedUrl(fileMetadata): Request presigned URL from POST /api/upload/presigned-url with file name, size, type
- uploadToS3(presignedUrl, file): Upload file directly to S3 using presigned URL with progress tracking via XMLHttpRequest
- createVideoRecord(videoData): Create video record after upload completes via POST /api/videos
- getVideos(filters, pagination): List videos with filters and pagination via GET /api/videos
- getVideo(videoId): Get video details via GET /api/videos/{id}
- updateVideo(videoId, data): Update video title/description via PATCH /api/videos/{id}
- deleteVideo(videoId): Delete video with confirmation via DELETE /api/videos/{id}

## Visual Design
No visual assets provided. Follow Shadcn/ui design system and existing project styling patterns from transcript components and authentication pages.

## Existing Code to Leverage

**Video Model (`backend/app/models/video.py`)**
- Video model already exists with required fields: id, user_id, title, description, file_size, format, duration, resolution, s3_key, cloudfront_url, status, timestamps
- VideoStatus enum includes: UPLOADED, PROCESSING, COMPLETED, FAILED
- Foreign key relationship to users table with proper indexing
- Reuse this model structure, ensure migration exists and is applied

**Auth API Pattern (`backend/app/api/routes/auth.py`)**
- Follow FastAPI router pattern with APIRouter, dependency injection (get_current_user, get_db)
- Use response models, proper HTTP status codes, error handling with HTTPException
- Apply same pattern for video routes: create `backend/app/api/routes/video.py` following auth.py structure

**TranscriptionProgress Component (`frontend/src/components/transcript/TranscriptionProgress.tsx`)**
- Polling pattern for real-time progress updates (every 2 seconds by default)
- Progress state management with useState, useEffect for polling, error handling
- Reuse polling pattern for upload progress and processing queue status updates
- Follow same error handling and retry button pattern

**API Client Pattern (`frontend/src/lib/api.ts`)**
- Extend existing apiClient with axios interceptors for auth token handling
- Follow same error handling patterns, token refresh logic
- Add video API functions following same structure as existing API functions
- Use same baseURL configuration and request/response interceptors

**ARQ Worker Pattern (`backend/app/worker.py`)**
- Follow transcribe_video worker pattern for background metadata extraction job
- Use Redis progress tracking with update_progress callback pattern
- Create extract_video_metadata worker function following same structure
- Use same error handling, database session management, and progress key naming convention

## Out of Scope
- Video thumbnail generation (defer to later feature, use placeholder images initially)
- Video transcoding/encoding (separate processing pipeline, not part of Phase 1)
- Batch upload of multiple videos simultaneously (post-MVP feature)
- Video preview before upload completes (only show metadata after upload)
- Upload resumption after network failure (cancel and retry only, no partial upload resume)
- Video editing capabilities (separate feature, timeline editor is separate spec)
- Video sharing/permissions system (post-MVP feature)
- Upload from URL or cloud storage import (future enhancement)
- Advanced filtering with date range picker or file size range (basic filtering only)
- Bulk operations like selecting multiple videos for batch actions (single video operations only)

