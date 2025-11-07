# Specification: Keyword Search & Clipping

## Goal
Enable users to search video transcripts for keywords, highlight matching segments, and create video clips from keyword matches with configurable context padding.

## User Stories
- As a content creator, I want to search my video transcript for keywords so that I can quickly find important moments
- As a user, I want to create clips from keyword matches so that I can extract highlights automatically

## Specific Requirements

**Clip Model & Database**
- Create Clip model with UUID primary key, video_id foreign key, start_time, end_time (float seconds)
- Store title, description (optional), keywords array (text[]), clip_url (S3 key)
- Include status enum: processing, completed, failed
- Add timestamps: created_at, updated_at
- Create database migration with indexes on video_id and keywords (GIN index for array search)

**Search Service**
- Full-text search in transcript using PostgreSQL full-text search capabilities
- Support multiple keywords with AND logic by default (all keywords must match)
- Fuzzy matching for typos (use PostgreSQL similarity or trigram)
- Return matching segments with start_time, end_time, and context
- Include ±5 seconds padding around matches by default (configurable)
- Highlight matching words in results
- Return relevance score for ranking results

**Clip Generation Service**
- Extract video segment from start_time to end_time using PyAV/FFmpeg
- Add configurable padding (±5 seconds default) around keyword match
- Generate clip file, upload to S3
- Create clip record in database with metadata
- Update clip status when generation completes
- Support generating multiple clips from search results

**Background Job Processing**
- Create ARQ task: generate_clip(clip_id: str) for async clip creation
- Download source video from S3, extract segment
- Upload clip to S3, update clip record
- Track progress in Redis for each clip individually
- Handle errors with retry logic

**Search & Clip API Endpoints**
- POST /api/videos/{id}/search: Search transcript with keywords array, return matching segments with timestamps
- POST /api/videos/{id}/clips: Create clip from time range (start_time, end_time, title, keywords)
- GET /api/videos/{id}/clips: List all clips for a video
- GET /api/clips/{id}: Get clip details including status and URL
- DELETE /api/clips/{id}: Delete clip record and S3 file
- GET /api/clips/{id}/progress: Get clip generation progress

**Keyword Search Component**
- Search input field supporting multiple keywords (comma-separated)
- Similar to TranscriptSearch component pattern
- AND logic by default (all keywords must match)
- Real-time search as user types (debounced)
- Search button or auto-search on Enter key
- Clear search button (X icon)

**Search Results Display**
- List of matching segments with timestamps (start/end times)
- Transcript excerpt showing context around match
- Highlight matching words in excerpt (similar to TranscriptDisplay highlighting)
- Display relevance score or match count
- Click result to seek video to that timestamp (onWordClick pattern)
- Show total number of matches found
- Empty state: "No matches found" message

**Clip Creation UI**
- Multi-select checkboxes next to each search result
- "Create Clips" button (disabled if no results selected)
- Clip creation modal or panel showing selected segments
- For each selected segment: show start/end times with ± buttons to adjust
- Default ±5 seconds padding displayed and editable
- Direct input fields for precise start/end time adjustment
- Title input field for each clip (required)
- Description input field (optional)
- Preview clip range on timeline (React-Konva visualization)
- "Create Clips" button triggers background jobs

**Clips Management Interface**
- Separate panel/section for clips (sidebar or tab)
- Grid view for clips with thumbnails (placeholder initially)
- List view toggle option
- Each clip card shows: thumbnail, title, duration, keywords, creation date
- Status badge (processing, completed, failed)
- Action buttons: Preview, Download, Delete
- Filter clips by keywords or date
- Sort by date, name, duration

**Clip Preview & Timeline Integration**
- Show clip range on timeline with visual indicators (React-Konva)
- Allow trimming start/end points before creation
- Display clip duration estimate
- Show which keywords matched in this clip
- Timeline visualization sufficient (video preview player optional)

**Clip Generation Progress**
- Individual progress tracking for each clip being generated
- Reuse TranscriptionProgress component pattern
- Polling every 2 seconds for each clip
- Progress indicator in clips list showing percentage
- Status updates: "Processing...", "Completed", "Failed"
- Error display with retry button for failed clips

**Clip Actions**
- Preview clip in video player (when completed)
- Download individual clips
- Delete clips with confirmation dialog (Shadcn/ui Dialog)
- Show clip metadata on hover or in details view

**Frontend Component Specifications**

**KeywordSearchComponent (Client Component)**
- Props: videoId (string), onResultsChange (function), onResultClick (function)
- State: searchQuery (string), isSearching (boolean), results (SearchResult[])
- Features: Comma-separated keyword input, debounced search (300ms), Enter key to search, clear button
- API: Calls searchTranscript(videoId, keywords) on search
- Shadcn/ui: Input component with Search icon, Button for clear

