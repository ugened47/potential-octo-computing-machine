# Spec Requirements: Phase 1 Completion

## Initial Description

Complete all remaining Phase 1 Foundation features to finish the MVP foundation stage. This includes:

1. **Video Upload to S3** - Complete implementation
   - Video model exists but no upload API endpoints
   - No S3 presigned URL generation
   - No upload frontend components

2. **Database Schema for Videos/Clips** - Complete implementation
   - Video model exists (backend/app/models/video.py)
   - No video API routes (backend/app/api/routes/video.py missing)

3. **Basic UI (Dashboard, Upload)** - Complete implementation
   - Dashboard page exists but is just a placeholder
   - No upload page/component

## Requirements Discussion

### First Round Questions

**Q1:** Spec Integration - Should this Phase 1 Completion spec coordinate with existing `2025-11-07-video-upload` and `2025-11-07-dashboard` specs, or create a comprehensive implementation plan?
**Answer:** Create a unified implementation plan that ensures all Phase 1 items are completed, referencing the existing specs where appropriate.

**Q2:** S3 Configuration - Should we create a dedicated S3 service module or integrate it into the video service?
**Answer:** Use MinIO instead of mocking for local development, so the project is more prepared for production on AWS. Create a dedicated S3 service module (`backend/app/services/s3.py`) that works with both MinIO (local) and AWS S3 (production) using boto3's S3-compatible API.

**Q3:** Upload Flow - Should metadata extraction happen synchronously or be deferred to a background job?
**Answer:** Choose the best and effective approach with upload/processing indicator. Defer metadata extraction to a background job for better UX, with real-time progress indicators.

**Q4:** Dashboard Integration - Should upload be accessible from both a dedicated `/upload` page AND the dashboard?
**Answer:** Use the best approach - both dedicated `/upload` page for focused uploads and dashboard button for quick access.

**Q5:** Video API Routes - Should we include PATCH /api/videos/{id} for updating title/description?
**Answer:** Use the best approach - include basic PATCH for title/description updates to provide essential video management capabilities.

**Q6:** Error Handling - Should we provide retry functionality for failed uploads?
**Answer:** Use the best approach - show error with a retry button that restarts the upload flow, providing good UX for network failures.

**Q7:** Video Metadata - Should we show "processing" status immediately or wait until metadata is extracted?
**Answer:** Use the best approach - show "processing" status immediately with progress indicator, then update to "uploaded" once metadata is extracted. This provides immediate feedback and transparency.

**Q8:** Scope Boundaries - Should we implement everything from existing specs or defer some features?
**Answer:** Use the best approaches - implement core functionality from both specs, but defer advanced features like batch upload, video thumbnails, and advanced filtering to later phases.

### Existing Code to Reference

**Similar Features Identified:**
- **Video Model**: `backend/app/models/video.py` - Video model already exists with required fields
- **Transcript Components**: `frontend/src/components/transcript/` - Can reference TranscriptPanel, TranscriptionProgress for upload progress patterns
- **Auth API Pattern**: `backend/app/api/routes/auth.py` - Follow FastAPI router pattern for video routes
- **Auth State Management**: `frontend/src/store/auth-store.ts` - Can reference Zustand patterns for video state if needed
- **API Client Pattern**: `frontend/src/lib/api.ts` - Follow existing apiClient pattern for video API functions
- **Protected Routes**: `frontend/src/components/auth/ProtectedRoute.tsx` - Use for protecting upload and dashboard pages
- **Form Validation**: `frontend/src/lib/validation.ts` - Can reference validation patterns for file validation
- **Dashboard Placeholder**: `frontend/src/app/dashboard/page.tsx` - Already exists, needs implementation

**Components to potentially reuse:**
- Progress component from `frontend/src/components/ui/progress.tsx` for upload progress
- Button, Card, Input components from Shadcn/ui
- Error handling patterns from transcript components
- Loading state patterns from TranscriptionProgress component

**Backend logic to reference:**
- Settings class from `backend/app/core/config.py` for S3/MinIO configuration
- ARQ worker patterns from `backend/app/worker.py` for background metadata extraction
- Database patterns from User model for Video model relationships

### Follow-up Questions

None needed - all requirements clarified.

