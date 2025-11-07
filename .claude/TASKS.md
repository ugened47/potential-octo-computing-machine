# AI Video Clipper - Project Tasks

> **Last Updated:** 2025-11-07
> **Status:** MVP Development Phase

This file tracks implementation status of all features defined in PRD.md. Use `/feature [name]` slash command to implement features systematically.

---

## Task Status Legend

- 🔴 **Not Started** - Task not yet begun
- 🟡 **In Progress** - Currently being worked on
- 🟢 **Completed** - Implementation done and tested
- ⚪ **Blocked** - Waiting on dependencies or decisions

---

## MVP Phase (Week 1-12) - MUST HAVE

### 1. Project Foundation & Infrastructure

#### 1.1 Initial Setup
- 🟢 Project structure created
- 🟢 Docker Compose configuration
- 🟢 Environment variables template (.env.example)
- 🟢 README and documentation
- 🟢 CLAUDE.md development guide
- 🟢 Claude Code slash commands created
- 🟢 Claude Code skills created
- 🔴 CI/CD pipeline (GitHub Actions)
  - Backend tests on PR
  - Frontend tests on PR
  - Automated deployment

#### 1.2 Backend Foundation
- 🔴 FastAPI application setup
  - Main app entry point
  - Configuration management
  - Logging setup
  - Error handling middleware
- 🔴 Database setup
  - PostgreSQL connection
  - SQLModel base models
  - Alembic migrations setup
- 🔴 Redis setup
  - Connection configuration
  - ARQ worker setup
- 🔴 S3 storage service
  - Upload presigned URLs
  - Download URLs
  - CloudFront CDN integration

#### 1.3 Frontend Foundation
- 🔴 Next.js 14 app setup
  - App router structure
  - Layout components
  - Global styles
- 🔴 Shadcn UI installation
  - Theme configuration
  - Base components (Button, Card, Input, etc.)
- 🔴 API client setup
  - Axios/Fetch configuration
  - Authentication interceptors
  - Error handling

---

### 2. User Authentication (Feature #1)

**Dependencies:** Backend Foundation, Frontend Foundation

#### 2.1 Backend Implementation
- 🔴 User model
  - UUID primary key
  - Email, password hash
  - Created/updated timestamps
  - Email verification status
- 🔴 Security utilities
  - Password hashing (bcrypt)
  - JWT token generation/validation
  - Refresh token management
- 🔴 Auth API endpoints
  - POST /api/auth/register
  - POST /api/auth/login
  - POST /api/auth/refresh
  - POST /api/auth/logout
  - POST /api/auth/forgot-password
  - POST /api/auth/reset-password
  - GET /api/auth/me
- 🔴 Google OAuth integration
  - OAuth2 flow setup
  - Google API credentials
  - User creation from OAuth
- 🔴 Auth tests
  - Unit tests for security functions
  - Integration tests for endpoints
  - Test fixtures for users

#### 2.2 Frontend Implementation
- 🔴 Auth pages
  - Login page
  - Register page
  - Forgot password page
  - Reset password page
- 🔴 Auth components
  - Login form with validation
  - Register form with validation
  - Google OAuth button
- 🔴 Auth context/state
  - User state management
  - Token storage (httpOnly cookies)
  - Auto-refresh on token expiry
- 🔴 Protected routes
  - Middleware for auth check
  - Redirect to login if not authenticated
- 🔴 Auth tests
  - Component tests
  - E2E tests for flows

**Status:** 🔴 Not Started

---

### 3. Video Upload (Feature #2)

**Dependencies:** User Authentication, S3 Storage Service

#### 3.1 Backend Implementation
- 🔴 Video model
  - UUID, user_id, title, description
  - File metadata (size, format, duration)
  - S3 key, CloudFront URL
  - Processing status enum
  - Timestamps
