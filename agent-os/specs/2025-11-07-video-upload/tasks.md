# Task Breakdown: Video Upload

## Overview
Total Tasks: 4 task groups, 25+ sub-tasks

## Task List

### Database Layer

#### Task Group 1: Video Model and Migrations
**Dependencies:** User Authentication (Task Group 1 from user-authentication spec)

- [ ] 1.0 Complete database layer
  - [ ] 1.1 Write 2-8 focused tests for Video model functionality
    - Test Video model creation with required fields
    - Test Video model validation (title, user_id foreign key)
    - Test Video model status enum (uploaded, processing, completed, failed)
    - Test Video model relationships with User
  - [ ] 1.2 Create Video model with validations
    - Fields: id (UUID), user_id (foreign key), title, description (optional)
    - File metadata: size, format, duration, resolution, S3 key, CloudFront URL
    - Processing status enum: uploaded, processing, completed, failed
    - Timestamps: created_at, updated_at
    - Reuse pattern from: User model in `backend/app/models/user.py`
  - [ ] 1.3 Create migration for videos table
    - Add indexes on user_id and created_at
    - Foreign key relationship to users table
    - Add status enum type
  - [ ] 1.4 Set up associations
    - Video belongs_to User (user_id foreign key)
    - User has_many Videos (relationship defined)
  - [ ] 1.5 Ensure database layer tests pass
    - Run ONLY the 2-8 tests written in 1.1
    - Verify migrations run successfully
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1 pass
- Video model passes validation tests
- Migrations run successfully
- Associations work correctly

### Backend API Layer

#### Task Group 2: Upload API Endpoints and Services
**Dependencies:** Task Group 1

- [ ] 2.0 Complete API layer
  - [ ] 2.1 Write 2-8 focused tests for API endpoints
    - Test POST /api/upload/presigned-url generates valid URL
    - Test POST /api/videos creates video record
    - Test GET /api/videos lists user's videos
    - Test DELETE /api/videos/{id} deletes video and S3 file
  - [ ] 2.2 Create video validation service
    - Validate file extension against allowed formats (MP4, MOV, AVI, WebM, MKV)
    - Check file size against max_upload_size_mb setting (2GB default)
    - Verify MIME type matches video format
    - Return clear error messages for validation failures
  - [ ] 2.3 Create S3 storage service
    - Generate presigned URLs with 15-minute expiration
    - Store videos in S3 with path structure: videos/{user_id}/{video_id}/{filename}
    - Use UUID for filenames to avoid collisions
    - Generate CloudFront URLs for video delivery
    - Configure S3 bucket CORS for direct browser uploads
  - [ ] 2.4 Create upload API endpoints
    - POST /api/upload/presigned-url: Generate S3 presigned URL, validate file type/size, return upload URL and video_id
    - POST /api/videos: Create video record after upload completes, accept video_id, title, description, S3 key
    - Follow pattern from: `backend/app/api/routes/auth.py`
  - [ ] 2.5 Create video management API endpoints
    - GET /api/videos: List user's videos with pagination, filtering by status, sorting by date
    - GET /api/videos/{id}: Get video details including metadata and processing status
    - DELETE /api/videos/{id}: Delete video record and S3 file, require user ownership
  - [ ] 2.6 Implement authentication/authorization
    - Use existing auth pattern (get_current_user dependency)
    - Add permission checks (users can only access their own videos)
  - [ ] 2.7 Add API response formatting
    - JSON responses with proper schemas
    - Error handling with appropriate status codes
    - Consistent response format
  - [ ] 2.8 Implement video metadata extraction (async)
    - Extract duration, resolution, format after video record creation
    - Update video record with metadata
    - Handle extraction errors gracefully
  - [ ] 2.9 Ensure API layer tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify critical CRUD operations work
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- All CRUD operations work
- Proper authorization enforced
- Consistent response format
- Presigned URLs work correctly
- S3 uploads succeed

### Frontend Components

#### Task Group 3: Upload UI Components
**Dependencies:** Task Group 2

