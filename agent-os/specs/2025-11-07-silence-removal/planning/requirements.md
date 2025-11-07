# Spec Requirements: Silence Removal

## Initial Description

Automatically detect and remove silent segments from videos with configurable threshold and minimum duration settings, providing preview before applying changes.

## Requirements Discussion

### First Round Questions

**Q1:** For the settings modal, I'm assuming we'll use Shadcn/ui Dialog component with a threshold slider (using @radix-ui/react-slider) and a number input for minimum duration. Should the modal be triggered by a button in the video editor toolbar, or should it be accessible from a different location?

**Answer:** The settings modal should be triggered by a "Remove Silence" button in the video editor toolbar, positioned near other editing controls like "Export" or "Search Keywords".

**Q2:** For the threshold slider, I'm assuming we'll display it with labels showing the range (-60dB to -20dB) and current value, with the default at -40dB. Should we include preset buttons (e.g., "Sensitive", "Normal", "Aggressive") or just the slider?

**Answer:** Include both the slider with current value display AND preset buttons for quick selection. Presets: "Sensitive" (-60dB), "Normal" (-40dB), "Aggressive" (-20dB). The slider should update when a preset is clicked.

**Q3:** For preview functionality, I'm assuming we'll show detected silent segments as a list with timestamps (start/end times) and duration, plus visualize them on the timeline. Should users be able to manually exclude specific segments from removal by clicking checkboxes, or should all detected segments be removed together?

**Answer:** Users should be able to manually exclude specific segments by clicking checkboxes next to each segment in the preview list. This gives them control over which silences to remove.

**Q4:** For the timeline visualization, I'm assuming we'll mark silent segments with gray bars or markers on the timeline (using React-Konva). Should these markers be interactive (click to seek, hover to see details), or just visual indicators?

**Answer:** Silent segment markers should be interactive - clicking a marker seeks to that timestamp, and hovering shows a tooltip with start/end time and duration. This helps users understand what will be removed.

**Q5:** For the before/after comparison, I'm assuming we'll show side-by-side duration information (e.g., "Original: 5:23" vs "After removal: 4:15"). Should we also show a percentage reduction or estimated file size change?

**Answer:** Show both duration comparison AND percentage reduction (e.g., "17% shorter"). File size estimation is nice-to-have but not critical for MVP.

**Q6:** For progress tracking during processing, I'm assuming we'll use the same Progress component pattern from TranscriptionProgress with polling every 2 seconds. Should we show processing stages (e.g., "Detecting silence...", "Removing segments...", "Re-encoding...") or just a percentage?

**Answer:** Show both processing stages AND percentage. Use the same polling pattern as TranscriptionProgress component, displaying current stage and progress percentage.

**Q7:** For error handling, I'm assuming we'll show error messages in a toast notification (using Shadcn/ui Toast) and provide a retry button. Should failed processing attempts preserve the original video, or should users need to re-upload?

**Answer:** Always preserve the original video. Failed processing should not affect the original, and users can retry without re-uploading. Show clear error messages with retry option.

**Q8:** What features should be explicitly excluded from this spec? For example, batch processing multiple videos, fade in/out effects on cuts, custom silence detection algorithms, or real-time preview playback?

**Answer:** Exclude: batch processing multiple videos, fade in/out effects (hard cuts only), custom detection algorithms (use standard audio energy analysis), real-time preview playback (show segments only), undo/redo beyond single operation, processing during upload (separate operation), export settings as preset.

### Existing Code to Reference

**Similar Features Identified:**
- Progress tracking: `frontend/src/components/transcript/TranscriptionProgress.tsx` - Use same polling pattern and Progress component
- Modal patterns: Shadcn/ui Dialog component (already in package.json via @radix-ui/react-dialog)
- Slider component: @radix-ui/react-slider (already in package.json) for threshold slider
- Button components: `frontend/src/components/ui/button.tsx` - Use existing Button component
- Progress component: `frontend/src/components/ui/progress.tsx` - Use existing Progress component
- Timeline integration: Reference timeline-editor spec for React-Konva patterns
- Video processing: Backend patterns from automatic-transcription spec for ARQ jobs

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
- Audio analysis service (detect silent segments using PyAV/audio analysis)
- Video processing service (remove segments, re-encode with FFmpeg/PyAV)
- ARQ background job for async processing
- API endpoints for silence detection and removal
- Progress tracking in Redis
- Preserve original video for undo capability

**Frontend:**
- "Remove Silence" button in video editor toolbar
- Settings modal (Shadcn/ui Dialog) with threshold slider and min duration input
- Preset buttons for quick threshold selection (Sensitive, Normal, Aggressive)
- Preview functionality showing detected segments as interactive list
- Timeline visualization of silent segments (React-Konva markers)
- Checkbox selection to exclude specific segments from removal
- Before/after comparison showing duration and percentage reduction
- Progress tracking component (reuse TranscriptionProgress pattern)
- Processing stage indicators with percentage
- Error handling with toast notifications and retry button
- Interactive timeline markers (click to seek, hover for details)

### Reusability Opportunities

- Frontend: Reuse Progress component, Button component, Dialog component from Shadcn/ui
- Frontend: Follow TranscriptionProgress polling pattern for progress updates
- Frontend: Use React-Konva for timeline visualization (from timeline-editor spec)
- Backend: Follow ARQ worker patterns from automatic-transcription spec
- Backend: Use Redis progress tracking similar to transcription jobs
- Backend: Follow video processing patterns from video-upload spec

### Scope Boundaries

**In Scope:**
- Silence detection with configurable threshold and minimum duration
- Preview functionality with segment list and timeline visualization
- Manual segment exclusion via checkboxes
- One-click application with progress tracking
- Before/after duration comparison
- Preserve original video for undo
- Interactive timeline markers

**Out of Scope:**
- Batch processing multiple videos
- Fade in/out effects (hard cuts only)
- Custom silence detection algorithms
- Real-time preview playback
- Undo/redo beyond single operation
- Processing during upload (separate operation)
- Export settings as preset
- Advanced audio filtering or noise reduction

### Technical Considerations

- Use Shadcn/ui Dialog for settings modal
- Use @radix-ui/react-slider for threshold slider
- Use React-Konva for timeline visualization (from timeline-editor spec)
- Follow TranscriptionProgress component pattern for progress tracking
- Polling interval: 2 seconds (same as transcription)
- Preserve original video in separate S3 location
- Use PyAV for audio analysis and video processing
- Follow ARQ background job patterns from transcription feature
- Use Redis for progress tracking
- Error handling with toast notifications (Shadcn/ui Toast)