- 🔴 Upload API endpoints
  - POST /api/upload/presigned-url
    - Generate S3 presigned URL
    - Validate file type/size
  - POST /api/videos
    - Create video record after upload
  - GET /api/videos
    - List user's videos
  - GET /api/videos/{id}
    - Get video details
  - DELETE /api/videos/{id}
    - Delete video and S3 file
- 🔴 Video validation service
  - Check format (MP4, MOV, AVI, WebM)
  - Check size limit (2GB)
  - Verify uploaded file
- 🔴 Database migration
  - Create videos table
  - Add indexes
- 🔴 Tests

#### 3.2 Frontend Implementation
- 🔴 Upload page/component
  - Drag-and-drop zone
  - File picker fallback
  - File validation (client-side)
- 🔴 Upload progress
  - Progress bar component
  - Upload to S3 via presigned URL
  - Abort upload functionality
- 🔴 Video list component
  - Card grid layout
  - Video thumbnails
  - Metadata display
  - Action buttons
- 🔴 Tests

**Status:** 🔴 Not Started

---

### 4. Automatic Transcription (Feature #3)

**Dependencies:** Video Upload, ARQ Worker

#### 4.1 Backend Implementation
- 🔴 Transcript model
  - video_id (foreign key)
  - Full text
  - Word-level timestamps (JSONB)
  - Language
  - Status (processing, completed, failed)
- 🔴 Transcription service
  - OpenAI Whisper API integration
  - Chunked processing for long videos
  - Word timestamp extraction
  - Language detection
- 🔴 Background job
  - ARQ task: transcribe_video
  - Progress tracking in Redis
  - Error handling and retries
- 🔴 API endpoints
  - GET /api/videos/{id}/transcript
  - POST /api/videos/{id}/transcribe (manual trigger)
  - GET /api/videos/{id}/transcript/export (SRT/VTT)
- 🔴 Database migration
- 🔴 Tests

#### 4.2 Frontend Implementation
- 🔴 Transcript display component
  - Scrollable transcript panel
  - Word highlighting
  - Click word to seek video
  - Search within transcript
- 🔴 Processing status
  - Real-time progress via SSE
  - Loading states
  - Error handling
- 🔴 Export transcript
  - Download as SRT
  - Download as VTT
- 🔴 Tests

**Status:** 🔴 Not Started

---

### 5. Silence Removal (Feature #4)

**Dependencies:** Automatic Transcription

#### 5.1 Backend Implementation
- 🔴 Audio analysis service
  - Extract audio from video (PyAV)
  - Detect silent segments
  - Configurable threshold (-40dB default)
  - Minimum silence duration (1s default)
- 🔴 Video processing service
  - Remove silent segments
  - Re-encode video (FFmpeg/PyAV)
  - Maintain audio sync
- 🔴 Background job
  - ARQ task: remove_silence
  - Progress tracking
- 🔴 API endpoints
  - POST /api/videos/{id}/remove-silence
    - Parameters: threshold, min_duration
  - GET /api/videos/{id}/silence-segments
    - Return detected silent parts
- 🔴 Tests

#### 5.2 Frontend Implementation
- 🔴 Silence removal UI
  - Settings modal
  - Threshold slider (-60dB to -20dB)
  - Min duration input
- 🔴 Preview functionality
  - Before/after comparison
  - Visual indicators on timeline
- 🔴 Apply silence removal
  - Trigger processing
  - Show progress
  - Update video after completion
- 🔴 Tests

**Status:** 🔴 Not Started

---

### 6. Keyword Search & Clipping (Feature #5)

**Dependencies:** Automatic Transcription

#### 6.1 Backend Implementation
- 🔴 Clip model
  - video_id, start_time, end_time
  - Title, description
  - Keywords (array)
  - Clip URL (S3)
  - Status
- 🔴 Search service
  - Full-text search in transcript
  - Fuzzy matching
  - Multiple keyword support
  - Return time ranges with context
- 🔴 Clip generation service
  - Extract video segment
  - Add padding (±5 seconds)
  - Generate clip file
