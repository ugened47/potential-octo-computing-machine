# Specification: Automatic Transcription

## Goal
Automatically transcribe uploaded videos using OpenAI Whisper API with word-level timestamps, language detection, and export capabilities.

## User Stories
- As a content creator, I want my videos automatically transcribed so that I can search for specific moments and create clips
- As a user, I want to export transcripts as SRT/VTT files so that I can use them in other video editing tools

## Specific Requirements

**Transcript Model & Database**
- Create Transcript model with video_id foreign key, full_text (text field), word_timestamps (JSONB array)
- Store language code (ISO 639-1), status enum (processing, completed, failed), accuracy score (optional)
- Add timestamps: created_at, updated_at, completed_at
- Create database migration with index on video_id and full-text search index on full_text

**Transcription Service**
- Integrate OpenAI Whisper API for speech-to-text conversion
- Support languages: English, Russian, Spanish, German, French (detect automatically)
- Extract word-level timestamps from Whisper response (start_time, end_time, word, confidence)
- Handle long videos by chunking if needed (Whisper supports up to 25MB audio)
- Store transcript data in database after successful transcription
- Update video processing status when transcription completes

**Background Job Processing**
- Create ARQ task: transcribe_video(video_id: str) for async processing
- Download video from S3, extract audio track using PyAV
- Call Whisper API with audio file, process response
- Store transcript in database, update video status
- Track progress in Redis (0-100%) for real-time updates
- Implement error handling with retry logic (max 3 attempts)
- Handle API rate limits and quota exceeded errors gracefully

**Transcription API Endpoints**
- GET /api/videos/{id}/transcript: Get transcript with word timestamps, return 404 if not available
- POST /api/videos/{id}/transcribe: Manually trigger transcription (if not already processing/completed)
- GET /api/videos/{id}/transcript/export: Export transcript as SRT or VTT format (query param: format=srt|vtt)
- GET /api/videos/{id}/transcript/progress: Get transcription progress percentage (for SSE updates)

**TranscriptPanel Component (Main Container)**
- Client component ('use client') managing overall transcript state and layout
- Props: videoId (string), currentTime (number, optional), onSeek (function, optional)
- State management: transcript (Transcript | null), searchQuery, isLoading, error, status
- useEffect hook to fetch transcript on videoId change
- Conditional rendering: loading state, error state, processing state, or transcript display
- Integration with child components: TranscriptDisplay, TranscriptSearch, TranscriptionProgress, TranscriptExport
- Error handling: 404 handling for missing transcripts (treats as processing), other errors displayed
- Auto-refetch: handleTranscriptComplete callback refetches transcript when processing completes

**TranscriptDisplay Component**
- Client component displaying word-level transcript with interactive features
- Props: transcript (Transcript), currentTime (number, optional), onWordClick (function, optional), searchQuery (string, optional)
- Word highlighting: Highlights current word based on currentTime prop, auto-scrolls to keep highlighted word visible
- Click-to-seek: Each word is clickable, calls onWordClick with word.start timestamp
- Search highlighting: Highlights matching words with yellow background when searchQuery provided
- Word rendering: Each word displayed as clickable span with hover effects, shows timestamp tooltip
- Fallback display: Shows full_text if word_timestamps not available
- Language and status display: Shows detected language and transcript status at top
- Responsive layout: Flex-wrap layout for words, scrollable container

**TranscriptSearch Component**
- Client component providing search input with clear functionality
- Props: onSearchChange (function), placeholder (string, optional)
- Real-time search: Updates parent component immediately as user types
- Clear button: X button appears when query exists, clears search on click
- Shadcn/ui components: Uses Input and Button components with icons (Search, X from lucide-react)
- Styling: Search icon on left, clear button on right, follows design system

**TranscriptionProgress Component**
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

**TranscriptExport Component**
- Client component providing export functionality for SRT and VTT formats
- Props: videoId (string), className (string, optional)
- Export buttons: Two buttons for SRT and VTT export formats
- Loading state: Disables buttons during export operation (isExporting state)
- Download handling: Calls exportTranscript API, creates blob, triggers browser download
- Error handling: Console error logging and alert on export failure
- Filename generation: Creates filename with videoId and format extension
- Shadcn/ui components: Uses Button component with Download icon from lucide-react

**Frontend API Client Functions**
- getTranscript(videoId): Fetches transcript data, returns Promise<Transcript>
- triggerTranscription(videoId): Manually triggers transcription, returns Promise<void>
- getTranscriptionProgress(videoId): Fetches progress data, returns Promise<TranscriptProgress>
- exportTranscript(videoId, format): Exports transcript as blob, returns Promise<Blob>
- downloadTranscript(blob, filename): Creates download link and triggers download
- All functions use apiClient with proper error handling and TypeScript types

**TypeScript Type Definitions**
- Transcript interface: id, video_id, full_text, word_timestamps, language, status, accuracy_score, timestamps
- TranscriptStatus type: 'processing' | 'completed' | 'failed'
- TranscriptProgress interface: progress (number), status (string), estimated_time_remaining (number, optional)
- WordTimestamp interface: word (string), start (number), end (number), confidence (number, optional)
- All types defined in frontend/src/types/transcript.ts

**Video Player Integration**
- onSeek callback: Parent component provides callback function to seek video to timestamp
- currentTime prop: Video player provides current playback time for word highlighting sync
- Bidirectional sync: Transcript highlights word during playback, clicking word seeks video
- Integration pattern: TranscriptPanel receives currentTime and onSeek from video player component

**ARQ Worker Setup**
- Configure ARQ worker with Redis connection from settings
- Register transcribe_video task in worker.py
- Set up worker to process jobs from queue
- Implement worker health checks and monitoring

## Visual Design
No visual assets provided. Follow Shadcn/ui design system for transcript panel and progress indicators.

## Existing Code to Leverage

**Background Job Pattern**
- Follow ARQ worker setup pattern from app.worker (when implemented)
- Use Redis for progress tracking similar to other async tasks
- Follow same error handling and retry patterns for background jobs

**API Route Structure**
- Follow FastAPI router pattern from app.api.routes.auth
- Use get_current_user dependency for authenticated endpoints
- Implement same async/await patterns for database operations
- Use Pydantic schemas for request/response validation

**Database Patterns**
- Use SQLModel async patterns from User model for Transcript model
- Follow same migration structure with Alembic
- Use JSONB field for word_timestamps similar to other JSON data storage

**Video Model Integration**
- Reference Video model from video-upload spec for foreign key relationship
- Update Video model to include transcript relationship
- Follow same status enum pattern for processing states

## Out of Scope
- Manual transcript editing/correction (post-MVP feature)
- Multiple speaker identification and labeling (future enhancement)
- Real-time transcription during upload (only post-upload processing)
- Custom vocabulary or terminology (use Whisper defaults)
- Transcript translation (post-MVP feature)
- Batch transcription of multiple videos (post-MVP feature)
- Transcript confidence threshold filtering (use all words)
- Custom timestamp precision (use Whisper's word-level precision)
- Transcript versioning/history (single transcript per video)
- Speaker diarization (identifying who said what)