- [ ] 3.0 Complete UI components
  - [ ] 3.1 Write 2-8 focused tests for UI components
    - Test upload component file selection
    - Test drag-and-drop functionality
    - Test upload progress tracking
    - Test video list component rendering
  - [ ] 3.2 Create upload page/component
    - Drag-and-drop zone with visual feedback (highlight on drag over)
    - File picker fallback button for browsers without drag-drop support
    - Client-side validation before upload starts (show errors immediately)
    - Display file name, size, and format before upload begins
    - Optional title and description input fields
    - Reuse: Shadcn/ui components (Button, Card, Input)
  - [ ] 3.3 Implement upload progress component
    - Progress bar component showing percentage (0-100%)
    - Display upload speed and estimated time remaining
    - Show upload status: preparing, uploading, processing, complete
    - Handle upload cancellation/abort functionality
    - Display error messages if upload fails with retry option
  - [ ] 3.4 Build video list component
    - Card grid layout showing video thumbnails (placeholder initially)
    - Display video metadata: title, duration, upload date, file size
    - Show processing status badge (uploaded, processing, completed, failed)
    - Action buttons: view, edit, delete with confirmation dialog
    - Empty state message when no videos uploaded
    - Match mockup: Follow Shadcn/ui design system
  - [ ] 3.5 Apply base styles
    - Follow existing design system
    - Use variables from: `frontend/src/app/globals.css`
  - [ ] 3.6 Implement responsive design
    - Mobile: 320px - 768px
    - Tablet: 768px - 1024px
    - Desktop: 1024px+
  - [ ] 3.7 Add interactions and animations
    - Hover states for cards and buttons
    - Transitions for upload progress
    - Loading states during upload
  - [ ] 3.8 Implement upload flow integration
    - Request presigned URL from backend
    - Upload directly to S3 using presigned URL
    - Track upload progress with XMLHttpRequest or fetch
    - Call backend API to create video record after upload
    - Handle errors and retries
  - [ ] 3.9 Ensure UI component tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify critical component behaviors work
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 3.1 pass
- Components render correctly
- Upload flow works end-to-end
- Progress tracking works
- Matches visual design (Shadcn/ui)

### Testing

#### Task Group 4: Test Review & Gap Analysis
**Dependencies:** Task Groups 1-3

- [ ] 4.0 Review existing tests and fill critical gaps only
  - [ ] 4.1 Review tests from Task Groups 1-3
    - Review the 2-8 tests written by database-engineer (Task 1.1)
    - Review the 2-8 tests written by api-engineer (Task 2.1)
    - Review the 2-8 tests written by ui-designer (Task 3.1)
    - Total existing tests: approximately 6-24 tests
  - [ ] 4.2 Analyze test coverage gaps for THIS feature only
    - Identify critical user workflows that lack test coverage
    - Focus ONLY on gaps related to video upload feature requirements
    - Do NOT assess entire application test coverage
    - Prioritize end-to-end workflows over unit test gaps
  - [ ] 4.3 Write up to 10 additional strategic tests maximum
    - Add maximum of 10 new tests to fill identified critical gaps
    - Focus on integration points and end-to-end workflows
    - Examples: Complete upload flow E2E, S3 upload integration, error handling flows
    - Do NOT write comprehensive coverage for all scenarios
    - Skip edge cases, performance tests, and accessibility tests unless business-critical
  - [ ] 4.4 Run feature-specific tests only
    - Run ONLY tests related to video upload feature (tests from 1.1, 2.1, 3.1, and 4.3)
    - Expected total: approximately 16-34 tests maximum
    - Do NOT run the entire test suite
    - Verify critical workflows pass

**Acceptance Criteria:**
- All feature-specific tests pass (approximately 16-34 tests total)
- Critical user workflows for video upload are covered
- No more than 10 additional tests added when filling in testing gaps
- Testing focused exclusively on video upload feature requirements

## Execution Order

Recommended implementation sequence:
1. Database Layer (Task Group 1)
2. Backend API Layer (Task Group 2)
3. Frontend Components (Task Group 3)
4. Test Review & Gap Analysis (Task Group 4)