**SearchResultsList Component (Client Component)**
- Props: results (SearchResult[]), onResultClick (function), onResultSelect (function)
- State: selectedResults (Set<string>)
- Features: Checkbox selection, click to seek, highlighted matches, relevance score display
- Rendering: Scrollable list, empty state, loading state
- Integration: Calls onResultClick with timestamp, onResultSelect with result ID

**ClipCreationPanel Component (Client Component)**
- Props: selectedResults (SearchResult[]), videoId (string), onClipCreated (function)
- State: clipSettings (ClipSettings[]), isCreating (boolean)
- Features: Time adjustment (± buttons, direct input), title/description inputs, timeline preview
- Validation: Required title, valid time ranges, at least one result selected
- API: Calls createClip for each selected result

**ClipsManagementPanel Component (Client Component)**
- Props: videoId (string), clips (Clip[]), onClipDelete (function)
- State: viewMode ('grid' | 'list'), filterQuery (string), sortBy (string)
- Features: Grid/list toggle, filter by keywords, sort by date/name/duration, delete with confirmation
- API: Calls getClips, deleteClip, downloadClip
- Progress: Shows ClipProgressIndicator for each processing clip

**ClipProgressIndicator Component (Client Component)**
- Props: clipId (string), videoId (string), onComplete (function, optional)
- State: progress (ClipProgress | null), isPolling (boolean)
- Features: Polls getClipProgress every 2s, shows percentage and status, retry on error
- Pattern: Reuses TranscriptionProgress component pattern

**Frontend API Client Functions (TypeScript)**
- searchTranscript(videoId: string, keywords: string[]): Promise<SearchResult[]>
- createClip(videoId: string, settings: ClipCreationSettings): Promise<Clip>
- getClips(videoId: string): Promise<Clip[]>
- getClip(clipId: string): Promise<Clip>
- deleteClip(clipId: string): Promise<void>
- getClipProgress(clipId: string): Promise<ClipProgress>
- downloadClip(clipId: string): Promise<Blob>
- All functions use apiClient with error handling

**TypeScript Type Definitions**
- SearchResult: { id: string, start_time: number, end_time: number, transcript_excerpt: string, relevance_score: number, matched_keywords: string[] }
- Clip: { id: string, video_id: string, start_time: number, end_time: number, title: string, description?: string, keywords: string[], clip_url?: string, status: ClipStatus, duration: number, created_at: string }
- ClipProgress: { progress: number, status: string, estimated_time_remaining?: number }
- ClipStatus: 'processing' | 'completed' | 'failed'
- Types defined in frontend/src/types/clip.ts

## Visual Design
No visual assets provided. Follow Shadcn/ui design system for search input, results list, clip cards, buttons, and progress components.

## Existing Code to Leverage

**Frontend Search Components**
- Search input: Reuse `frontend/src/components/transcript/TranscriptSearch.tsx` pattern for keyword input
- Results highlighting: Reference `frontend/src/components/transcript/TranscriptDisplay.tsx` for word highlighting patterns
- Click to seek: Use same onWordClick pattern from TranscriptDisplay

**Frontend Progress Tracking**
- Progress component: Reuse `frontend/src/components/ui/progress.tsx`
- Progress pattern: Follow `frontend/src/components/transcript/TranscriptionProgress.tsx` for polling and state management
- Individual progress: Show progress for each clip in clips list

**Frontend Components**
- Button component: Use `frontend/src/components/ui/button.tsx` for all buttons
- Dialog component: Use @radix-ui/react-dialog for confirmation dialogs
- Card component: Use Shadcn/ui Card for clip cards in grid view

**Timeline Integration**
- Use React-Konva (already in package.json) for timeline visualization
- Reference timeline-editor spec for React-Konva patterns
- Use same visual indicator patterns for clip range marking

**Backend Patterns**
- Follow ARQ worker setup pattern from automatic-transcription and silence-removal specs
- Use Redis for progress tracking similar to other async tasks
- Use PyAV/FFmpeg patterns from silence-removal spec for video processing
- Follow S3 storage patterns from video-upload spec

**Database Patterns**
- Use SQLModel async patterns from existing models
- Follow GIN index pattern for array search on keywords
- Use PostgreSQL full-text search capabilities

**API Route Structure**
- Follow FastAPI router pattern from existing routes
- Use get_current_user dependency for authenticated endpoints
- Implement same async/await patterns for database operations
- Use Pydantic schemas for request/response validation

## Out of Scope
- Search across multiple videos (single video search only)
- Explicit AND/OR logic toggle in UI (AND by default, backend supports OR)
- Clip templates or presets (manual clip creation only)
- Batch generation from all search results (select individually)
- Clip sharing or public URLs (private clips only)
- Clip editing after creation (regenerate if needed)
- Clip collections or playlists (post-MVP feature)
- Search history or saved searches (future enhancement)
- Clip export in multiple formats (MP4 only)
- Video preview player for clips before creation (timeline visualization sufficient)
- "Did you mean" suggestions for fuzzy matching (show results directly)
