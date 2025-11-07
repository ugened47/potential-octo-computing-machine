# Spec Requirements: Video Export

## Initial Description

Enable users to export edited videos in multiple resolutions and quality settings, supporting both individual clips and combined videos from selected segments.

## Requirements Summary

### Functional Requirements

**Backend:**
- Export model with settings and status tracking
- Export service (combine segments, re-encode, upload)
- ARQ background job for async export processing
- API endpoints for export management and download

**Frontend:**
- Export modal with settings (resolution, quality, single/multiple)
- Export progress tracking with real-time updates
- Download functionality (single video or ZIP for multiple clips)
- Export history interface

### Dependencies
- Timeline Editor feature must be complete
- Video Upload feature must be complete
- ARQ Worker must be set up

### Technical Considerations
- Resolution options: 720p, 1080p
- Quality presets: High (CRF 18), Medium (CRF 23), Low (CRF 28)
- Format: MP4 (H.264, AAC)
- Support single combined video or multiple clips (ZIP)
- Progress tracking via SSE or polling

### Scope Boundaries
**In Scope:** Export with resolution/quality settings, progress tracking, download
**Out of Scope:** Custom formats, watermarks, subtitles, custom bitrates, audio-only, GIF export

