# Specification: Video Upload

## Goal
Enable users to upload video files to the platform with drag-and-drop interface, direct S3 upload via presigned URLs, progress tracking, and metadata storage.

## User Stories
- As a content creator, I want to upload videos by dragging and dropping them so that I can quickly add content without navigating file dialogs
- As a user, I want to see upload progress so that I know how long the upload will take

## Specific Requirements

**Video Upload Flow**
- Frontend requests presigned URL from backend with file metadata (name, size, type)
- Backend validates file type (MP4, MOV, AVI, WebM, MKV) and size (max 2GB) before generating presigned URL
- Frontend uploads directly to S3 using presigned URL with progress tracking
- After successful upload, frontend calls backend API to create video record in database
- Backend extracts video metadata (duration, resolution, format) asynchronously after record creation

**Video Model & Database**
- Create Video model with UUID primary key, user_id foreign key, title, description (optional)
- Store file metadata: size, format, duration, resolution, S3 key, CloudFront URL
- Include processing status enum: uploaded, processing, completed, failed
- Add timestamps: created_at, updated_at
- Create database migration with indexes on user_id and created_at

**Upload API Endpoints**
- POST /api/upload/presigned-url: Generate S3 presigned URL with expiration (15 minutes), validate file type/size, return upload URL and video_id
- POST /api/videos: Create video record after upload completes, accept video_id, title, description, S3 key
- GET /api/videos: List user's videos with pagination, filtering by status, sorting by date
- GET /api/videos/{id}: Get video details including metadata and processing status
- DELETE /api/videos/{id}: Delete video record and S3 file, require user ownership

**Video Validation Service**
- Validate file extension against allowed formats from config
- Check file size against max_upload_size_mb setting (2GB default)
- Verify MIME type matches video format
- Return clear error messages for validation failures

**Upload UI Component**
- Drag-and-drop zone with visual feedback (highlight on drag over)
- File picker fallback button for browsers without drag-drop support
- Client-side validation before upload starts (show errors immediately)
- Display file name, size, and format before upload begins
- Optional title and description input fields

**Upload Progress Tracking**
- Progress bar component showing percentage (0-100%)
- Display upload speed and estimated time remaining
- Show upload status: preparing, uploading, processing, complete
- Handle upload cancellation/abort functionality
- Display error messages if upload fails with retry option

**Video List Component**
- Card grid layout showing video thumbnails (placeholder initially)
- Display video metadata: title, duration, upload date, file size
- Show processing status badge (uploaded, processing, completed, failed)
- Action buttons: view, edit, delete with confirmation dialog
- Empty state message when no videos uploaded

**S3 Storage Service**
- Generate presigned URLs with 15-minute expiration for uploads
- Store videos in S3 with path structure: videos/{user_id}/{video_id}/{filename}
- Use UUID for filenames to avoid collisions
- Configure S3 bucket CORS for direct browser uploads
- Generate CloudFront URLs for video delivery after upload

## Visual Design
No visual assets provided. Follow Shadcn/ui design system and existing project styling.

## Existing Code to Leverage

**Backend Authentication Pattern**
- Use get_current_user dependency from app.api.deps for authenticated endpoints
- Follow same error handling pattern as auth routes (HTTPException with status codes)
- Use SQLModel async patterns from User model for Video model

**Configuration Management**
- Use Settings class from app.core.config for S3 credentials and upload limits
- Reference allowed_video_formats and max_upload_size_mb from config
- Follow same environment variable pattern for AWS credentials

**API Route Structure**
- Follow FastAPI router pattern from app.api.routes.auth
- Use Pydantic schemas for request/response validation like auth schemas
- Implement same async/await patterns for database operations

**Frontend Component Patterns**
- Use Shadcn/ui components (Button, Card, Input, Progress) following existing patterns
- Follow Next.js 14 App Router structure with Server/Client component separation
- Use Zustand for state management if needed, following project conventions

## Out of Scope
- Video thumbnail generation (defer to later feature)
- Video transcoding/encoding (handled by separate processing pipeline)
- Batch upload of multiple videos (post-MVP feature)
- Video preview before upload completes
- Upload resumption after network failure (cancel and retry only)
- Video editing capabilities (separate feature)
- Video sharing/permissions (post-MVP feature)
- Upload from URL or cloud storage (future enhancement)
- Video metadata editing after upload (separate feature)
- Upload queue management for multiple simultaneous uploads