## Visual Assets

### Files Provided:
No visual files found in the visuals folder.

### Visual Insights:
No visual assets provided. Will follow Shadcn/ui design system and existing project styling patterns from transcript components and authentication pages.

## Requirements Summary

### Functional Requirements

**Backend Implementation:**

1. **S3/MinIO Storage Service**
   - Create `backend/app/services/s3.py` with S3-compatible service
   - Support both MinIO (local dev) and AWS S3 (production) using boto3
   - Generate presigned URLs with 15-minute expiration
   - Store videos in path structure: `videos/{user_id}/{video_id}/{filename}`
   - Use UUID for filenames to avoid collisions
   - Configure CORS for direct browser uploads
   - Generate CloudFront URLs for video delivery (production)

2. **Video API Routes**
   - POST /api/upload/presigned-url: Generate presigned URL, validate file, return URL + video_id
   - POST /api/videos: Create video record after upload completes
   - GET /api/videos: List user's videos with pagination, filtering, sorting
   - GET /api/videos/{id}: Get video details including metadata and status
   - PATCH /api/videos/{id}: Update video title and description
   - DELETE /api/videos/{id}: Delete video record and S3 file

3. **Video Validation Service**
   - Validate file extension against allowed formats (MP4, MOV, AVI, WebM, MKV)
   - Check file size against max_upload_size_mb (2GB default)
   - Verify MIME type matches video format
   - Return clear error messages for validation failures

4. **Background Metadata Extraction**
   - ARQ background job to extract video metadata (duration, resolution, format)
   - Update video status: "uploaded" → "processing" → "completed"
   - Handle extraction failures with "failed" status
   - Progress tracking in Redis for real-time updates

5. **Database Migrations**
   - Ensure Video model migration exists with proper indexes
   - Index on user_id and created_at for efficient queries
   - Foreign key relationship to users table

**Frontend Implementation:**

1. **Upload Page (`/upload`)**
   - Dedicated upload page with drag-and-drop zone
   - File picker fallback button
   - Client-side validation before upload
   - Display file name, size, format before upload
   - Optional title and description input fields
   - Upload progress with percentage, speed, ETA
   - Upload status indicators: preparing, uploading, processing, complete
   - Error handling with retry button
   - Cancel/abort upload functionality

2. **Dashboard Page (`/dashboard`)**
   - Stats cards: Total Videos, Storage Used, Processing Time, Recent Activity
   - Video grid/list view toggle
   - Search bar for finding videos by title
   - Prominent upload button linking to `/upload`
   - Processing queue section with auto-refresh (every 5 seconds)
   - Filter by status: All, Uploaded, Processing, Completed, Failed
   - Sort by: Date, Name, Duration
   - Empty states for no videos, no processing, no search results

3. **Video List/Grid Components**
   - Grid view: Card layout with video thumbnails (placeholder)
   - List view: Table layout with sortable columns
   - Video cards showing: title, duration, file size, upload date, status badge
   - Action buttons: View, Edit, Delete with confirmation
   - Click card to navigate to video detail page

4. **Upload Progress Component**
   - Real-time progress bar (0-100%)
   - Upload speed and estimated time remaining
   - Status text: preparing, uploading, processing, complete
   - Error display with retry button
   - Cancel button during upload

5. **Video API Client Functions**
   - getPresignedUrl(fileMetadata): Request presigned URL
   - uploadToS3(presignedUrl, file): Upload file directly to S3
   - createVideoRecord(videoData): Create video record after upload
   - getVideos(filters, pagination): List videos with filters
   - getVideo(videoId): Get video details
   - updateVideo(videoId, data): Update video title/description
   - deleteVideo(videoId): Delete video with confirmation

### Reusability Opportunities

- **UI Components:** Reuse Progress, Button, Card, Input, Badge from Shadcn/ui
- **API Client:** Extend existing `apiClient` from `frontend/src/lib/api.ts`
- **Error Patterns:** Follow error handling from `TranscriptPanel` component
- **Loading Patterns:** Follow loading states from `TranscriptionProgress` component
- **State Management:** Use Zustand for video list state if needed
- **Protected Routes:** Use `ProtectedRoute` component for upload and dashboard pages
- **Form Validation:** Reference validation patterns from auth forms
- **Backend Patterns:** Follow FastAPI router pattern from auth routes
- **Service Layer:** Follow service pattern from `TranscriptionService`
- **ARQ Jobs:** Follow background job pattern from transcription worker

