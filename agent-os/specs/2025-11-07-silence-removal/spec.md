# Specification: Silence Removal

## Goal
Automatically detect and remove silent segments from videos with configurable threshold and minimum duration settings, providing preview before applying changes.

## User Stories
- As a content creator, I want to remove silent pauses from my videos so that my content is more engaging and concise
- As a user, I want to preview silence removal before applying it so that I can adjust settings if needed

## Specific Requirements

**Audio Analysis Service**
- Extract audio track from video using PyAV
- Analyze audio to detect silent segments using audio energy analysis
- Configurable silence threshold: -40dB default, adjustable range -60dB to -20dB
- Minimum silence duration: 1 second default, adjustable 0.5s to 5s
- Return list of silent segments with start_time, end_time, and duration
- Store detected segments for preview functionality

**Video Processing Service**
- Remove detected silent segments from video using FFmpeg/PyAV
- Re-encode video maintaining original quality settings
- Ensure audio and video remain synchronized after removal
- Generate new video file and upload to S3
- Update video record with new S3 key and duration
- Preserve original video for undo capability (store in separate S3 location)

**Background Job Processing**
- Create ARQ task: remove_silence(video_id: str, threshold: int, min_duration: float, excluded_segments: list)
- Download video from S3, extract audio, detect silence
- Process video to remove selected silent segments, re-encode
- Upload processed video to S3, update database
- Track progress in Redis (0-100%) with processing stages
- Handle errors gracefully with retry logic

**Silence Removal API Endpoints**
- POST /api/videos/{id}/remove-silence: Trigger silence removal with parameters (threshold, min_duration, excluded_segments array)
- GET /api/videos/{id}/silence-segments: Get detected silent segments without applying removal (for preview)
- GET /api/videos/{id}/silence-removal/progress: Get processing progress percentage and current stage

**Remove Silence Button & Modal**
- "Remove Silence" button in video editor toolbar (near Export/Search controls)
- Button opens Shadcn/ui Dialog modal with settings and preview
- Modal header: "Remove Silence" with close button
- Modal footer: Preview, Apply, and Cancel buttons

**Settings Modal - Threshold Configuration**
- Threshold slider using @radix-ui/react-slider component (-60dB to -20dB range)
- Current threshold value display (e.g., "-40 dB")
- Preset buttons: "Sensitive" (-60dB), "Normal" (-40dB), "Aggressive" (-20dB)
- Slider updates when preset is clicked, presets highlight when selected
- Minimum duration input field (number input, 0.5s to 5s, default 1s)
- Input validation with error messages for invalid values

**Preview Functionality**
- Preview button triggers silence detection API call
- Show detected segments as interactive list with checkboxes
- Each segment shows: start time, end time, duration, checkbox for exclusion
- Checkboxes default to checked (will be removed), unchecked = exclude from removal
- Timeline visualization with silent segments marked as gray bars/markers (React-Konva)
- Interactive markers: click to seek video, hover shows tooltip with details
- Before/after comparison: "Original: 5:23" vs "After removal: 4:15" with percentage reduction (e.g., "17% shorter")
- Estimated file size change display (optional, nice-to-have)

**Progress Tracking Component**
- Reuse TranscriptionProgress component pattern with polling every 2 seconds
- Display processing stages: "Detecting silence...", "Removing segments...", "Re-encoding...", "Uploading..."
- Show progress percentage (0-100%) with Progress bar component
- Estimated time remaining calculation and display
- Cancel button during processing (if possible)
- Error display with toast notification (Shadcn/ui Toast) and retry button
- Always preserve original video - failed processing doesn't affect original

**Timeline Integration**
- Mark silent segments on timeline with visual indicators (gray bars or markers using React-Konva)
- Interactive markers: click to seek to timestamp, hover for tooltip
- Show which segments will be removed (checked) vs excluded (unchecked)
- Update timeline after processing completes to show new video duration
- Visual distinction between detected segments and processed video

**Error Handling**
- Toast notifications for errors using Shadcn/ui Toast component
- Clear error messages explaining what went wrong
- Retry button to restart processing without re-uploading
- Original video always preserved regardless of processing status

## Visual Design
No visual assets provided. Follow Shadcn/ui design system for Dialog modal, Slider component, Progress component, Button components, and Toast notifications.

## Existing Code to Leverage

**Frontend Components**
- Dialog component: Use @radix-ui/react-dialog (already in package.json) - create Shadcn/ui Dialog wrapper if needed
- Slider component: Use @radix-ui/react-slider (already in package.json) for threshold slider
- Progress component: Reuse `frontend/src/components/ui/progress.tsx` for progress tracking
- Button component: Use `frontend/src/components/ui/button.tsx` for all buttons
- Toast component: Use @radix-ui/react-toast (already in package.json) for error notifications
- Progress tracking pattern: Follow `frontend/src/components/transcript/TranscriptionProgress.tsx` for polling and state management

**Timeline Visualization**
- Use React-Konva (already in package.json) for timeline markers and visualization
- Reference timeline-editor spec for React-Konva patterns and segment marking
- Use same visual indicator patterns for segment marking

**Backend Patterns**
- Follow ARQ worker setup pattern from automatic-transcription spec
- Use Redis for progress tracking similar to transcription jobs
- Follow same error handling and retry patterns
- Use PyAV for video/audio manipulation (from tech stack)
- Follow FFmpeg patterns for video encoding
- Reference video storage patterns from video-upload spec

**API Route Structure**
- Follow FastAPI router pattern from existing routes
- Use get_current_user dependency for authenticated endpoints
- Implement same async/await patterns for database operations
- Use Pydantic schemas for request/response validation

**Configuration Management**
- Use default_silence_threshold_db and default_min_silence_duration_ms from Settings
- Follow same config pattern for processing parameters

## Out of Scope
- Batch processing multiple videos (post-MVP feature)
- Fade in/out effects on cuts (hard cuts only)
- Custom silence detection algorithms (use standard audio energy analysis)
- Real-time preview playback (show segments only, no video playback)
- Undo/redo beyond single operation (single undo via original video preservation)
- Processing during upload (separate operation after upload completes)
- Export settings as preset (future enhancement)
- Advanced audio filtering or noise reduction (basic silence detection only)
- Multiple threshold profiles (single configurable threshold with presets)
