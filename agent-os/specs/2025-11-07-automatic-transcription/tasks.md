# Task Breakdown: Automatic Transcription

## Overview
Total Tasks: 4 task groups, 30+ sub-tasks

## Task List

### Database Layer

#### Task Group 1: Transcript Model and Migrations
**Dependencies:** Video Upload (Task Group 1)

- [x] 1.0 Complete database layer
  - [x] 1.1 Write 2-8 focused tests for Transcript model functionality
    - Test Transcript model creation with required fields (video_id, full_text, status)
    - Test Transcript model validation (video_id foreign key, status enum)
    - Test Transcript model word_timestamps JSONB field storage and retrieval
    - Test Transcript model language code (ISO 639-1) validation
    - Test Transcript model relationships with Video
    - Test Transcript model timestamps (created_at, updated_at, completed_at)
  - [x] 1.2 Create Transcript model with validations
    - Fields: id (UUID), video_id (foreign key to videos), full_text (text field)
    - word_timestamps (JSONB array with start_time, end_time, word, confidence)
    - language (ISO 639-1 code), status enum (processing, completed, failed)
    - accuracy_score (optional float), timestamps (created_at, updated_at, completed_at)
    - Reuse pattern from: Video model in `backend/app/models/video.py`
  - [x] 1.3 Create migration for transcripts table
    - Add index on video_id for fast lookups
    - Add full-text search index on full_text column
    - Foreign key relationship to videos table
    - Add status enum type (processing, completed, failed)
    - JSONB column for word_timestamps
  - [x] 1.4 Set up associations
    - Transcript belongs_to Video (video_id foreign key)
    - Video has_one Transcript (relationship defined)
  - [x] 1.5 Ensure database layer tests pass
    - Run ONLY the 2-8 tests written in 1.1
    - Verify migrations run successfully
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1 pass
- Transcript model passes validation tests
- Migrations run successfully
- Associations work correctly
- Full-text search index is created

### Backend API Layer

#### Task Group 2: Transcription Service and API Endpoints
**Dependencies:** Task Group 1, ARQ Worker setup

- [x] 2.0 Complete API layer
  - [x] 2.1 Write 2-8 focused tests for transcription endpoints
    - Test GET /api/videos/{id}/transcript returns transcript with word timestamps
    - Test GET /api/videos/{id}/transcript returns 404 if transcript not available
    - Test POST /api/videos/{id}/transcribe triggers transcription job
    - Test POST /api/videos/{id}/transcribe prevents duplicate transcription
    - Test GET /api/videos/{id}/transcript/export returns SRT format
    - Test GET /api/videos/{id}/transcript/export returns VTT format
    - Test GET /api/videos/{id}/transcript/progress returns progress percentage
  - [x] 2.2 Create transcription service with OpenAI Whisper API integration
    - Integrate OpenAI Whisper API client
    - Support language detection (English, Russian, Spanish, German, French)
    - Extract word-level timestamps from Whisper response (start_time, end_time, word, confidence)
    - Handle long videos by chunking if needed (Whisper 25MB audio limit)
    - Process Whisper API response and format word timestamps
    - Handle API rate limits and quota exceeded errors gracefully
    - Reuse pattern from: `backend/app/services/transcription.py` (if exists)
  - [x] 2.3 Create ARQ task: transcribe_video for async processing
    - Task function: transcribe_video(video_id: str)
    - Download video from S3 using video S3 key
    - Extract audio track from video using PyAV
    - Call Whisper API with extracted audio file
    - Process Whisper response and extract word timestamps
    - Store transcript data in database (full_text, word_timestamps, language, status)
    - Update video processing status when transcription completes
    - Handle errors with retry logic (max 3 attempts)
    - Register task in worker.py
  - [x] 2.4 Implement progress tracking in Redis
    - Track transcription progress (0-100%) in Redis
    - Key format: transcription_progress:{video_id}
    - Update progress at key stages (downloading, extracting audio, calling API, processing)
    - Set progress to 100% on completion
    - Clear progress key on completion or failure
  - [x] 2.5 Add API endpoints for transcript operations
    - GET /api/videos/{id}/transcript: Get transcript with word timestamps, return 404 if not available
    - POST /api/videos/{id}/transcribe: Manually trigger transcription (if not already processing/completed)
    - GET /api/videos/{id}/transcript/export: Export transcript as SRT or VTT format (query param: format=srt|vtt)
    - GET /api/videos/{id}/transcript/progress: Get transcription progress percentage (for SSE updates)
    - Follow pattern from: `backend/app/api/routes/transcript.py` (if exists)
  - [x] 2.6 Implement error handling and retry logic
    - Handle Whisper API errors (rate limits, quota exceeded, invalid audio)
    - Retry logic with exponential backoff (max 3 attempts)
    - Update transcript status to 'failed' on permanent failure
    - Log errors for debugging
    - Return appropriate error responses in API endpoints
  - [x] 2.7 Create Pydantic schemas for request/response validation
    - TranscriptResponse schema (id, video_id, full_text, word_timestamps, language, status, accuracy_score, timestamps)
    - TranscriptProgress schema (progress, status, estimated_time_remaining)
    - ExportFormat enum (srt, vtt)
    - Reuse pattern from: `backend/app/schemas/transcript.py` (if exists)
  - [x] 2.8 Implement authentication/authorization
    - Use existing auth pattern (get_current_user dependency)
    - Add permission checks (users can only access transcripts for their own videos)
  - [x] 2.9 Ensure API layer tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify all endpoints work correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- All API endpoints work correctly
