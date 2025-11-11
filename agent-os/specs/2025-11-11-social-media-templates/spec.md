# Specification: Social Media Templates

## Goal
Enable one-click export of videos optimized for social media platforms (YouTube Shorts, TikTok, Instagram Reels) with automatic aspect ratio conversion, duration trimming, and platform-specific caption styling to help creators repurpose long-form content into engaging short-form clips.

## User Stories
- As a content creator, I want to export my video as a YouTube Short with one click so that I can quickly repurpose my content for YouTube's short-form platform
- As a TikTok creator, I want my video automatically converted to 9:16 aspect ratio and trimmed to 60 seconds so that I don't have to manually edit for platform requirements
- As a social media manager, I want captions automatically added in platform-specific styles so that my videos are accessible and engaging without manual subtitle work
- As a user, I want to preview how my video will look on each platform before exporting so that I can ensure it meets my quality standards
- As a podcaster, I want to select which segment of my video to export for each platform so that I can create platform-optimized clips from longer content

## Specific Requirements

### Template Model & Database
- Create SocialMediaTemplate model with platform enum ('youtube_shorts', 'tiktok', 'instagram_reels', 'custom')
- Platform constraints: aspect_ratio (string, e.g., '9:16', '16:9', '1:1'), max_duration_seconds (integer)
- Caption configuration: auto_captions (boolean), caption_style (JSON containing font, size, color, position, background)
- Style presets: style_preset enum ('minimal', 'bold', 'gaming', 'podcast', 'vlog', 'custom')
- Export settings: video_codec (string, default 'h264'), audio_codec (string, default 'aac'), bitrate (string, default '5M')
- Metadata: name (string), description (text), is_system_preset (boolean), user_id (foreign key, nullable for system templates)
- Status: is_active (boolean), usage_count (integer)
- Timestamps: created_at, updated_at
- Create database migration with indexes on platform, user_id, is_active, is_system_preset
- Create VideoExport model tracking exports: video_id, template_id, export_url, status enum ('processing', 'completed', 'failed'), file_size, resolution, created_at

### Platform Configuration System
- Define system presets (non-editable by users):
  - **YouTube Shorts**: 9:16 aspect ratio, 60s max duration, bold captions at bottom-center, high energy style
  - **TikTok**: 9:16 aspect ratio, 60s max duration (180s for verified), bold animated captions, trendy style
  - **Instagram Reels**: 9:16 aspect ratio, 90s max duration, clean captions with background, aesthetic style
  - **Twitter/X Video**: 16:9 or 1:1 aspect ratio, 140s max duration, minimal captions
  - **LinkedIn Video**: 1:1 aspect ratio preferred, 600s max duration, professional captions, corporate style
- Platform-specific caption styles (JSON schema):
  - font_family: string (default per platform)
  - font_size: percentage of video height (3-8%)
  - font_weight: 'normal' | 'bold' | 'extra-bold'
  - text_color: hex color
  - background_color: hex color with alpha
  - stroke_color: hex color for text outline
  - stroke_width: integer pixels
  - position: 'top' | 'center' | 'bottom' with y_offset percentage
  - alignment: 'left' | 'center' | 'right'
  - animation: 'none' | 'fade' | 'slide' | 'pop' | 'word-by-word'
  - max_chars_per_line: integer (25-40 depending on platform)
  - max_lines: integer (2-3)
- Resolution presets per platform:
  - YouTube Shorts: 1080x1920 (Full HD)
  - TikTok: 1080x1920 (Full HD)
  - Instagram Reels: 1080x1920 (Full HD)
  - Square format: 1080x1080
- Bitrate and encoding settings per platform for optimal quality/size balance

