# Spec Requirements: Automatic Transcription

## Initial Description

Automatically transcribe uploaded videos using OpenAI Whisper API with word-level timestamps, language detection, and export capabilities. Transcription happens asynchronously via background jobs after video upload.

## Requirements Summary

### Functional Requirements

**Backend:**
- Transcript model with video relationship, word-level timestamps, language detection
- OpenAI Whisper API integration for speech-to-text
- ARQ background job for async transcription processing
- Audio extraction from video using PyAV
- Progress tracking in Redis
- API endpoints for transcript retrieval, manual triggering, and export

**Frontend:**
- TranscriptPanel component: Main container managing transcript state, loading, error handling, and conditional rendering
- TranscriptDisplay component: Word-level highlighting synchronized with video playback, click-to-seek functionality, search highlighting
- TranscriptSearch component: Search input with clear button, real-time filtering
- TranscriptionProgress component: Progress bar, status messages, estimated time remaining, retry functionality, polling every 2 seconds
- TranscriptExport component: Export buttons for SRT/VTT formats, download handling
- API client functions: getTranscript, triggerTranscription, getTranscriptionProgress, exportTranscript, downloadTranscript
- TypeScript types: Transcript, TranscriptStatus, TranscriptProgress, WordTimestamp interfaces
- State management: React hooks for transcript state, loading states, error handling
- Video player integration: onSeek callback for word clicks, currentTime prop for sync
- Error handling: 404 handling for missing transcripts, error display with retry options
- Loading states: Loading indicators during transcript fetch and export operations

### Dependencies
- Video Upload feature must be complete
- ARQ Worker must be set up
- OpenAI API key configured

### Technical Considerations
- Handle long videos by chunking (Whisper 25MB limit)
- Support languages: English, Russian, Spanish, German, French
- Word-level timestamps stored as JSONB
- Full-text search index on transcript text
- Retry logic with max 3 attempts

### Scope Boundaries
**In Scope:** Automatic transcription, word timestamps, language detection, export SRT/VTT, progress tracking
**Out of Scope:** Manual editing, speaker identification, real-time transcription, translation, batch processing