- Transcription service integrates with Whisper API
- ARQ task processes videos asynchronously
- Progress tracking works in Redis
- Error handling and retries work correctly

### Frontend Components

#### Task Group 3: Transcript UI Components
**Dependencies:** Task Group 2

- [x] 3.0 Complete UI components
  - [x] 3.1 Write 2-8 focused tests for transcript components
    - Test TranscriptPanel fetches and displays transcript
    - Test TranscriptPanel handles loading and error states
    - Test TranscriptDisplay highlights current word based on currentTime
    - Test TranscriptDisplay click-to-seek functionality
    - Test TranscriptSearch filters words in real-time
    - Test TranscriptionProgress polls and displays progress
    - Test TranscriptExport downloads SRT/VTT files
  - [x] 3.2 Create TypeScript type definitions
    - Define Transcript interface (id, video_id, full_text, word_timestamps, language, status, accuracy_score, timestamps)
    - Define TranscriptStatus type ('processing' | 'completed' | 'failed')
    - Define TranscriptProgress interface (progress, status, estimated_time_remaining)
    - Define WordTimestamp interface (word, start, end, confidence)
    - Create file: `frontend/src/types/transcript.ts`
  - [x] 3.3 Create frontend API client functions
    - getTranscript(videoId): Fetches transcript data, returns Promise<Transcript>
    - triggerTranscription(videoId): Manually triggers transcription, returns Promise<void>
    - getTranscriptionProgress(videoId): Fetches progress data, returns Promise<TranscriptProgress>
    - exportTranscript(videoId, format): Exports transcript as blob, returns Promise<Blob>
    - downloadTranscript(blob, filename): Creates download link and triggers download
    - All functions use apiClient with proper error handling and TypeScript types
    - Create or update: `frontend/src/lib/api.ts` or similar
  - [x] 3.4 Create TranscriptPanel component (main container)
    - Client component ('use client') managing overall transcript state and layout
    - Props: videoId (string), currentTime (number, optional), onSeek (function, optional)
    - State management: transcript (Transcript | null), searchQuery, isLoading, error, status
    - useEffect hook to fetch transcript on videoId change
    - Conditional rendering: loading state, error state, processing state, or transcript display
    - Integration with child components: TranscriptDisplay, TranscriptSearch, TranscriptionProgress, TranscriptExport
    - Error handling: 404 handling for missing transcripts (treats as processing), other errors displayed
    - Auto-refetch: handleTranscriptComplete callback refetches transcript when processing completes
    - Create file: `frontend/src/components/TranscriptPanel.tsx`
  - [x] 3.5 Create TranscriptDisplay component
    - Client component displaying word-level transcript with interactive features
    - Props: transcript (Transcript), currentTime (number, optional), onWordClick (function, optional), searchQuery (string, optional)
    - Word highlighting: Highlights current word based on currentTime prop, auto-scrolls to keep highlighted word visible
    - Click-to-seek: Each word is clickable, calls onWordClick with word.start timestamp
    - Search highlighting: Highlights matching words with yellow background when searchQuery provided
    - Word rendering: Each word displayed as clickable span with hover effects, shows timestamp tooltip
    - Fallback display: Shows full_text if word_timestamps not available
    - Language and status display: Shows detected language and transcript status at top
    - Responsive layout: Flex-wrap layout for words, scrollable container
    - Create file: `frontend/src/components/TranscriptDisplay.tsx`
  - [x] 3.6 Create TranscriptSearch component
    - Client component providing search input with clear functionality
    - Props: onSearchChange (function), placeholder (string, optional)
    - Real-time search: Updates parent component immediately as user types
    - Clear button: X button appears when query exists, clears search on click
    - Shadcn/ui components: Uses Input and Button components with icons (Search, X from lucide-react)
    - Styling: Search icon on left, clear button on right, follows design system
    - Create file: `frontend/src/components/TranscriptSearch.tsx`
  - [x] 3.7 Create TranscriptionProgress component
    - Client component displaying transcription progress and status
    - Props: videoId (string), onComplete (function, optional), pollInterval (number, default 2000ms)
    - Polling mechanism: Polls getTranscriptionProgress API every pollInterval milliseconds
    - Progress display: Progress bar component showing percentage (0-100%), status text, percentage value
    - Estimated time: Displays estimated_time_remaining in minutes when available
    - Error handling: Displays error messages, stops polling on error
    - Retry functionality: Retry button appears on failure, triggers triggerTranscription API call
    - Status detection: Stops polling when progress reaches 100% or status includes "failed"
    - Completion callback: Calls onComplete when transcription completes successfully
    - Shadcn/ui components: Uses Progress, Button, AlertCircle icon from lucide-react
    - Create file: `frontend/src/components/TranscriptionProgress.tsx`
  - [x] 3.8 Create TranscriptExport component
    - Client component providing export functionality for SRT and VTT formats
    - Props: videoId (string), className (string, optional)
    - Export buttons: Two buttons for SRT and VTT export formats
    - Loading state: Disables buttons during export operation (isExporting state)
    - Download handling: Calls exportTranscript API, creates blob, triggers browser download
    - Error handling: Console error logging and alert on export failure
    - Filename generation: Creates filename with videoId and format extension
    - Shadcn/ui components: Uses Button component with Download icon from lucide-react
    - Create file: `frontend/src/components/TranscriptExport.tsx`
  - [x] 3.9 Ensure UI component tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify all components render correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 3.1 pass