### Scope Boundaries

**In Scope:**
- Video upload with drag-and-drop and file picker
- Direct S3/MinIO upload via presigned URLs
- Upload progress tracking with speed and ETA
- Video CRUD operations (Create, Read, Update, Delete)
- Dashboard with stats, video list, and processing queue
- Video metadata extraction via background job
- Basic filtering and sorting (status, date, name, duration)
- Search by video title
- Error handling with retry functionality
- MinIO for local development (S3-compatible)
- Video status tracking (uploaded, processing, completed, failed)

**Out of Scope:**
- Video thumbnail generation (defer to later feature)
- Video transcoding/encoding (separate processing pipeline)
- Batch upload of multiple videos (post-MVP feature)
- Video preview before upload completes
- Upload resumption after network failure (cancel and retry only)
- Video editing capabilities (separate feature)
- Video sharing/permissions (post-MVP feature)
- Upload from URL or cloud storage (future enhancement)
- Advanced filtering (date range picker, file size range)
- Video thumbnails (placeholder images initially)
- Bulk operations (select multiple videos)
- Video analytics or view statistics

### Technical Considerations

**MinIO Configuration:**
- Add MinIO service to docker-compose.yml for local development
- Configure MinIO with S3-compatible API endpoint
- Use environment variables to switch between MinIO (local) and AWS S3 (production)
- MinIO access key and secret key for local development
- MinIO endpoint URL: `http://minio:9000` (internal) or `http://localhost:9000` (external)
- Same boto3 client works with both MinIO and AWS S3

**S3 Service Implementation:**
- Create `backend/app/services/s3.py` with S3Service class
- Use boto3 S3 client with endpoint_url parameter for MinIO
- Detect environment (development vs production) to choose endpoint
- Generate presigned URLs with PUT method for uploads
- Configure CORS on MinIO/S3 bucket for direct browser uploads
- Path structure: `videos/{user_id}/{video_id}/{filename}.{ext}`

**Upload Flow:**
1. Frontend: User selects/drops file
2. Frontend: Client-side validation (size, format)
3. Frontend: Request presigned URL from backend with file metadata
4. Backend: Validate file metadata, generate presigned URL, create video record with "uploaded" status
5. Frontend: Upload file directly to S3/MinIO using presigned URL with progress tracking
6. Frontend: After upload completes, call backend to confirm upload
7. Backend: Update video status to "processing" and enqueue metadata extraction job
8. Worker: Extract metadata (duration, resolution, format) asynchronously
9. Worker: Update video record with metadata and set status to "completed"
10. Frontend: Poll or use SSE to update UI with processing status

**Progress Tracking:**
- Upload progress: Track via XMLHttpRequest/Fetch upload progress events
- Processing progress: Track via Redis keys updated by background job
- Display both upload and processing progress with clear status indicators
- Use Server-Sent Events (SSE) or polling for real-time processing updates

**Error Handling:**
- File validation errors: Show immediately before upload starts
- Network errors: Show error with retry button
- S3 upload errors: Show error with retry button (restarts from presigned URL request)
- Processing errors: Show error status with retry option
- All errors: Clear, user-friendly error messages

**Database Considerations:**
- Video model already exists, ensure migration is applied
- Add indexes on user_id and created_at for efficient queries
- Foreign key relationship to users table
- Status enum: uploaded, processing, completed, failed

**Frontend State Management:**
- Upload state: Local component state for upload progress
- Video list state: Server Component for initial data, Client Component for interactions
- Filter/sort state: URL query parameters for shareable state
- View preference: LocalStorage for grid/list preference
- Processing queue: Polling state managed in ProcessingQueue component

**Integration Points:**
- Reference existing `2025-11-07-video-upload` spec for detailed upload requirements
- Reference existing `2025-11-07-dashboard` spec for detailed dashboard requirements
- Integrate with existing authentication system (ProtectedRoute)
- Use existing ARQ worker infrastructure for background jobs
- Follow existing API client patterns for consistency

