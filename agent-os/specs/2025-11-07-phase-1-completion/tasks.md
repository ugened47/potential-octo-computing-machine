# Task Breakdown: Phase 1 Completion

## Overview
Total Tasks: 5 task groups, 40+ sub-tasks

## Task List

### Infrastructure & Configuration

#### Task Group 1: MinIO Setup and S3 Service
**Dependencies:** None

- [x] 1.0 Complete infrastructure setup
  - [x] 1.1 Add MinIO service to docker-compose.yml
    - Add MinIO service with S3-compatible API endpoint
    - Configure MinIO access key and secret key for local development
    - Set up MinIO endpoint URL: `http://minio:9000` (internal) or `http://localhost:9000` (external)
    - Configure MinIO bucket with CORS for direct browser uploads
    - Add MinIO environment variables to backend and worker services
  - [x] 1.2 Update backend/app/core/config.py for MinIO support
    - Add MinIO endpoint URL configuration
    - Add MinIO access key and secret key fields
    - Add environment detection (development vs production) to choose endpoint
    - Reuse pattern from: existing AWS S3 configuration in config.py
  - [x] 1.3 Write 2-8 focused tests for S3 service
    - Test presigned URL generation with MinIO endpoint
    - Test presigned URL generation with AWS S3 endpoint
    - Test path structure: `videos/{user_id}/{video_id}/{filename}.{ext}`
    - Test CloudFront URL generation for production
    - Test CORS configuration
  - [x] 1.4 Create S3 storage service (`backend/app/services/s3.py`)
    - Create S3Service class using boto3 S3-compatible API
    - Support both MinIO (local dev) and AWS S3 (production) via endpoint_url configuration
    - Generate presigned URLs with PUT method and 15-minute expiration
    - Store videos in path structure: `videos/{user_id}/{video_id}/{filename}.{ext}` using UUID filenames
    - Generate CloudFront URLs for video delivery in production environment
    - Configure CORS on MinIO/S3 bucket to allow direct browser uploads
    - Use environment variables to switch between MinIO endpoint and AWS S3
    - Reuse pattern from: TranscriptionService for S3 operations
  - [x] 1.5 Ensure infrastructure tests pass
    - Run ONLY the 2-8 tests written in 1.3
    - Verify MinIO service starts correctly
    - Verify S3 service works with both MinIO and AWS S3
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- MinIO service runs in docker-compose
- S3 service generates valid presigned URLs
- Path structure follows specified format
- The 2-8 tests written in 1.3 pass

### Database Layer

#### Task Group 2: Video Model Verification and Migrations
**Dependencies:** Task Group 1

- [x] 2.0 Complete database layer
  - [x] 2.1 Write 2-8 focused tests for Video model functionality
    - Test Video model creation with required fields
    - Test Video model validation (title, user_id foreign key)
    - Test Video model status enum (uploaded, processing, completed, failed)
    - Test Video model relationships with User
    - Test Video model metadata fields (duration, resolution, format)
  - [x] 2.2 Verify Video model exists and is correct
    - Verify Video model in `backend/app/models/video.py` has all required fields
    - Verify VideoStatus enum includes: UPLOADED, PROCESSING, COMPLETED, FAILED
    - Verify foreign key relationship to users table with proper indexing
    - Verify timestamps: created_at, updated_at with indexes
  - [x] 2.3 Verify migration exists and is applied
    - Check if migration for videos table exists in alembic/versions/
    - Ensure migration includes indexes on user_id and created_at
    - Ensure migration includes foreign key relationship to users table
    - Run migration if not already applied
  - [x] 2.4 Ensure database layer tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify migrations run successfully
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- Video model passes validation tests
- Migrations run successfully
- All required fields and relationships exist

### Backend API Layer

#### Task Group 3: Video API Routes and Services
**Dependencies:** Task Group 2