- All components render correctly
- TranscriptPanel manages state and integrates child components
- TranscriptDisplay highlights words and supports click-to-seek
- TranscriptSearch filters words in real-time
- TranscriptionProgress polls and displays progress
- TranscriptExport downloads SRT/VTT files
- Video player integration works (onSeek callback, currentTime prop)

### Testing

#### Task Group 4: Test Review & Gap Analysis
**Dependencies:** Task Groups 1-3

- [x] 4.0 Review existing tests and fill critical gaps
  - [x] 4.1 Review tests from Task Groups 1-3
    - Review database layer tests (Task Group 1)
    - Review API layer tests (Task Group 2)
    - Review UI component tests (Task Group 3)
  - [x] 4.2 Analyze test coverage gaps
    - Identify missing edge cases
    - Identify missing integration tests
    - Identify missing error handling tests
    - Check coverage for all API endpoints
    - Check coverage for all UI components
  - [x] 4.3 Write up to 10 additional strategic tests
    - Integration tests for transcription workflow (upload → transcribe → retrieve)
    - Error handling tests (API failures, network errors, invalid data)
    - Edge case tests (empty transcripts, very long transcripts, special characters)
    - Performance tests (large transcripts, concurrent transcriptions)
    - End-to-end tests for transcript display and interaction
  - [x] 4.4 Run feature-specific tests only
    - Run all transcription-related tests
    - Verify all tests pass
    - Do NOT run the entire test suite

**Acceptance Criteria:**
- All tests from Task Groups 1-3 pass
- Additional strategic tests are written and pass
- Test coverage is comprehensive for transcription feature
- No critical gaps in test coverage

## Execution Order
1. Database Layer (Task Group 1)
2. Backend API Layer (Task Group 2)
3. Frontend Components (Task Group 3)
4. Test Review & Gap Analysis (Task Group 4)
