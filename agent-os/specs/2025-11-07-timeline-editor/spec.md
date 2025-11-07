# Specification: Timeline Editor

## Goal
Provide a visual timeline editor with waveform display, transcript synchronization, segment selection, and video player integration for precise video editing.

## User Stories
- As a content creator, I want to see a visual timeline with waveform so that I can identify audio patterns and edit precisely
- As a user, I want to click transcript words to seek the video so that I can quickly navigate to specific moments

## Specific Requirements

**Timeline Component (React-Konva)**
- Canvas-based timeline visualization using React-Konva
- Display video track with duration scale (time markers)
- Show audio waveform using Wavesurfer.js integration
- Playhead/cursor showing current playback position
- Zoom controls (zoom in/out, fit to screen)
- Pan/drag timeline horizontally when zoomed in
- Responsive layout adapting to container size

**Audio Waveform Generation**
- Generate waveform data from video audio track (backend service)
- Use Wavesurfer.js format for waveform data (peaks array)
- Cache waveform data in S3 or database for performance
- Generate waveform asynchronously after video upload
- Support waveform regeneration if needed

**Segment Management**
- Visual segments on timeline representing selected video portions
- Select/deselect segments by clicking or dragging
- Drag segment edges to trim start/end points
- Reorder clips by dragging segments horizontally
- Visual distinction between selected and unselected segments
- Show segment duration and time range on hover

**Transcript Synchronization**
- Transcript panel synchronized with video playback
- Highlight current word during playback (word-level sync)
- Click transcript word to seek video to that timestamp
- Auto-scroll transcript to keep current word visible
- Visual connection between transcript and timeline (line or highlight)
- Word-level timestamps from transcript used for precise seeking

**Video Player Integration**
- Integrate Video.js or Remotion Player for video playback
- Play/pause controls synchronized with timeline
- Seek functionality updates playhead position
- Playback speed control (0.5x, 1x, 1.5x, 2x)
- Current time display matching timeline position
- Fullscreen support

**Timeline State Management**
- Store segment selections in component state (Zustand or React state)
- Calculate final video duration from selected segments
- Track playhead position for synchronization
- Manage zoom level and pan position
- Persist timeline state during session

**Waveform API Endpoints**
- GET /api/videos/{id}/waveform: Get waveform data (peaks array) for video
- POST /api/videos/{id}/waveform: Trigger waveform generation if not exists
- GET /api/videos/{id}/waveform/status: Check waveform generation status

**Segment API Endpoints**
- POST /api/videos/{id}/segments: Update segment selections (save timeline state)
- GET /api/videos/{id}/segments: Get saved segment selections
- DELETE /api/videos/{id}/segments: Clear all segment selections

**Timeline Controls**
- Play/pause button
- Seek backward/forward buttons (5s, 10s jumps)
- Zoom in/out buttons
- Fit to screen button
- Reset zoom button
- Time display (current time / total duration)

**Keyboard Shortcuts**
- Spacebar: Play/pause
- Left/Right arrows: Seek backward/forward (1s)
- Shift + Left/Right: Seek backward/forward (5s)
- +/-: Zoom in/out
- 0: Reset zoom
- Delete: Remove selected segment

**Frontend Component Specifications**

**TimelineEditor Component (Client Component)**
- Props: videoId (string), videoUrl (string), transcript (Transcript), segments (Segment[]), onSegmentChange (function)
- State: zoomLevel (number), panPosition (number), playheadPosition (number), selectedSegments (Set<string>)
- Features: React-Konva canvas, zoom/pan controls, playhead tracking, segment selection
- Integration: Receives currentTime from video player, calls onSeek when timeline clicked

**WaveformDisplay Component (Client Component)**
- Props: waveformData (number[]), duration (number), currentTime (number), onSeek (function)
- Features: Wavesurfer.js integration via @wavesurfer/react, displays audio waveform, click to seek
- State: isReady (boolean), peaks (number[])
- API: Calls getWaveform or generateWaveform if not exists