- [x] 3.0 Complete API layer
  - [x] 3.1 Write 2-8 focused tests for API endpoints
    - Test POST /api/upload/presigned-url generates valid URL and creates video record
    - Test POST /api/videos creates video record after upload
    - Test GET /api/videos lists user's videos with pagination, filtering, sorting
    - Test GET /api/videos/{id} returns video details
    - Test PATCH /api/videos/{id} updates video title/description
    - Test DELETE /api/videos/{id} deletes video and S3 file
    - Test authorization (users can only access their own videos)
  - [x] 3.2 Create video validation service
    - Validate file extension against allowed formats from config (MP4, MOV, AVI, WebM, MKV)
    - Check file size against max_upload_size_mb setting (2GB default)
    - Verify MIME type matches video format to prevent malicious file uploads
    - Return clear, user-friendly error messages for validation failures
    - Reject uploads that exceed size limit or have invalid formats immediately
    - Reuse pattern from: config.py for allowed formats and size limits
  - [x] 3.3 Create video API routes (`backend/app/api/routes/video.py`)
    - POST /api/upload/presigned-url: Validate file metadata, generate presigned URL, create video record with "uploaded" status, return URL and video_id
    - POST /api/videos: Create video record after upload completes, accept video_id, title, description, S3 key
    - GET /api/videos: List user's videos with pagination (limit/offset), filtering by status, sorting by date/name/duration
    - GET /api/videos/{id}: Get video details including metadata, processing status, and S3 key
    - PATCH /api/videos/{id}: Update video title and description, require user ownership
    - DELETE /api/videos/{id}: Delete video record and S3 file, require user ownership, handle cascade deletion
    - Follow pattern from: `backend/app/api/routes/auth.py` for router structure
  - [x] 3.4 Create video schemas (`backend/app/schemas/video.py`)
    - VideoCreate schema for POST /api/videos
    - VideoUpdate schema for PATCH /api/videos/{id}
    - VideoRead schema for GET responses
    - PresignedUrlRequest schema for upload endpoint
    - PresignedUrlResponse schema with URL and video_id
    - Follow pattern from: `backend/app/schemas/auth.py` for schema structure
  - [x] 3.5 Register video routes in main app
    - Add video router to `backend/app/api/routes/__init__.py`
    - Include router in `backend/app/main.py` with prefix `/api/videos`
    - Include upload router with prefix `/api/upload`
  - [x] 3.6 Implement authentication/authorization
    - Use existing auth pattern (get_current_user dependency)
    - Add permission checks (users can only access their own videos)
    - Verify ownership before PATCH and DELETE operations
  - [x] 3.7 Ensure API layer tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify critical CRUD operations work
    - Verify authorization is enforced
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 3.1 pass
- All CRUD operations work
- Proper authorization enforced
- Presigned URLs work correctly
- File validation works

### Background Jobs

#### Task Group 4: Metadata Extraction Worker
**Dependencies:** Task Group 3

- [x] 4.0 Complete background job layer
  - [x] 4.1 Write 2-8 focused tests for metadata extraction
    - Test extract_video_metadata job extracts duration, resolution, format
    - Test video status updates: "uploaded" → "processing" → "completed"
    - Test error handling sets status to "failed"
    - Test Redis progress tracking updates correctly
  - [x] 4.2 Create metadata extraction ARQ job (`backend/app/worker.py`)
    - Create extract_video_metadata worker function following transcribe_video pattern
    - Extract duration, resolution, format using ffprobe/ffmpeg
    - Update video status flow: "uploaded" → "processing" → "completed" or "failed"
    - Store metadata in Video model fields: duration (seconds), resolution (e.g., "1920x1080"), format
    - Handle extraction failures gracefully with "failed" status and error logging
    - Use Redis progress tracking similar to transcription progress pattern for real-time updates
    - Reuse pattern from: transcribe_video function in `backend/app/worker.py`
  - [x] 4.3 Update video routes to enqueue metadata job
    - After POST /api/videos confirms upload, update status to "processing"
    - Enqueue extract_video_metadata job with video_id
    - Handle job enqueue errors gracefully
  - [x] 4.4 Ensure background job tests pass
    - Run ONLY the 2-8 tests written in 4.1
    - Verify metadata extraction works
    - Verify status updates correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 4.1 pass
- Metadata extraction works correctly
- Status updates flow correctly
- Redis progress tracking works

### Frontend Components

