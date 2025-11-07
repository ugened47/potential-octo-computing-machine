# Spec Requirements: Keyword Search & Clipping

## Initial Description

Enable users to search video transcripts for keywords, highlight matching segments, and create video clips from keyword matches with configurable context padding.

## Requirements Discussion

### First Round Questions

**Q1:** For the keyword search input, I'm assuming we'll use a search input field (similar to TranscriptSearch component) that supports multiple keywords separated by commas or entered as tags. Should we support AND/OR logic operators in the UI, or just search for all keywords together (AND by default)?

**Answer:** Support multiple keywords with AND logic by default (all keywords must match). For MVP, no explicit AND/OR toggle in UI - just comma-separated keywords. Backend can support OR logic but UI will default to AND.

**Q2:** For search results display, I'm assuming we'll show a list of matching segments with timestamps, transcript excerpts, and relevance indicators. Should users be able to click a result to seek the video to that timestamp, similar to transcript word clicking?

**Answer:** Yes, clicking a search result should seek the video to that timestamp. Show transcript excerpt with matching words highlighted, timestamp, and relevance score or match count.

**Q3:** For clip creation, I'm assuming users can select multiple search results (checkboxes) and create clips from them. Should we allow users to adjust the start/end times before creating clips, or use the default ±5 seconds padding automatically?

**Answer:** Show default ±5 seconds padding, but allow users to adjust start/end times with ± buttons or direct input before creating clips. Preview the clip range on timeline.

**Q4:** For the clips management interface, I'm assuming we'll show a list/grid of created clips with thumbnails, titles, and metadata. Should clips be displayed in a separate panel/section, or integrated into the main video editor view?

**Answer:** Show clips in a separate panel/section (like a sidebar or tab), but also allow quick access from the main editor. Grid view for clips with thumbnails (placeholder initially), title, duration, keywords, and creation date.

**Q5:** For clip preview before creation, I'm assuming we'll show the clip range on the timeline and allow trimming. Should we also show a small video preview player for the clip segment, or just timeline visualization?

**Answer:** Show clip range on timeline with visual indicators, and allow trimming. Video preview player is nice-to-have but not critical for MVP - timeline visualization is sufficient.

**Q6:** For fuzzy matching, I'm assuming the backend will handle typos and similar words. Should the frontend show suggestions for "Did you mean..." if no exact matches are found, or just show fuzzy results directly?

**Answer:** Show fuzzy results directly without "Did you mean" suggestions for MVP. Backend handles fuzzy matching, frontend just displays results.

**Q7:** For clip generation progress, I'm assuming we'll use the same progress tracking pattern as transcription (polling every 2 seconds). Should we show progress for each clip individually when generating multiple clips, or aggregate progress?

**Answer:** Show progress for each clip individually when generating multiple clips. Each clip should have its own progress indicator in the clips list.

**Q8:** What features should be explicitly excluded from this spec? For example, search across multiple videos, clip templates/presets, batch clip generation from all results, clip sharing, or clip editing after creation?

**Answer:** Exclude: search across multiple videos (single video search only), clip templates/presets, batch generation from all results (select individually), clip sharing/public URLs, clip editing after creation (regenerate if needed), clip collections/playlists, search history, clip export in multiple formats (MP4 only).

### Existing Code to Reference

**Similar Features Identified:**
- Search component: `frontend/src/components/transcript/TranscriptSearch.tsx` - Use similar search input pattern
- Progress tracking: `frontend/src/components/transcript/TranscriptionProgress.tsx` - Use same polling pattern for clip generation
- Transcript display: `frontend/src/components/transcript/TranscriptDisplay.tsx` - Reference for highlighting matching words
- Button components: `frontend/src/components/ui/button.tsx` - Use existing Button component
- Timeline integration: Reference timeline-editor spec for React-Konva patterns
- Video processing: Backend patterns from silence-removal spec for ARQ jobs

### Follow-up Questions

None needed - all requirements are clear.

## Visual Assets

### Files Provided:
No visual files found.

### Visual Insights:
No visual assets provided. Will follow Shadcn/ui design system and existing project styling patterns.

## Requirements Summary

### Functional Requirements

**Backend:**
- Clip model with video relationship, time ranges, keywords array
- Full-text search service in transcripts using PostgreSQL
- Fuzzy matching support for typos
- Clip generation service (extract segments with PyAV/FFmpeg, add padding)
- ARQ background job for async clip creation
- API endpoints for search and clip management
- Progress tracking in Redis

**Frontend:**
- Keyword search input component (comma-separated keywords, AND logic by default)
- Search results list with timestamps, transcript excerpts, highlighted matches
- Click result to seek video to timestamp
- Multi-select checkboxes for creating clips from multiple results
- Clip creation UI with start/end time adjustment (± buttons or direct input)
- Default ±5 seconds padding (configurable)
- Timeline preview of clip range
- Clips management interface (grid/list view with thumbnails)
- Individual progress tracking for each clip being generated
- Clip metadata display (title, duration, keywords, creation date)
- Delete clips with confirmation dialog

### Reusability Opportunities

- Frontend: Reuse TranscriptSearch component pattern for keyword input
- Frontend: Reuse TranscriptionProgress pattern for clip generation progress
- Frontend: Reuse TranscriptDisplay highlighting patterns for search results
- Frontend: Use React-Konva for timeline visualization (from timeline-editor spec)
- Backend: Follow ARQ worker patterns from transcription and silence-removal specs
- Backend: Use PostgreSQL full-text search with GIN index on keywords array
- Backend: Follow video processing patterns from silence-removal spec

### Scope Boundaries

**In Scope:**
- Keyword search in single video transcript
- Multiple keywords with AND logic (comma-separated)
- Fuzzy matching (backend handles)
- Search results with timestamps and highlighted matches
- Click result to seek video
- Create clips from selected search results
- Adjust clip start/end times with ±5s padding
- Timeline preview of clip range
- Clips management interface
- Individual clip progress tracking
- Delete clips

**Out of Scope:**
- Search across multiple videos
- Explicit AND/OR logic toggle in UI
- Clip templates or presets
- Batch generation from all results
- Clip sharing or public URLs
- Clip editing after creation
- Clip collections or playlists
- Search history or saved searches
- Clip export in multiple formats (MP4 only)
- Video preview player for clips (timeline visualization sufficient)

### Technical Considerations

- Use TranscriptSearch component pattern for keyword input
- Support comma-separated keywords (AND logic by default)
- Backend handles fuzzy matching, frontend displays results
- Use PostgreSQL full-text search with GIN index
- Default ±5 seconds padding, configurable via UI
- Use React-Konva for timeline visualization
- Follow TranscriptionProgress pattern for clip generation progress
- Polling interval: 2 seconds (same as transcription)
- Use PyAV/FFmpeg for clip extraction
- Follow ARQ background job patterns
- Use Redis for progress tracking
