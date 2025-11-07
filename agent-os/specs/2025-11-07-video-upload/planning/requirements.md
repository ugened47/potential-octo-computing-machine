# Spec Requirements: Video Upload

## Initial Description

Video Upload is a foundational feature that allows users to upload video files to the platform. Users can drag-and-drop videos or use a file picker, and videos are uploaded directly to S3 using presigned URLs. The system validates file types and sizes, tracks upload progress, and stores video metadata in the database.

## Requirements Discussion

### Requirements Summary

Based on PRD.md, TASKS.md, and existing spec.md, the following requirements have been established:

**Supported Formats:** MP4, MOV, AVI, WebM, MKV
**Maximum File Size:** 2GB
**Upload Method:** Direct S3 upload via presigned URLs
**Progress Tracking:** Real-time progress bar with speed and ETA
**Metadata Extraction:** Asynchronous extraction after upload (duration, resolution, format)

### Existing Code to Reference

**Backend Patterns:**
- Authentication: Use get_current_user dependency from `backend/app/api/deps.py`
- Error Handling: Follow HTTPException pattern from auth routes
- Database: Use SQLModel async patterns from User model
- Configuration: Use Settings class from `backend/app/core/config.py` for S3 credentials
- API Routes: Follow FastAPI router pattern from `backend/app/api/routes/auth.py`

**Frontend Patterns:**
- Components: Use Shadcn/ui components (Button, Card, Input, Progress)
- Structure: Follow Next.js 14 App Router with Server/Client component separation
- State: Use Zustand if needed, following project conventions
- Styling: Follow existing Tailwind CSS theme

## Visual Assets

### Files Provided:
No visual files found.

### Visual Insights:
No visual assets provided. Will follow Shadcn/ui design system and existing project styling patterns.

## Requirements Summary

### Functional Requirements

**Backend:**
- Video model with all required fields and relationships
- Presigned URL generation for S3 uploads
- Video validation service (format, size, MIME type)
- API endpoints for upload flow and video management
- Database migration for videos table
- S3 storage service with proper path structure
- CloudFront URL generation

**Frontend:**
- Drag-and-drop upload component
- File picker fallback
- Client-side validation
- Upload progress tracking
- Video list component with metadata display
- Error handling and retry functionality

### Scope Boundaries

**In Scope:**
- Single video uploads (one at a time)
- Direct S3 upload via presigned URLs
- Progress tracking and status display
- Video metadata storage
- Video list management
- File validation (client and server)

**Out of Scope:**
- Video thumbnail generation
- Video transcoding/encoding
- Batch upload of multiple videos
- Video preview before upload completes
- Upload resumption after network failure
- Video editing capabilities
- Video sharing/permissions
- Upload from URL or cloud storage
- Video metadata editing after upload
- Upload queue management

### Technical Considerations

- Dependencies: User Authentication must be complete
- S3 bucket CORS configuration required for direct browser uploads
- Presigned URLs expire after 15 minutes
- Video metadata extraction happens asynchronously after upload
- Use UUID for filenames to avoid collisions
- Store videos in path structure: videos/{user_id}/{video_id}/{filename}