- 🔴 API endpoints
  - POST /api/videos/{id}/search
    - Body: { keywords: string[] }
  - POST /api/videos/{id}/clips
    - Create clip from time range
  - GET /api/videos/{id}/clips
  - DELETE /api/clips/{id}
- 🔴 Database migration
- 🔴 Tests

#### 6.2 Frontend Implementation
- 🔴 Keyword search component
  - Search input with multi-keyword support
  - Search results list
  - Highlight matches in transcript
- 🔴 Clip creation UI
  - Select search results
  - Preview clip range
  - Adjust start/end times
  - Create clip button
- 🔴 Clips management
  - List created clips
  - Preview clips
  - Delete clips
- 🔴 Tests

**Status:** 🔴 Not Started

---

### 7. Timeline Editor (Feature #6)

**Dependencies:** Automatic Transcription, Keyword Search

#### 7.1 Backend Implementation
- 🔴 Timeline state management
  - Store segment selections
  - Calculate final video duration
- 🔴 Audio waveform generation
  - Generate waveform data
  - Cache in S3
- 🔴 API endpoints
  - GET /api/videos/{id}/waveform
  - POST /api/videos/{id}/segments
    - Update segment selections

#### 7.2 Frontend Implementation
- 🔴 Timeline component (React-Konva)
  - Video track visualization
  - Audio waveform display (Wavesurfer.js)
  - Playhead/cursor
  - Zoom controls
- 🔴 Segment management
  - Select/deselect segments
  - Drag to trim
  - Reorder clips (drag & drop)
- 🔴 Transcript sync
  - Highlight current word during playback
  - Click transcript to seek
  - Auto-scroll transcript
- 🔴 Video player integration
  - Video.js or Remotion Player
  - Play/pause controls
  - Seek functionality
  - Playback speed
- 🔴 Tests

**Status:** 🔴 Not Started

---

### 8. Video Export (Feature #7)

**Dependencies:** Timeline Editor, Video Processing Service

#### 8.1 Backend Implementation
- 🔴 Export model
  - video_id, user_id
  - Resolution, format, quality
  - Output URL (S3)
  - Status, progress
  - File size
- 🔴 Export service
  - Combine selected segments
  - Re-encode with settings
  - Upload to S3
  - Generate download URL
- 🔴 Background job
  - ARQ task: export_video
  - Progress tracking (%)
  - Estimated time remaining
- 🔴 API endpoints
  - POST /api/videos/{id}/export
    - Parameters: resolution, quality, segments
  - GET /api/exports/{id}
    - Export status and progress
  - GET /api/exports/{id}/download
    - Generate download URL
- 🔴 Database migration
- 🔴 Tests

#### 8.2 Frontend Implementation
- 🔴 Export modal
  - Resolution selector (720p, 1080p)
  - Quality preset (High, Medium, Low)
  - Export options (single/multiple clips)
- 🔴 Export progress
  - Progress bar
  - Estimated time remaining
  - Real-time updates via SSE
- 🔴 Download functionality
  - Download button
  - ZIP for multiple clips
  - Copy shareable link
- 🔴 Tests

**Status:** 🔴 Not Started

---

### 9. Dashboard (Feature #8)

**Dependencies:** Video Upload, User Authentication

#### 9.1 Backend Implementation
- 🔴 Dashboard API
  - GET /api/dashboard/stats
    - Total videos, clips, processing time
  - GET /api/videos?sort=date&status=processing
    - Filtering and sorting

#### 9.2 Frontend Implementation
- 🔴 Dashboard page
  - Stats cards (total videos, storage used, etc.)
  - Recent videos list
  - Processing queue
- 🔴 Video grid/list view
  - Toggle between grid and list
  - Sort by date, name, duration
  - Filter by status
- 🔴 Quick actions
  - View/Edit buttons
  - Delete with confirmation
  - Duplicate video
- 🔴 Tests

**Status:** 🔴 Not Started

---

## Post-MVP Phase (Month 4-6) - SHOULD HAVE