#### Task Group 5: Upload and Dashboard UI
**Dependencies:** Task Group 3

- [ ] 5.0 Complete UI components
  - [ ] 5.1 Write 2-8 focused tests for UI components
    - Test upload component file selection and drag-and-drop
    - Test upload progress tracking
    - Test dashboard video list rendering
    - Test video grid/list view toggle
    - Test search and filtering functionality
  - [ ] 5.2 Create video API client functions (`frontend/src/lib/api.ts` or new file)
    - getPresignedUrl(fileMetadata): Request presigned URL from POST /api/upload/presigned-url with file name, size, type
    - uploadToS3(presignedUrl, file): Upload file directly to S3 using presigned URL with progress tracking via XMLHttpRequest
    - createVideoRecord(videoData): Create video record after upload completes via POST /api/videos
    - getVideos(filters, pagination): List videos with filters and pagination via GET /api/videos
    - getVideo(videoId): Get video details via GET /api/videos/{id}
    - updateVideo(videoId, data): Update video title/description via PATCH /api/videos/{id}
    - deleteVideo(videoId): Delete video with confirmation via DELETE /api/videos/{id}
    - Reuse pattern from: existing apiClient in `frontend/src/lib/api.ts`
  - [ ] 5.3 Create upload progress component (`frontend/src/components/video/UploadProgress.tsx`)
    - Real-time progress bar (0-100%) using Shadcn/ui Progress component
    - Display upload speed (MB/s) and estimated time remaining calculated from upload rate
    - Status text: preparing, uploading, processing, complete with appropriate icons
    - Error display with clear error message and retry button that restarts upload
    - Cancel button during upload that aborts XMLHttpRequest and cleans up state
    - Reuse pattern from: TranscriptionProgress component for polling and progress display
  - [ ] 5.4 Create upload page (`frontend/src/app/upload/page.tsx`)
    - Dedicated upload page with drag-and-drop zone using HTML5 drag-and-drop API
    - File picker fallback button for browsers without drag-and-drop support
    - Client-side validation before upload (file type, size) with immediate error display
    - Display file name, size, format before upload starts
    - Optional title and description input fields using Shadcn/ui Input components
    - Upload progress component integration
    - Upload status indicators: preparing, uploading, processing, complete with visual badges
    - Error handling with retry button that restarts upload flow from presigned URL request
    - Use ProtectedRoute component to protect the page
    - Reuse: Shadcn/ui components (Button, Card, Input, Badge, Progress)
  - [ ] 5.5 Create video list/grid components (`frontend/src/components/video/`)
    - VideoGrid component: Card layout with video thumbnails (placeholder images initially), responsive grid (4 columns desktop, 2 mobile)
    - VideoList component: Table layout with sortable columns (thumbnail, title, duration, file size, upload date, status, actions)
    - VideoCard component: Show title (truncated if long), duration, file size, upload date (relative time), status badge
    - Action buttons: View (navigate to detail page), Edit (navigate to editor), Delete (with confirmation dialog)
    - Click card to navigate to video detail page, hover effects for better UX
    - Empty state component for no videos
    - Reuse: Shadcn/ui components (Card, Badge, Button, Table, DropdownMenu)
  - [ ] 5.6 Create processing queue component (`frontend/src/components/video/ProcessingQueue.tsx`)
    - Display videos with "processing" status
    - Auto-refresh every 5 seconds to update status
    - Show processing progress for each video
    - Link to view video details
    - Reuse pattern from: TranscriptionProgress component for polling
  - [ ] 5.7 Create stats cards component (`frontend/src/components/video/StatsCards.tsx`)
    - Total Videos: Count of all user's videos
    - Storage Used: Total size of all videos (GB)
    - Processing Time: Total minutes of video processed
    - Recent Activity: Count of videos uploaded in last 7 days
    - Display cards in responsive grid (4 columns desktop, 2 mobile)
    - Reuse: Shadcn/ui Card component
  - [ ] 5.8 Update dashboard page (`frontend/src/app/dashboard/page.tsx`)
    - Stats cards section at top
    - Video grid/list view toggle with preference stored in LocalStorage
    - Search bar for finding videos by title with real-time filtering
    - Prominent upload button linking to `/upload` page
    - Processing queue section with auto-refresh (every 5 seconds)
    - Filter by status: All, Uploaded, Processing, Completed, Failed with URL query parameters
    - Sort by: Date (newest/oldest), Name (A-Z/Z-A), Duration (longest/shortest) with visual indicators
    - Empty states for no videos, no processing queue, no search results with helpful messages
    - Use ProtectedRoute component to protect the page
    - Server Component for initial data fetch, Client Component for interactions
    - Reuse: All components created in 5.3-5.7
  - [ ] 5.9 Create dashboard API endpoint integration
    - GET /api/dashboard/stats: Return user statistics (total videos, storage used, processing time, recent activity)
    - Enhance GET /api/videos with search parameter for title filtering
    - Add stats calculation logic in backend
  - [ ] 5.10 Apply responsive design
    - Mobile: 320px - 768px
    - Tablet: 768px - 1024px
    - Desktop: 1024px+
    - Follow existing responsive patterns from transcript components
  - [ ] 5.11 Ensure UI component tests pass
    - Run ONLY the 2-8 tests written in 5.1
    - Verify critical component behaviors work
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 5.1 pass
- Components render correctly
- Upload flow works end-to-end
- Progress tracking works
- Dashboard displays videos correctly
- Search and filtering work
- Matches visual design (Shadcn/ui)