### Video Transformation Service
- Create VideoTransformationService handling aspect ratio conversion
- Aspect ratio conversion strategies:
  - **Crop (Smart)**: Detect main subject (face detection, motion tracking) and crop to preserve important content
  - **Crop (Center)**: Center crop maintaining aspect ratio (simple, may lose content on edges)
  - **Scale (Letterbox)**: Scale video to fit, add letterbox bars (top/bottom for landscape, sides for portrait)
  - **Scale (Blur Background)**: Scale video to fit, use blurred version as background behind scaled video
  - **Pan & Zoom**: Intelligently pan and zoom to follow action (advanced, ML-based)
- Implement smart crop algorithm:
  - Use face detection (OpenCV or MediaPipe) to identify faces in frames
  - Track faces across frames to maintain consistent framing
  - If no faces, use motion detection to identify active areas
  - Calculate crop region that keeps most important content centered
  - Smooth crop transitions between frames (avoid jarring jumps)
- Implement blur background strategy:
  - Scale original video to fit within target aspect ratio
  - Apply Gaussian blur to upscaled version of same video
  - Composite scaled video on top of blurred background
  - Add subtle vignette for professional look
- Use PyAV or FFmpeg for video transformations
- Support hardware acceleration (NVENC, VideoToolbox) for faster processing
- Maintain video quality during transformations (use high-quality scaling algorithms)

### Duration Enforcement Service
- Create DurationEnforcementService handling duration limits
- Trimming strategies:
  - **Trim Start**: Keep last N seconds (e.g., last 60s for TikTok)
  - **Trim End**: Keep first N seconds (e.g., first 60s)
  - **Smart Trim**: Use highlight scores to keep best N seconds
  - **User Selection**: Allow user to manually select segment via timeline
  - **Multiple Segments**: Combine multiple short segments to reach duration (e.g., 3x 20s clips)