**VideoPlayer Component (Client Component)**
- Props: videoUrl (string), currentTime (number), onTimeUpdate (function), onSeek (function)
- Features: Video.js or Remotion Player integration, play/pause, seek, playback speed control
- State: isPlaying (boolean), playbackRate (number), duration (number)
- Integration: Provides currentTime to timeline, receives seek commands from timeline/transcript

**TimelineControls Component (Client Component)**
- Props: onPlayPause (function), onSeek (function), onZoom (function), currentTime (number), duration (number)
- Features: Play/pause button, seek buttons (±5s, ±10s), zoom controls, time display
- Shadcn/ui: Button components, time display formatting

**SegmentMarker Component (React-Konva)**
- Props: segment (Segment), zoomLevel (number), isSelected (boolean), onClick (function), onDrag (function)
- Features: Visual marker on timeline, click to select, drag to adjust, hover tooltip
- Rendering: Konva Rect or Group, color coding for selected/unselected

**Frontend API Client Functions (TypeScript)**
- getWaveform(videoId: string): Promise<WaveformData>
- generateWaveform(videoId: string): Promise<WaveformData>
- getWaveformStatus(videoId: string): Promise<WaveformStatus>
- saveSegments(videoId: string, segments: Segment[]): Promise<void>
- getSegments(videoId: string): Promise<Segment[]>
- deleteSegments(videoId: string): Promise<void>
- All functions use apiClient with error handling

**TypeScript Type Definitions**
- WaveformData: { peaks: number[], duration: number, sample_rate: number }
- Segment: { id: string, start_time: number, end_time: number, selected: boolean }
- WaveformStatus: { status: 'processing' | 'completed' | 'failed', progress?: number }
- Types defined in frontend/src/types/timeline.ts

**State Management**
- Timeline state: Use Zustand store for timeline state (zoom, pan, segments) or React state
- Video player state: Local component state for playback state
- Segment state: Managed in TimelineEditor component, synced with backend on save
- Integration: TimelineEditor coordinates between video player, transcript, and segments

**Keyboard Shortcut Handling**
- useKeyboardShortcuts hook: Custom hook for keyboard event handling
- Event listeners: Attached to timeline container, prevent default browser behavior
- Shortcut mapping: Maps key combinations to actions (play/pause, seek, zoom)

## Visual Design
No visual assets provided. Follow Shadcn/ui design system for controls and use React-Konva for timeline canvas.

## Existing Code to Leverage

**Video Player**
- Use Video.js (already in package.json) for video playback
- Reference Remotion Player as alternative if needed
- Follow video player patterns from project setup

**Waveform Library**
- Use Wavesurfer.js (already in package.json) for waveform visualization
- Use @wavesurfer/react wrapper for React integration
- Follow Wavesurfer.js documentation for peak data format

**Canvas Library**
- Use Konva and React-Konva (already in package.json) for timeline canvas
- Follow Konva patterns for interactive canvas elements
- Reference React-Konva documentation for component structure

**Transcript Integration**
- Reference Transcript model and display from automatic-transcription spec
- Use word_timestamps for precise synchronization
- Follow transcript display patterns from transcription feature

**Video Model**
- Reference Video model from video-upload spec
- Use video URL and metadata for player integration
- Follow same video access patterns

**API Route Structure**
- Follow FastAPI router pattern from existing routes
- Use get_current_user dependency for authenticated endpoints
- Implement same async/await patterns for database operations
- Use Pydantic schemas for request/response validation

**State Management**
- Use Zustand (already in package.json) for timeline state if needed
- Follow project's state management patterns
- Consider React state for component-local state

## Out of Scope
- Multi-track timeline (single video track only)
- Video effects or filters (basic trimming only)
- Audio mixing or separate audio tracks (single audio track)
- Keyframe animation (static segments only)
- Timeline markers or annotations (post-MVP feature)
- Export timeline as project file (save segments only)
- Collaborative editing (single user only)
- Timeline templates or presets (manual editing only)
- Undo/redo beyond browser session (session-only)
- Timeline scrubbing with preview (playhead movement only)