### 10. Auto-Highlight Detection (Feature #9)
**Status:** 🔴 Not Started

**Tasks:**
- Implement highlight scoring algorithm
- Audio energy analysis
- Scene change detection (PySceneDetect)
- Keyword-based scoring
- API endpoints for highlights
- Frontend highlight suggestions UI

---

### 11. Batch Processing (Feature #10)
**Status:** 🔴 Not Started

**Tasks:**
- Batch upload API
- Queue management system
- Apply settings to multiple videos
- Bulk export functionality
- Frontend batch operations UI

---

### 12. Embedded Subtitles (Feature #11)
**Status:** 🔴 Not Started

**Tasks:**
- Subtitle styling options
- Burn subtitles into video (FFmpeg)
- Multi-language support
- Google Translate API integration
- Subtitle customization UI

---

### 13. Social Media Templates (Feature #12)
**Status:** 🔴 Not Started

**Tasks:**
- Template presets (YouTube Shorts, TikTok, Instagram)
- Aspect ratio conversion (9:16)
- Duration limits enforcement
- Auto-caption overlay
- Template selection UI

---

### 14. Team Collaboration (Feature #13)
**Status:** 🔴 Not Started

**Tasks:**
- Organization/team models
- Role-based access control (RBAC)
- Sharing functionality
- Timeline comments
- Version history
- Collaboration UI

---

### 15. Advanced Editor (Feature #14)
**Status:** 🔴 Not Started

**Tasks:**
- Multi-track timeline
- Image/overlay support
- Transitions library
- Background music
- Advanced editor UI

---

## Future Features (Month 7+) - COULD HAVE

### 16. Live Stream Processing (Feature #15)
**Status:** 🔴 Not Started

### 17. AI Chapter Generation (Feature #16)
**Status:** 🔴 Not Started

### 18. Mobile Apps (Feature #17)
**Status:** 🔴 Not Started

### 19. API Access (Feature #18)
**Status:** 🔴 Not Started

---

## Cross-Cutting Concerns

### Security
- 🔴 Rate limiting implementation
- 🔴 CORS configuration (production)
- 🔴 Input sanitization review
- 🔴 Security audit
- 🔴 Penetration testing

### Performance
- 🔴 Database query optimization
- 🔴 Redis caching strategy
- 🔴 CDN configuration
- 🔴 Video processing optimization
- 🔴 Frontend bundle optimization
- 🔴 Load testing

### Monitoring & Observability
- 🔴 Application logging (structured logs)
- 🔴 Error tracking (Sentry)
- 🔴 Performance monitoring (APM)
- 🔴 Uptime monitoring
- 🔴 Cost tracking (AWS)

### Documentation
- 🔴 API documentation (OpenAPI/Swagger)
- 🔴 User guide
- 🔴 Video tutorials
- 🔴 Troubleshooting guide
- 🔴 Developer onboarding docs

### Testing
- 🔴 Backend unit tests (>80% coverage)
- 🔴 Backend integration tests
- 🔴 Frontend component tests
- 🔴 Frontend E2E tests (Playwright)
- 🔴 Load testing (Locust/k6)

---

## Development Workflow

### Starting a New Feature

1. **Update this file** - Mark feature as 🟡 In Progress
2. **Use slash commands**:
   ```
   /feature [feature-name]
   ```
3. **Follow the workflow**:
   - Read related code
   - Create implementation plan with TodoWrite
   - Implement backend → frontend → tests
   - Run `/quality` before committing
   - Run `/test all` to verify
4. **Update status** - Mark as 🟢 Completed when done

### Weekly Review

- Review completed tasks
- Update priorities
- Identify blockers
- Plan next week's work

---

## Notes

- This task list is synchronized with PRD.md
- Update task status as features are completed
- Use `/feature` command to implement features systematically
- Refer to CLAUDE.md for development guidelines
- All MUST HAVE features should be completed before moving to SHOULD HAVE

---

**Last Reviewed:** 2025-11-07