- Smart trim algorithm:
  - If highlights available, select highest-scoring continuous segment within duration limit
  - If no highlights, use audio energy analysis to find best segment
  - Prefer segments with speech over silent segments
  - Ensure selected segment is coherent (doesn't cut mid-sentence if possible)
- Handle edge cases:
  - Video shorter than limit: No trimming needed
  - Video exactly at limit: Minor trim to ensure under limit with buffer
  - Very long video: Show warning about automatic trimming, suggest manual selection
- Provide preview of trimmed result before final export
- Store trim metadata: original_duration, trimmed_duration, trim_start_time, trim_end_time

### Auto-Caption Overlay Service
- Create CaptionOverlayService for burning captions into video
- Use existing transcript data (word-level timestamps) from Whisper
- Caption rendering process:
  - Parse transcript into caption chunks (2-5 words per caption, based on platform style)
  - Calculate display timing: show caption for duration of words + buffer (0.1s)
  - Ensure captions don't overlap or flash too quickly (minimum 0.8s per caption)
  - Break long sentences into multiple captions at natural pauses
  - Apply platform-specific styling (font, color, position, animation)
- Text rendering with FFmpeg drawtext filter or Python imaging (PIL/Pillow):
  - Render text with specified font, size, color
  - Add background box with padding and corner radius
  - Add text outline/stroke for readability
  - Position on video according to style preset
  - Apply animations (fade in/out, word-by-word reveal)
- Caption positioning logic:
  - Bottom captions: y = video_height * 0.85 (avoid cutting off on mobile)
  - Center captions: y = video_height * 0.5
  - Top captions: y = video_height * 0.15
  - Safe zones: Avoid edges where platform UI elements appear
- Handle special cases:
  - Multiple speakers: Option to color-code captions per speaker
  - Long words: Auto-break words that exceed max width
  - Emoji support: Render emojis in captions if present in transcript
  - Punctuation: Handle commas, periods, exclamation for natural reading
- Performance optimization:
  - Cache rendered caption frames
  - Use GPU for video encoding if available
  - Render captions in parallel with video processing where possible
- Quality control:
  - Ensure captions are readable at mobile sizes (test at 1080x1920)
  - Verify caption timing matches audio (±0.1s accuracy)
  - Check caption contrast ratio for accessibility (WCAG AA compliance)

### Caption Style Presets
- **Minimal**: Small sans-serif font, white text with black outline, bottom position, no background, fade animation
- **Bold**: Large bold font, white text with yellow background box, bottom-center, pop animation per word
- **Gaming**: Bright colors (cyan/magenta), large bold font, center position, animated word-by-word with effects
- **Podcast**: Clean serif font, medium size, white text with dark semi-transparent background, center position
- **Vlog**: Friendly rounded font, medium size, colored text matching video palette, bottom position, slide-up animation
- **Professional**: Standard sans-serif, medium size, black text on white background, bottom position, simple fade
- **Trendy**: Modern font with style variations (outline, shadow), animated transitions, emojis highlighted
- Allow users to create custom presets:
  - Save custom font, color, position combinations
  - Name custom presets for reuse
  - Share presets with team members (for teams feature)

### Template Management API Endpoints
- GET /api/templates: List all templates
  - Query params: platform, is_system_preset, user_id, is_active
  - Returns paginated list of templates with usage stats
  - Include sample thumbnail for each template
- GET /api/templates/{id}: Get single template details
  - Returns full template configuration
  - Include example export preview
- POST /api/templates: Create custom template
  - Body: {name, platform, aspect_ratio, max_duration_seconds, caption_style, style_preset}
  - Validate aspect ratio format, duration limits
  - Return created template with id
- PATCH /api/templates/{id}: Update custom template
  - Only allow updating user-owned templates (not system presets)
  - Validate updates against platform constraints
- DELETE /api/templates/{id}: Delete custom template
  - Only allow deleting user-owned templates
  - Soft delete (set is_active = false)
- GET /api/templates/presets: Get system presets
  - Returns all platform presets (YouTube Shorts, TikTok, etc.)
  - Include platform requirements and constraints

### Video Export API Endpoints
- POST /api/videos/{id}/export: Create export with template
  - Body: {template_id, segment_start_time?, segment_end_time?, crop_strategy: 'smart' | 'center' | 'letterbox' | 'blur'}
  - Validates video exists and user has access
  - Validates segment times are within video duration
  - Enqueues export job (ARQ), returns job_id and export_id
  - Prevents duplicate exports (check if identical export already in progress)
- GET /api/videos/{id}/exports: List all exports for video
  - Query params: template_id, status, limit, offset
  - Returns exports sorted by created_at DESC
  - Include download URL for completed exports
- GET /api/exports/{id}: Get single export details
  - Returns export status, progress, file info
  - If completed, include download URL (presigned S3 URL, 1 hour expiration)
  - If failed, include error message and retry option
- DELETE /api/exports/{id}: Delete export
  - Remove from database and delete S3 file
  - Only allow deleting user's own exports
- GET /api/exports/{id}/progress: Get export progress
  - Returns {progress: 0-100, status, current_stage: string, estimated_time_remaining: seconds}
  - Stages: 'extracting', 'transforming', 'trimming', 'adding_captions', 'encoding', 'uploading'
- POST /api/exports/{id}/retry: Retry failed export
  - Re-enqueue export job with same configuration
  - Reset status to 'processing'

### Export Preview API Endpoints
- POST /api/videos/{id}/preview-export: Generate preview without full export
  - Body: {template_id, segment_start_time, segment_end_time, crop_strategy}
  - Generates quick low-quality preview (30s max, 720p)
  - Returns preview URL (temporary, expires in 1 hour)
  - Useful for testing template before full export
  - Cache previews for performance
- GET /api/templates/{id}/sample: Get template sample video
  - Returns sample export showing template style
  - System-generated samples for all presets
  - Helps users understand what template will look like

### Background Job Processing
- ARQ task: export_video_with_template(video_id, template_id, config)
- Export workflow:
  1. Download original video from S3
  2. Extract segment if specified (segment_start_time, segment_end_time)
  3. Apply aspect ratio transformation (crop/letterbox/blur based on strategy)
  4. Trim to platform duration limit if needed
  5. Generate captions and overlay on video
  6. Encode video with platform-specific settings
  7. Upload to S3 with unique filename
  8. Update VideoExport record with URL and metadata
  9. Track progress in Redis (0-100%)
  10. Clean up temporary files
- Progress tracking:
  - Stage 1 (Download): 0-10%
  - Stage 2 (Extract segment): 10-20%
  - Stage 3 (Transform aspect ratio): 20-40%
  - Stage 4 (Trim duration): 40-50%
  - Stage 5 (Add captions): 50-75%
  - Stage 6 (Encode): 75-95%
  - Stage 7 (Upload): 95-100%
- Error handling:
  - Retry logic for transient failures (S3 upload, network issues)
  - Max 3 retries with exponential backoff
  - Store error details in VideoExport record
  - Send error notification to user
- Performance optimization:
  - Use hardware acceleration for encoding (NVENC on GPU)
  - Process multiple exports in parallel (max 3 per user)
  - Limit concurrent exports globally (based on worker capacity)
- Job timeout: 20 minutes for standard videos, 40 minutes for long videos

### TemplateSelector Component
- Client component for selecting social media template
- Props: videoId (string), onTemplateSelect (function), selectedTemplateId (string, optional)
- Display system presets as cards with platform logos:
  - YouTube Shorts (red theme)
  - TikTok (black/cyan theme)
  - Instagram Reels (gradient theme)
  - Twitter/X (blue theme)
  - LinkedIn (blue professional theme)
- Each preset card shows:
  - Platform logo and name
  - Aspect ratio badge (9:16, 1:1, etc.)
  - Max duration badge (60s, 90s, etc.)
  - Caption style preview (small text sample)
  - "Use Template" button
- Show user's custom templates in separate section
- Create template button: Opens TemplateCreator dialog
- Template search and filter: By platform, duration, aspect ratio
- Hover effect: Show template details on hover
- Selected state: Highlight selected template card
- Shadcn components: Card, Button, Badge, Tabs, Dialog
- Responsive: Grid layout on desktop, list on mobile
- Create file: `frontend/src/components/templates/TemplateSelector.tsx`

### PlatformPreview Component
- Client component showing platform-specific preview
- Props: videoId (string), templateId (string), segmentStart (number), segmentEnd (number), cropStrategy (string)
- Display video preview in platform aspect ratio
- Mock platform UI overlay:
  - For TikTok: Show TikTok UI elements (heart, comment, share buttons on right)
  - For Instagram: Show Instagram Reels UI (bottom profile, like, comment)
  - For YouTube Shorts: Show YouTube Shorts UI (subscribe button, like/dislike)
- Video player centered with correct aspect ratio
- Platform logo in corner
- Duration indicator: "0:45 / 1:00" showing trimmed duration
- Caption preview: Show how captions will look with platform styling
- Comparison toggle: Switch between "Before" and "After" preview
- Zoom controls: Zoom in/out to see detail
- Loading state: Skeleton loader while preview generates
- Error state: Display error message if preview fails
- Generate preview button: Triggers preview generation API call
- Shadcn components: Card, Skeleton, Button, Tabs, AspectRatio
- Create file: `frontend/src/components/templates/PlatformPreview.tsx`

### AspectRatioEditor Component
- Client component for configuring aspect ratio transformation
- Props: videoId (string), targetAspectRatio (string), onStrategyChange (function)
- Show current video aspect ratio vs target aspect ratio
- Strategy selector (radio group or tabs):
  - Smart Crop: "Automatically crop to keep important content"
  - Center Crop: "Simple center crop (may lose edge content)"
  - Letterbox: "Add bars to fit video"
  - Blur Background: "Blur background with video centered" (recommended)
- Visual preview for each strategy:
  - Show thumbnail/frame with strategy applied
  - Highlight what will be cropped/changed
  - Side-by-side comparison
- Advanced options (collapsible):
  - Crop position bias: Top, center, bottom (for center crop)
  - Blur intensity: Slider for blur background strategy
  - Letterbox color: Color picker for letterbox bars
- Face detection toggle: "Prioritize faces when cropping" (for smart crop)
- Warning messages:
  - "Center crop will remove 30% of video width" (if significant crop)
  - "Letterbox may not look good on mobile" (if using letterbox for portrait)
- Preview button: Generate preview with selected strategy
- Shadcn components: RadioGroup, Tabs, Slider, Collapsible, Alert
- Create file: `frontend/src/components/templates/AspectRatioEditor.tsx`

### ExportDialog Component
- Client component for configuring and starting export
- Props: videoId (string), onExportStart (function)
- Multi-step dialog:
  - Step 1: Select template (TemplateSelector)
  - Step 2: Select segment (TimelineSegmentSelector or use full video)
  - Step 3: Configure aspect ratio (AspectRatioEditor)
  - Step 4: Preview and confirm (PlatformPreview)
- Timeline segment selector:
  - Visual timeline with draggable start/end handles
  - Duration counter showing selected duration
  - Platform duration limit indicator
  - "Use Highlight" button to auto-select highlight segments
- Export options:
  - Quality selector: High (1080p, 8Mbps), Medium (1080p, 5Mbps), Low (720p, 3Mbps)
  - Caption toggle: Enable/disable captions
  - Caption style selector: Choose from presets or custom
- Export button: Start export, disable during processing
- Progress display: Show export progress with stage names
- Estimated time: Calculate based on video length and export queue
- Error handling: Display errors with retry button
- Success state: "Export completed! Download now" with download button
- Close dialog: Can close and check progress later from dashboard
- Shadcn components: Dialog, Stepper, Button, Slider, Switch, Progress
- Create file: `frontend/src/components/templates/ExportDialog.tsx`

### ExportsList Component
- Client component displaying all exports for a video
- Props: videoId (string)
- Fetch exports on mount using getVideoExports
- Display exports as table or card list:
  - Template/Platform name with icon
  - Created timestamp (relative time)
  - Status badge (processing, completed, failed)
  - File size (for completed exports)
  - Duration and resolution
  - Action buttons: Download, Delete, Retry (if failed), Preview
- Progress bars for in-progress exports
- Auto-refresh: Poll for updates every 5 seconds if any export is processing
- Filtering: By status, platform, date range
- Sorting: By created date, status
- Bulk actions: Delete multiple exports
- Empty state: "No exports yet. Create your first export!"
- Loading state: Skeleton loaders for table rows
- Export limit warning: "You have 3/10 exports this month" (based on plan)
- Shadcn components: Table, Badge, Button, Progress, Checkbox, DropdownMenu
- Create file: `frontend/src/components/templates/ExportsList.tsx`

### TemplateCreator Component
- Client component for creating custom templates
- Props: onTemplateCreate (function), initialTemplate (Template, optional for editing)
- Form fields:
  - Template name (text input)
  - Platform (select dropdown)
  - Aspect ratio (select or custom input: "9:16", "16:9", "1:1", "4:5", etc.)
  - Max duration (number input in seconds)
  - Auto-captions toggle (boolean)
  - Caption style configuration:
    - Style preset selector (minimal, bold, gaming, etc.) or custom
    - If custom: Font selector, size slider, color pickers, position selector
  - Video quality preset (High, Medium, Low)
- Live preview: Show caption style preview on sample frame
- Validation:
  - Name required (max 50 chars)
  - Valid aspect ratio format (e.g., "9:16")
  - Duration within reasonable limits (5-600 seconds)
- Save button: Create/update template via API
- Cancel button: Close dialog without saving
- Reset button: Reset to default values
- Error handling: Display validation errors inline
- Success message: "Template created successfully!"
- Shadcn components: Dialog, Form, Input, Select, Slider, Switch, ColorPicker, Button
- Create file: `frontend/src/components/templates/TemplateCreator.tsx`

### CaptionStylePreview Component
- Client component showing caption style preview
- Props: captionStyle (CaptionStyle), sampleText (string, optional)
- Display sample video frame or static image
- Overlay caption with specified style
- Show caption at specified position (top/center/bottom)
- Animate caption if animation style specified
- Editable sample text: Allow user to type custom text to preview
- Background options: Light/dark/colorful to test contrast
- Zoom controls: Zoom in to see caption detail
- Platform safe zones: Show platform UI overlays to ensure captions don't conflict
- Shadcn components: Card, Input, Tabs
- Create file: `frontend/src/components/templates/CaptionStylePreview.tsx`

### QuickExport Component
- Client component for one-click export
- Props: videoId (string), platform (string, e.g., 'youtube_shorts')
- Single button: "Export to [Platform]" with platform logo
- Uses platform's default template automatically
- If video longer than platform limit, opens segment selector
- Shows quick confirmation: "Export to YouTube Shorts (60s, 9:16)?"
- Progress notification: Toast showing export progress
- Success notification: "Export completed! Click to download"
- Error notification: "Export failed. Click to retry"
- Ideal for users who want fast exports without configuration
- Shadcn components: Button, Popover, Toast
- Create file: `frontend/src/components/templates/QuickExport.tsx`

### Frontend API Client Functions
- getSocialMediaTemplates(params): Fetch templates, returns Promise<{templates: Template[], total: number}>
  - Params: {platform, is_system_preset, is_active}
- getTemplate(templateId): Fetch single template, returns Promise<Template>
- createTemplate(template): Create custom template, returns Promise<Template>
  - Template: {name, platform, aspect_ratio, max_duration_seconds, caption_style, style_preset}
- updateTemplate(templateId, updates): Update template, returns Promise<Template>
- deleteTemplate(templateId): Delete template, returns Promise<void>
- getSystemPresets(): Fetch system presets, returns Promise<Template[]>
- exportVideoWithTemplate(videoId, config): Start export, returns Promise<{job_id: string, export_id: string}>
  - Config: {template_id, segment_start_time, segment_end_time, crop_strategy, quality}
- getVideoExports(videoId, params): Fetch exports, returns Promise<{exports: VideoExport[], total: number}>
  - Params: {template_id, status, limit, offset}
- getExport(exportId): Fetch single export, returns Promise<VideoExport>
- deleteExport(exportId): Delete export, returns Promise<void>
- getExportProgress(exportId): Get export progress, returns Promise<ExportProgress>
- retryExport(exportId): Retry failed export, returns Promise<void>
- generateExportPreview(videoId, config): Generate preview, returns Promise<{preview_url: string}>
  - Config: {template_id, segment_start_time, segment_end_time, crop_strategy}
- getTemplateSample(templateId): Get sample video for template, returns Promise<{sample_url: string}>
- All functions use apiClient with proper error handling and TypeScript types

### TypeScript Type Definitions
- Template interface: id, platform, name, description, aspect_ratio, max_duration_seconds, auto_captions, caption_style, style_preset, video_codec, audio_codec, bitrate, is_system_preset, user_id, is_active, usage_count, created_at, updated_at
- PlatformType type: 'youtube_shorts' | 'tiktok' | 'instagram_reels' | 'twitter' | 'linkedin' | 'custom'
- AspectRatio type: '9:16' | '16:9' | '1:1' | '4:5' | '4:3' | string (for custom)
- CaptionStyle interface: font_family, font_size, font_weight, text_color, background_color, stroke_color, stroke_width, position, y_offset, alignment, animation, max_chars_per_line, max_lines
- StylePreset type: 'minimal' | 'bold' | 'gaming' | 'podcast' | 'vlog' | 'professional' | 'trendy' | 'custom'
- CaptionAnimation type: 'none' | 'fade' | 'slide' | 'pop' | 'word-by-word'
- CropStrategy type: 'smart' | 'center' | 'letterbox' | 'blur'
- VideoExport interface: id, video_id, template_id, template_name, platform, export_url, status, file_size, resolution, duration_seconds, segment_start_time, segment_end_time, crop_strategy, error_message, created_at, updated_at
- ExportStatus type: 'processing' | 'completed' | 'failed'
- ExportProgress interface: progress, status, current_stage, estimated_time_remaining
- ExportStage type: 'extracting' | 'transforming' | 'trimming' | 'adding_captions' | 'encoding' | 'uploading'
- ExportConfig interface: template_id, segment_start_time?, segment_end_time?, crop_strategy, quality, enable_captions
- QualityPreset type: 'high' | 'medium' | 'low'

### Integration with Existing Features
- Dashboard: Add "Export" dropdown button on video cards with platform quick actions
- Video Editor: Add "Export to Social Media" button in toolbar, opens ExportDialog
- Timeline Editor: Add platform icons in timeline header for quick export of selected segment
- Highlights: Add "Export as [Platform]" action on each highlight card
- Clips: Add "Export to Social Media" option when creating clips
- Settings: Add "Default Export Settings" section to configure preferred platforms and quality
- User Profile: Show export history and usage stats (exports per month)
- Billing: Track export limits per plan, show upgrade prompts when limit reached

### Testing Requirements
- Backend unit tests: Test aspect ratio transformation algorithms with various input aspect ratios
- Backend unit tests: Test duration enforcement logic with edge cases (very short, very long videos)
- Backend unit tests: Test caption overlay rendering with different styles and text lengths
- Backend integration tests: Test template CRUD operations via API
- Backend integration tests: Test export endpoints with various template configurations
- Worker tests: Test full export workflow with real video samples
- Worker tests: Test error handling and retry logic for failed exports
- Frontend component tests: Test TemplateSelector, PlatformPreview, AspectRatioEditor, ExportDialog
- Frontend component tests: Test QuickExport, ExportsList, TemplateCreator, CaptionStylePreview
- E2E tests: Full export workflow (select template, configure, preview, export, download)
- E2E tests: Test each platform preset (YouTube Shorts, TikTok, Instagram Reels)
- E2E tests: Test custom template creation and usage
- Visual regression tests: Ensure caption styles render consistently across updates
- Performance tests: Test export speed for various video lengths and aspect ratios
- Quality tests: Verify exported videos meet platform requirements (resolution, bitrate, duration)
- Accessibility tests: Ensure caption contrast meets WCAG AA standards

### Performance Considerations
- Use FFmpeg hardware acceleration (NVENC, VideoToolbox, VAAPI) for faster encoding
- Cache aspect ratio transformations for common conversions (16:9 to 9:16)
- Pre-compute smart crop regions during video upload to speed up exports
- Generate low-res previews quickly (720p, 2Mbps) for fast feedback
- Limit concurrent exports per user (3 max) to prevent resource exhaustion
- Use CDN for serving exported videos (CloudFront)
- Implement progressive upload (stream to S3) to reduce disk usage
- Clean up temporary files immediately after export completes
- Cache rendered caption frames to avoid re-rendering for similar captions
- Use video segment extraction instead of full video processing when possible
- Optimize FFmpeg filters pipeline (combine multiple operations in single pass)

### Quality Considerations
- Validate all exported videos meet platform specifications (aspect ratio, duration, resolution)
- Test caption readability at mobile sizes (especially for 9:16 videos)
- Ensure audio quality is maintained during re-encoding (use high-quality AAC codec)
- Verify color accuracy after transformation (avoid color shifts)
- Test exported videos on actual mobile devices (iOS, Android)
- Implement quality metrics: Check bitrate, resolution, duration after export
- Add quality warnings: Alert user if export quality is lower than original
- Support lossless export option for pro users (higher bitrate, larger file size)
- Maintain metadata (title, description) from original video
- Add watermark removal for paid users (remove watermark added in free tier)

### Platform-Specific Requirements
- **YouTube Shorts**:
  - Vertical format (9:16) required
  - Max 60 seconds
  - Recommended resolution: 1080x1920
  - File format: MP4
  - Captions should be bold and bottom-centered
  - Include #Shorts in description/metadata
- **TikTok**:
  - Vertical format (9:16) required
  - Max 60 seconds (180s for accounts with 1K+ followers)
  - Recommended resolution: 1080x1920
  - File format: MP4 or MOV
  - Captions should be animated and trendy
  - High engagement areas: Bottom 25% of screen (avoid UI overlap)
- **Instagram Reels**:
  - Vertical format (9:16) preferred
  - Max 90 seconds
  - Recommended resolution: 1080x1920
  - File format: MP4
  - Captions should be clean with aesthetic styling
  - Consider Instagram UI elements (profile pic bottom-left, action buttons right)
- **Twitter/X**:
  - Flexible aspect ratios (16:9, 1:1, 9:16)
  - Max 140 seconds (2:20)
  - Max file size: 512MB
  - Recommended resolution: 1280x720 or 1080x1080
  - Minimal captions preferred
- **LinkedIn**:
  - Square format (1:1) preferred for feed
  - Max 10 minutes (600s)
  - Recommended resolution: 1080x1080
  - Professional tone and styling
  - Captions should be clear and corporate-friendly

### Error Handling & Edge Cases
- Video too long for platform: Show trim options with smart trim suggestion
- Video aspect ratio cannot be converted: Show warning, suggest letterbox or blur background
- Caption text too long for platform limits: Auto-truncate or split into multiple captions
- Multiple speakers in transcript: Option to color-code or distinguish captions per speaker
- No transcript available: Disable auto-captions, show warning "Upload requires manual captions"
- Export queue full: Show wait time estimate, offer priority processing for paid users
- S3 upload failure: Retry with exponential backoff, show error if max retries exceeded
- FFmpeg encoding error: Capture error details, show user-friendly message, offer retry
- Invalid segment selection: Validate start < end, within video duration
- Platform API changes: Monitor platform specs, update configurations as needed
- Concurrent exports limit: Show message "Max 3 exports at once. Please wait."
- Storage quota exceeded: Show upgrade prompt, offer to delete old exports

### Analytics & Tracking
- Track template usage: Which templates are most popular?
- Track export success rate: Percentage of exports that complete successfully
- Track export duration: Average time to complete export by video length
- Track platform preference: Which platforms do users export to most?
- Track crop strategy preference: Which strategies do users choose?
- Track caption usage: What percentage of exports include captions?
- Track export quality: Which quality preset is most popular?
- A/B test different caption styles: Which styles get more usage?
- Monitor error rates: Which exports fail most often and why?
- Track time to first export: How long after signup do users export their first video?
- Track export engagement: Do users download/share their exported videos?

### User Experience Enhancements
- Batch export: Export to multiple platforms with one click
- Export presets: Save favorite configurations for quick reuse
- Template recommendations: Suggest templates based on video content (ML-based)
- Smart duration: Suggest optimal duration based on video content and platform
- Caption auto-editing: Fix transcript errors before burning captions
- Brand kit: Save brand colors, fonts, logos for consistent styling
- Schedule exports: Queue exports for later processing (off-peak hours)
- Notification preferences: Choose how to be notified when export completes
- Export history: View all past exports with analytics (views, downloads)
- Share exports: Share exported videos directly to social media (OAuth integration)
- Export templates marketplace: Browse and download community-created templates (future feature)

## Success Criteria
- Export completes in <5 minutes for 30-minute video
- Aspect ratio conversion maintains quality (no visible artifacts)
- Captions are readable and properly timed (±0.2s accuracy)
- Exported videos meet all platform specifications (100% compliance)
- Users successfully export to at least one platform within first session (>60% adoption)
- Export success rate >95% (excluding user cancellations)
- User satisfaction with caption styling >4.0/5.0 average rating
- Smart crop accurately identifies main subject >80% of time
- Export file sizes are optimized (balance quality/size)
- Test coverage >90% for export workflow code
- No critical bugs in production after launch
- Average exports per user: >3 per month
- Users find one-click export intuitive (>90% successful without help docs)