### Testing

#### Task Group 6: Test Review & Gap Analysis
**Dependencies:** Task Groups 1-5

- [ ] 6.0 Review existing tests and fill critical gaps only
  - [ ] 6.1 Review tests from Task Groups 1-5
    - Review the 2-8 tests written by infrastructure setup (Task 1.3)
    - Review the 2-8 tests written by database-engineer (Task 2.1)
    - Review the 2-8 tests written by api-engineer (Task 3.1)
    - Review the 2-8 tests written by worker-engineer (Task 4.1)
    - Review the 2-8 tests written by ui-designer (Task 5.1)
    - Total existing tests: approximately 10-40 tests
  - [ ] 6.2 Analyze test coverage gaps for THIS feature only
    - Identify critical user workflows that lack test coverage
    - Focus ONLY on gaps related to Phase 1 completion feature requirements
    - Do NOT assess entire application test coverage
    - Prioritize end-to-end workflows over unit test gaps
  - [ ] 6.3 Write up to 10 additional strategic tests maximum
    - Add maximum of 10 new tests to fill identified critical gaps
    - Focus on integration points and end-to-end workflows
    - Examples: Complete upload flow E2E, S3/MinIO upload integration, metadata extraction flow, dashboard stats calculation
    - Do NOT write comprehensive coverage for all scenarios
    - Skip edge cases, performance tests, and accessibility tests unless business-critical
  - [ ] 6.4 Run feature-specific tests only
    - Run ONLY tests related to Phase 1 completion feature (tests from 1.3, 2.1, 3.1, 4.1, 5.1, and 6.3)
    - Expected total: approximately 20-50 tests maximum
    - Do NOT run the entire test suite
    - Verify critical workflows pass

**Acceptance Criteria:**
- All feature-specific tests pass (approximately 20-50 tests total)
- Critical user workflows for Phase 1 completion are covered
- No more than 10 additional tests added when filling in testing gaps
- Testing focused exclusively on Phase 1 completion feature requirements

## Execution Order

Recommended implementation sequence:
1. Infrastructure & Configuration (Task Group 1)
2. Database Layer (Task Group 2)
3. Backend API Layer (Task Group 3)
4. Background Jobs (Task Group 4)
5. Frontend Components (Task Group 5)
6. Test Review & Gap Analysis (Task Group 6)

## Notes

- This spec unifies implementation from both `2025-11-07-video-upload` and `2025-11-07-dashboard` specs
- MinIO is used for local development instead of mocking S3
- Metadata extraction happens asynchronously via background job for better UX
- Upload page is accessible both as dedicated `/upload` page and from dashboard
- Video API includes PATCH endpoint for title/description updates
- Error handling includes retry functionality for failed uploads
- Processing status is shown immediately with progress indicators

