# Task Breakdown: Video Export

## Overview
Total Tasks: 4 task groups

## Task List

### Database Layer

#### Task Group 1: Export Model and Migrations
**Dependencies:** Video Upload (Task Group 1), Timeline Editor (Task Group 1)

- [ ] 1.0 Complete database layer
  - [ ] 1.1 Write 2-8 focused tests for Export model
  - [ ] 1.2 Create Export model with video_id, user_id, resolution, quality, format, output_url, status enum, progress, segments array (JSONB)
  - [ ] 1.3 Create migration with indexes on video_id, user_id, and status
  - [ ] 1.4 Set up associations (Export belongs_to Video and User)
  - [ ] 1.5 Ensure database layer tests pass

### Backend API Layer

#### Task Group 2: Export Service and API Endpoints
**Dependencies:** Task Group 1

- [ ] 2.0 Complete API layer
  - [ ] 2.1 Write 2-8 focused tests for export endpoints
  - [ ] 2.2 Create export service (combine segments, re-encode with FFmpeg/PyAV, upload to S3)
  - [ ] 2.3 Create ARQ task: export_video for async processing
  - [ ] 2.4 Implement progress tracking in Redis
  - [ ] 2.5 Add API endpoints: POST /api/videos/{id}/export, GET /api/exports/{id}, GET /api/exports/{id}/download, GET /api/exports, DELETE /api/exports/{id}
  - [ ] 2.6 Implement ZIP generation for multiple clips
  - [ ] 2.7 Ensure API layer tests pass

### Frontend Components

#### Task Group 3: Export UI Components
**Dependencies:** Task Group 2, Timeline Editor (for segment selection)

- [ ] 3.0 Complete UI components
  - [ ] 3.1 Write 2-8 focused tests for export components
  - [ ] 3.2 Create export modal with settings (resolution, quality, single/multiple options)
  - [ ] 3.3 Implement export progress tracking (progress bar, SSE/polling updates)
  - [ ] 3.4 Add download functionality (single video or ZIP)
  - [ ] 3.5 Create export history interface
  - [ ] 3.6 Ensure UI component tests pass

### Testing

#### Task Group 4: Test Review & Gap Analysis
**Dependencies:** Task Groups 1-3

- [ ] 4.0 Review existing tests and fill critical gaps
  - [ ] 4.1 Review tests from Task Groups 1-3
  - [ ] 4.2 Analyze test coverage gaps
  - [ ] 4.3 Write up to 10 additional strategic tests
  - [ ] 4.4 Run feature-specific tests only

## Execution Order
1. Database Layer (Task Group 1)
2. Backend API Layer (Task Group 2)
3. Frontend Components (Task Group 3)
4. Test Review & Gap Analysis (Task Group 4)

