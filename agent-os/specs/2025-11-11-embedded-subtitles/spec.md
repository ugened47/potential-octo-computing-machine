# Specification: Embedded Subtitles

## Goal
Enable users to burn customizable, professionally-styled subtitles directly into their videos with support for multiple languages and automatic translation, making content accessible and optimized for social media platforms where viewers watch without sound.

## User Stories
- As a content creator, I want to burn subtitles into my videos so that viewers can watch without sound on social media
- As a creator, I want to customize subtitle styling (font, size, color, position) so that subtitles match my brand and are readable
- As a multilingual creator, I want to automatically translate my subtitles to multiple languages so that I can reach a global audience
- As a user, I want to preview subtitle styling in real-time so that I can see exactly how they will look before exporting
- As a TikTok creator, I want to use preset subtitle styles (YouTube, TikTok, Instagram) so that I can quickly apply platform-appropriate styling
- As a user, I want to export videos with embedded subtitles in multiple languages so that I can create localized versions efficiently

## Specific Requirements

### SubtitleStyle Model & Database
- Create SubtitleStyle model with video_id (foreign key), language_code (string, ISO 639-1 format)
- Style properties:
  - font_family (string, default 'Arial'): Font name
  - font_size (integer, default 24): Font size in pixels (range 12-72)
  - font_weight (enum: 'normal', 'bold', default 'bold'): Font weight
  - font_color (string, default '#FFFFFF'): Primary text color (hex format)
  - font_alpha (float, default 1.0): Text opacity (0.0-1.0)
- Background properties:
  - background_enabled (boolean, default true): Whether to show background
  - background_color (string, default '#000000'): Background color (hex)
  - background_alpha (float, default 0.7): Background opacity (0.0-1.0)
  - background_padding (integer, default 10): Padding around text in pixels
  - background_radius (integer, default 4): Border radius in pixels
- Outline/stroke properties:
  - outline_enabled (boolean, default true): Whether to show text outline
  - outline_color (string, default '#000000'): Outline color (hex)
  - outline_width (integer, default 2): Outline width in pixels (range 0-8)
- Position properties:
  - position_vertical (enum: 'top', 'center', 'bottom', default 'bottom'): Vertical alignment
  - position_horizontal (enum: 'left', 'center', 'right', default 'center'): Horizontal alignment
  - margin_vertical (integer, default 50): Vertical margin from edge in pixels
  - margin_horizontal (integer, default 40): Horizontal margin from edge in pixels
  - max_width_percent (integer, default 80): Maximum subtitle width as percentage of video width
- Timing properties:
  - words_per_line (integer, default 7): Maximum words per subtitle line
  - max_lines (integer, default 2): Maximum number of lines per subtitle
  - min_display_duration (float, default 1.0): Minimum display time in seconds
  - max_display_duration (float, default 6.0): Maximum display time in seconds
- Animation properties:
  - animation_type (enum: 'none', 'fade', 'slide', 'pop', default 'none'): Animation style
  - animation_duration (float, default 0.3): Animation duration in seconds
- Metadata:
  - preset_name (string, nullable): Name of preset if based on template (e.g., 'YouTube Default', 'TikTok Viral')
  - is_template (boolean, default false): Whether this is a reusable template
  - created_by (UUID, foreign key to User): User who created the style
- Timestamps: created_at, updated_at
- Create database migration with indexes on video_id, language_code, preset_name, is_template
- Unique constraint on (video_id, language_code) to ensure one style per language per video
- Cascade delete when video is deleted

### SubtitleTranslation Model & Database
- Create SubtitleTranslation model for storing translated subtitle content
- Fields:
  - id (UUID, primary key)
  - video_id (UUID, foreign key to Video)
  - source_language (string, ISO 639-1): Original language code
  - target_language (string, ISO 639-1): Translation target language
  - translation_service (string, default 'google'): Service used ('google', 'deepl', 'manual')
  - translation_quality (enum: 'machine', 'reviewed', 'professional', default 'machine')
  - segments (JSONB): Array of translated segments with structure:
    ```json
    [
      {
        "start_time": 0.0,
        "end_time": 2.5,
        "original_text": "Hello world",
        "translated_text": "Hola mundo",
        "confidence": 0.95
      }
    ]
    ```
  - character_count (integer): Total character count of translation
  - word_count (integer): Total word count of translation
  - status (enum: 'pending', 'processing', 'completed', 'failed', default 'pending')
  - error_message (text, nullable): Error details if translation failed
- Timestamps: created_at, updated_at
- Create database migration with indexes on video_id, target_language, status
- Unique constraint on (video_id, target_language)
- Cascade delete when video is deleted

### Subtitle Style Preset System
- Create SubtitleStylePreset model for reusable style templates
- Pre-defined platform-specific presets:
  - **YouTube Default**: Arial bold 32px, white text with black outline, bottom center, 2px outline
  - **TikTok Viral**: Montserrat ExtraBold 48px, yellow (#FFD700) with black background box, center screen
  - **Instagram Reels**: Poppins Bold 36px, white with 80% black background, bottom center, rounded corners
  - **LinkedIn Professional**: Roboto 28px, dark gray (#2D2D2D) on white background, bottom center, clean minimal
  - **Accessibility High Contrast**: Arial 40px, yellow text on black background, 100% opacity, large margins
  - **Minimalist**: Inter 24px, white with subtle shadow, no background, bottom center
- Each preset includes:
  - name (string, unique)
  - description (string)
  - platform (enum: 'youtube', 'tiktok', 'instagram', 'linkedin', 'custom')
  - thumbnail_url (string, nullable): Preview image
  - style_config (JSONB): Complete SubtitleStyle configuration
  - usage_count (integer, default 0): Track popularity
  - is_system_preset (boolean, default false): Cannot be deleted if true
  - is_public (boolean, default true): Available to all users
  - created_by (UUID, nullable): User who created custom preset
- Users can create custom presets from their current style
- Users can share presets (generate shareable link)
- Trending presets based on usage_count

### Subtitle Styling Service
- Create `SubtitleStylingService` class in `backend/app/services/subtitle_styling.py`
- Methods:
  - `get_or_create_default_style(video_id: UUID, language: str) -> SubtitleStyle`
    - Get existing style or create with default values
    - Apply system default preset if first time
  - `apply_preset(video_id: UUID, preset_name: str, language: str) -> SubtitleStyle`
    - Load preset configuration
    - Create or update SubtitleStyle with preset values
    - Track preset usage count
  - `update_style(style_id: UUID, updates: dict) -> SubtitleStyle`
    - Validate style property values (ranges, format)
    - Update SubtitleStyle record
    - Return updated style
  - `clone_style(source_style_id: UUID, target_video_id: UUID) -> SubtitleStyle`
    - Copy style from one video to another
    - Useful for batch processing with consistent styling
  - `validate_style(style_data: dict) -> dict[str, list[str]]`
    - Validate all style properties
    - Check color formats (hex codes)
    - Check numeric ranges (font size, opacity, etc.)
    - Return validation errors if any
  - `generate_style_preview_image(style: SubtitleStyle, sample_text: str) -> bytes`
    - Generate preview thumbnail with sample text
    - Use PIL/Pillow to render styled text
    - Return PNG image bytes
  - `export_style_as_preset(style_id: UUID, name: str, description: str) -> SubtitleStylePreset`
    - Convert SubtitleStyle to reusable preset
    - Allow users to save favorite styles
- Validation rules:
  - Font size: 12-72 pixels
  - Opacity values: 0.0-1.0
  - Outline width: 0-8 pixels
  - Margins: 0-200 pixels
  - Max width percent: 20-100%
  - Color values: valid hex codes (#RRGGBB or #RRGGBBAA)
- Handle errors gracefully with detailed messages

### FFmpeg Subtitle Burning Service
- Create `SubtitleBurningService` class in `backend/app/services/subtitle_burning.py`
- Methods:
  - `burn_subtitles(video_id: UUID, language: str, output_format: str = 'mp4') -> str`
    - Main method to burn subtitles into video
    - Returns output video path or S3 URL
  - `generate_ass_subtitle_file(video_id: UUID, style: SubtitleStyle, language: str) -> str`
    - Convert transcript segments to ASS (Advanced SubStation Alpha) format
    - Apply all style properties (font, color, position, outline)
    - ASS format supports advanced styling better than SRT
    - Return path to generated .ass file
  - `generate_srt_subtitle_file(video_id: UUID, language: str) -> str`
    - Convert transcript to simple SRT format (for fallback/compatibility)
    - Include timing and text only (no advanced styling)
    - Return path to generated .srt file
  - `apply_ffmpeg_subtitle_burn(video_path: str, subtitle_path: str, output_path: str, style: SubtitleStyle) -> None`
    - Use FFmpeg with subtitles filter to burn subtitles
    - FFmpeg command structure:
      ```bash
      ffmpeg -i input.mp4 -vf "ass=subtitles.ass" -c:a copy output.mp4
      ```
    - Or for SRT with custom styling:
      ```bash
      ffmpeg -i input.mp4 -vf "subtitles=subtitles.srt:force_style='FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=2,Alignment=2,MarginV=50'" -c:a copy output.mp4
      ```
    - Preserve audio codec (-c:a copy for efficiency)
    - Re-encode video with burned subtitles
  - `estimate_burn_duration(video_duration: float, resolution: str) -> float`
    - Estimate processing time based on video length and resolution
    - Used for progress tracking and user expectations
    - Return estimated seconds
  - `validate_subtitle_file(subtitle_path: str, format: str) -> bool`
    - Validate ASS or SRT file format
    - Check for syntax errors
    - Ensure timing is valid
- ASS format generation:
  - Create proper ASS header with style definitions
  - Map SubtitleStyle properties to ASS Style format:
    ```
    [V4+ Styles]
    Style: Default,Arial,24,&H00FFFFFF,&H00000000,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,10,2,40,40,50,1
    ```
  - Convert hex colors to ASS color format (&HAABBGGRR)
  - Handle position using Alignment codes (1-9 numpad layout)
  - Include all transcript segments with timing
- SRT format generation:
  - Standard format:
    ```
    1
    00:00:00,000 --> 00:00:02,500
    Hello world

    2
    00:00:02,500 --> 00:00:05,000
    Welcome to the video
    ```
  - Convert transcript word-level timestamps to subtitle segments
  - Group words into lines based on words_per_line setting
  - Respect max_lines and display duration limits
- Error handling:
  - Validate FFmpeg is installed and accessible
  - Check video file exists and is readable
  - Verify sufficient disk space for output
  - Handle FFmpeg errors with detailed logging
  - Fallback to SRT if ASS fails
- Performance optimization:
  - Process in chunks for long videos
  - Use hardware acceleration if available (GPU)
  - Stream processing to minimize memory usage
  - Cache subtitle files for reuse

### Translation Service
- Create `SubtitleTranslationService` class in `backend/app/services/subtitle_translation.py`
- Integration with Google Cloud Translation API v3:
  - Use google-cloud-translate library
  - Configure API credentials via environment variables
  - Handle API quotas and rate limits
- Methods:
  - `translate_subtitles(video_id: UUID, source_lang: str, target_lang: str) -> SubtitleTranslation`
    - Main method to translate all subtitles
    - Fetch original transcript segments
    - Batch translate text segments
    - Store translation in SubtitleTranslation model
    - Return translation record
  - `translate_batch(texts: list[str], source_lang: str, target_lang: str) -> list[dict]`
    - Translate multiple text segments in single API call
    - Google Translate API supports batch requests
    - Return list of translations with confidence scores
    - Handle API errors and retries
  - `detect_language(text: str) -> str`
    - Auto-detect source language if not specified
    - Return ISO 639-1 language code
  - `get_supported_languages() -> list[dict]`
    - Return list of supported languages
    - Include language code, name, and native name
    - Cache list for performance
  - `estimate_translation_cost(character_count: int) -> float`
    - Calculate estimated cost based on Google Translate pricing
    - Return cost in USD
  - `validate_translation_quality(original: str, translated: str, target_lang: str) -> float`
    - Basic quality check (length ratio, special character preservation)
    - Return quality score 0-1
  - `create_manual_translation(video_id: UUID, target_lang: str, segments: list[dict]) -> SubtitleTranslation`
    - Allow users to upload manual translations
    - Validate segment structure and timing
    - Mark as 'professional' quality
- Supported languages (prioritize common ones):
  - Tier 1 (launch): English (en), Spanish (es), French (fr), German (de), Portuguese (pt), Russian (ru), Chinese (zh), Japanese (ja), Korean (ko), Arabic (ar)
  - Tier 2 (post-launch): Italian (it), Dutch (nl), Polish (pl), Turkish (tr), Hindi (hi), Vietnamese (vi), Thai (th), Indonesian (id)
  - Total: 18+ languages
- Translation optimization:
  - Batch translate up to 100 segments per API call
  - Cache common phrases/words to reduce API calls
  - Preserve special formatting (timestamps, names, technical terms)
  - Handle context across subtitle segments for better accuracy
- Cost management:
  - Track translation character count per user
  - Implement usage limits based on pricing tier
  - Estimate cost before translation and confirm with user
  - Google Translate pricing: ~$20 per 1M characters
- Quality considerations:
  - Allow users to edit machine translations
  - Track user edits to improve translation over time
  - Option to use professional translation services (future)
  - Preserve subtitle timing and formatting
- Error handling:
  - Handle API quotas exceeded
  - Retry failed translations with exponential backoff
  - Fallback to alternative translation service if available
  - Store partial results if batch fails

### Background Job Processing
- ARQ task: `burn_subtitles_job(video_id: str, language: str, style_id: str = None) -> dict`
  - Download video from S3
  - Get or create subtitle style
  - Generate ASS/SRT subtitle file
  - Burn subtitles using FFmpeg
  - Upload output video to S3
  - Update video metadata with subtitle_burned flag
  - Track progress in Redis (0-100%)
  - Return {status, output_url, duration}
- ARQ task: `translate_subtitles_job(video_id: str, target_languages: list[str]) -> dict`
  - Fetch video transcript
  - Detect source language if not specified
  - For each target language:
    - Check if translation already exists
    - Translate all subtitle segments
    - Store SubtitleTranslation record
    - Track progress in Redis
  - Return {status, translations: [{language, segment_count, character_count}]}
- ARQ task: `batch_burn_subtitles_job(video_ids: list[str], language: str, preset_name: str) -> dict`
  - Process multiple videos with same subtitle styling
  - Apply preset to all videos
  - Burn subtitles for each video
  - Generate batch export ZIP file
  - Return {status, processed_count, failed_count, download_url}
- Progress tracking:
  - Subtitle burning: Upload 10%, Generate subtitle file 20%, FFmpeg processing 30-90%, Upload output 90-100%
  - Translation: Detect language 10%, Batch 1 20-40%, Batch 2 40-60%, Batch 3 60-80%, Store results 80-100%
- Job timeouts:
  - Subtitle burning: 20 minutes for 1080p 30-min video
  - Translation: 5 minutes per language
- Error handling:
  - Retry failed FFmpeg operations (max 2 attempts)
  - Store error details in job result
  - Send notification to user on failure
  - Clean up temporary files on error

### Subtitle API Endpoints

**Style Management:**
- GET /api/videos/{id}/subtitle-styles: List all subtitle styles for video
  - Query params: language (optional, filter by language)
  - Returns array of SubtitleStyle objects
- GET /api/subtitle-styles/{id}: Get single subtitle style
  - Returns SubtitleStyle with all properties
- POST /api/videos/{id}/subtitle-styles: Create new subtitle style
  - Body: {language, font_family, font_size, ...all style properties}
  - Validates all properties
  - Returns created SubtitleStyle
- PATCH /api/subtitle-styles/{id}: Update subtitle style
  - Body: partial style properties to update
  - Validates changes
  - Returns updated SubtitleStyle
- DELETE /api/subtitle-styles/{id}: Delete subtitle style
  - Soft delete or hard delete based on dependencies
- POST /api/subtitle-styles/{id}/clone: Clone style to another video
  - Body: {target_video_id}
  - Returns new SubtitleStyle

**Preset Management:**
- GET /api/subtitle-presets: List all available presets
  - Query params: platform (optional), is_public, sort (popular, recent, name)
  - Returns array of SubtitleStylePreset objects
- GET /api/subtitle-presets/{name}: Get specific preset
  - Returns preset configuration
- POST /api/videos/{id}/subtitle-styles/apply-preset: Apply preset to video
  - Body: {preset_name, language}
  - Creates or updates SubtitleStyle with preset values
  - Returns SubtitleStyle
- POST /api/subtitle-presets: Create custom preset from style
  - Body: {style_id, name, description, is_public}
  - Only authenticated users
  - Returns created SubtitleStylePreset
- DELETE /api/subtitle-presets/{name}: Delete custom preset
  - Only creator can delete
  - Cannot delete system presets

**Subtitle Burning:**
- POST /api/videos/{id}/burn-subtitles: Trigger subtitle burning
  - Body: {language, style_id (optional), output_format (default 'mp4')}
  - Enqueues ARQ job
  - Returns {job_id, estimated_duration}
- GET /api/videos/{id}/burn-subtitles/progress: Get burning progress
  - Returns {progress, status, estimated_time_remaining, current_stage}
- GET /api/videos/{id}/subtitled-versions: List all versions with burned subtitles
  - Returns array of {language, created_at, file_size, download_url}

**Translation:**
- GET /api/videos/{id}/translations: List all translations
  - Returns array of SubtitleTranslation objects
- POST /api/videos/{id}/translations: Create new translation
  - Body: {target_languages: string[], source_language (optional)}
  - Enqueues translation job for each language
  - Returns {job_ids: string[], estimated_cost: number}
- GET /api/translations/{id}: Get translation details
  - Returns SubtitleTranslation with all segments
- PATCH /api/translations/{id}/segments: Update translated segments
  - Body: {segments: [{start_time, end_time, translated_text}]}
  - Allow manual corrections
  - Updates translation_quality to 'reviewed'
  - Returns updated SubtitleTranslation
- DELETE /api/translations/{id}: Delete translation
- POST /api/videos/{id}/translations/export: Export translation as SRT/VTT file
  - Body: {language, format: 'srt' | 'vtt'}
  - Returns download URL

**Preview:**
- POST /api/subtitle-styles/{id}/preview: Generate preview image
  - Body: {sample_text (optional, default "Sample subtitle text")}
  - Returns {preview_url, expires_at}
- GET /api/videos/{id}/subtitle-preview: Preview video segment with subtitles
  - Query params: start_time, duration, language, style_id
  - Returns short video clip with burned subtitles for preview
  - Cache preview clips for 1 hour

### SubtitleStyleEditor Component
- Client component for customizing subtitle styling
- Props:
  - videoId (string)
  - language (string, default 'en')
  - initialStyle (SubtitleStyle, optional)
  - onSave (function, optional)
- Layout: Split view - Editor controls (left 40%) + Live preview (right 60%)
- Editor sections (collapsible accordions):
  1. **Font Settings**:
     - Font family: Dropdown with web-safe fonts + Google Fonts integration
     - Font size: Slider (12-72px) + number input
     - Font weight: Toggle buttons (Normal, Bold)
     - Font color: Color picker with opacity slider
  2. **Background Settings**:
     - Enable background: Toggle
     - Background color: Color picker with opacity slider
     - Padding: Slider (0-30px)
     - Border radius: Slider (0-20px)
  3. **Outline Settings**:
     - Enable outline: Toggle
     - Outline color: Color picker
     - Outline width: Slider (0-8px)
  4. **Position Settings**:
     - Vertical position: Radio buttons (Top, Center, Bottom)
     - Horizontal position: Radio buttons (Left, Center, Right)
     - Vertical margin: Slider (0-200px)
     - Horizontal margin: Slider (0-150px)
     - Max width: Slider (20-100%)
  5. **Timing Settings**:
     - Words per line: Number input (1-15)
     - Max lines: Number input (1-4)
     - Min display duration: Number input (0.5-3.0s)
     - Max display duration: Number input (3.0-10.0s)
  6. **Animation Settings** (optional):
     - Animation type: Dropdown (None, Fade, Slide Up, Pop)
     - Animation duration: Slider (0.1-1.0s)
- Preset selector:
  - Dropdown at top with platform presets
  - Quick apply button
  - "Save as preset" button for current style
- Action buttons:
  - Save: Persist style to database
  - Reset: Restore to last saved state
  - Copy from another video: Import style
  - Export: Download style as JSON
- Real-time preview updates:
  - Debounce updates (300ms) to avoid excessive re-renders
  - Update preview as user adjusts settings
- Keyboard shortcuts:
  - Ctrl+S: Save
  - Ctrl+Z: Undo
  - Ctrl+Shift+Z: Redo
- Shadcn components: Accordion, Slider, Select, Input, ColorPicker, RadioGroup, Tabs, Button
- Implement undo/redo functionality for style changes
- Validation with inline error messages
- Responsive design: Stack editor and preview vertically on mobile
- Create file: `frontend/src/components/subtitles/SubtitleStyleEditor.tsx`

### SubtitlePreview Component
- Client component for real-time subtitle preview
- Props:
  - videoId (string)
  - style (SubtitleStyle)
  - sampleText (string, default "This is a sample subtitle")
  - showVideo (boolean, default true)
  - autoUpdate (boolean, default true)
- Preview modes:
  1. **Static Image Preview**: Render styled text on colored background
  2. **Video Segment Preview**: Show 5-second video clip with subtitles
  3. **Full Timeline Preview**: Scrub through video and see subtitles
- Static preview:
  - Canvas-based rendering or styled HTML div
  - Show sample text with all style properties applied
  - Background with video aspect ratio (16:9 default)
  - Update immediately when style changes
- Video preview:
  - Fetch short video segment from API
  - Overlay subtitle using CSS positioned div (not burned)
  - Match exact styling from SubtitleStyle
  - Play/pause controls
  - Seek to different parts to test readability
- Subtitle rendering:
  - Position based on position_vertical and position_horizontal
  - Apply font styles, colors, background, outline
  - Respect margins and max width
  - Multi-line support with proper line breaking
  - Show animation if enabled
- Accessibility:
  - Show high contrast warning if color contrast is low (<4.5:1)
  - Suggest alternative colors for better readability
  - Test subtitle readability against different video backgrounds
- Performance:
  - Memoize styled text rendering
  - Throttle preview updates during rapid changes
  - Lazy load video preview (only when "Preview with Video" tab selected)
- Create file: `frontend/src/components/subtitles/SubtitlePreview.tsx`

### TranslationPanel Component
- Client component for managing subtitle translations
- Props:
  - videoId (string)
  - sourceLanguage (string, detected or specified)
  - onTranslationComplete (function, optional)
- Layout sections:
  1. **Source Language Detection**:
     - Auto-detect button
     - Manual override dropdown
     - Display detected language with confidence
  2. **Target Languages Selection**:
     - Multi-select dropdown with search
     - Popular languages at top
     - Select all / Deselect all buttons
     - Show flag icons for each language
  3. **Translation Settings**:
     - Translation service: Google Translate (default), option for manual
     - Quality preference: Fast (machine) vs. Accurate (reviewed)
     - Preserve formatting: Toggle
  4. **Cost Estimation**:
     - Show character count
     - Estimated cost per language
     - Total cost for all selected languages
     - User's remaining translation quota
  5. **Translation List** (after translation):
     - Table of all translations
     - Columns: Language, Status, Segments, Actions
     - Status indicators: Pending, Processing, Completed, Failed
     - Actions: View, Edit, Export, Delete
- Translation workflow:
  - User selects target languages
  - Show cost estimate and confirmation dialog
  - Click "Translate" button
  - Show progress for each language
  - Display success/error notifications
- Translation editor:
  - Open modal to edit translation
  - Side-by-side view: Original | Translation
  - Segment-by-segment editing
  - Timing display for each segment
  - Save changes updates translation_quality to 'reviewed'
- Export options:
  - Export translation as SRT file
  - Export translation as VTT file
  - Burn translation into video (link to subtitle burning)
- Progress tracking:
  - Real-time progress bars for each language
  - WebSocket or polling for updates
  - Estimated time remaining
- Error handling:
  - Display API errors with retry button
  - Show partial results if some languages succeed
  - Validate user input before submission
- Shadcn components: Select, Checkbox, Table, Progress, Dialog, Button, Badge, Alert
- Create file: `frontend/src/components/subtitles/TranslationPanel.tsx`

### SubtitleBurnDialog Component
- Client component for configuring and triggering subtitle burning
- Props:
  - videoId (string)
  - onBurnStart (function, optional)
  - onBurnComplete (function, optional)
- Dialog content:
  1. **Language Selection**:
     - Dropdown to select subtitle language
     - Show available languages (original + translations)
  2. **Style Selection**:
     - Radio group: "Use existing style" vs. "Apply preset"
     - If existing: Show current style preview
     - If preset: Preset selector dropdown
  3. **Output Settings**:
     - Output format: MP4 (default), AVI, MOV
     - Video quality: Keep original, 1080p, 720p
     - File name: Input with auto-generated default
  4. **Preview**:
     - Show preview with selected style
     - "Preview with video" button to see short clip
  5. **Burn Button**:
     - Primary button: "Burn Subtitles"
     - Show estimated processing time
     - Disable during processing
- After clicking "Burn Subtitles":
  - Trigger API call to start job
  - Close dialog
  - Show progress in notification or dedicated progress modal
  - Allow user to continue working (non-blocking)
- Progress modal:
  - Title: "Burning Subtitles..."
  - Progress bar with percentage
  - Current stage: "Generating subtitle file...", "Processing video...", "Uploading..."
  - Cancel button (only before FFmpeg starts)
  - Estimated time remaining
- Completion:
  - Success notification with download link
  - Option to view video or download immediately
  - Add to "Subtitled Versions" list
- Error handling:
  - Display error message
  - Offer retry button
  - Link to support if error persists
- Shadcn components: Dialog, Select, RadioGroup, Input, Button, Progress, Alert
- Create file: `frontend/src/components/subtitles/SubtitleBurnDialog.tsx`

### SubtitleLanguageSelector Component
- Client component for selecting subtitle language
- Props:
  - videoId (string)
  - selectedLanguage (string, optional)
  - onChange (function)
  - showAddTranslation (boolean, default true)
- Dropdown showing:
  - Original transcript language (marked with "Original" badge)
  - All available translations (sorted alphabetically)
  - Option to add new translation (if showAddTranslation is true)
- Each language option displays:
  - Flag icon
  - Language name (in English)
  - Native name (e.g., "Spanish (Español)")
  - Segment count or status
- "Add Translation" option:
  - Opens TranslationPanel or simple language picker
  - Quick action to create new translation
- Keyboard navigation support
- Search/filter for long language lists
- Shadcn components: Select with custom rendering
- Create file: `frontend/src/components/subtitles/SubtitleLanguageSelector.tsx`

### SubtitleTimeline Component
- Client component showing subtitle segments on timeline
- Props:
  - videoId (string)
  - language (string)
  - videoDuration (number, seconds)
  - currentTime (number, optional)
  - onSegmentClick (function, optional)
- Visual timeline showing:
  - Horizontal timeline spanning video duration
  - Each subtitle segment as colored block
  - Segment text on hover
  - Current playback position indicator
- Features:
  - Zoom in/out controls
  - Scroll/pan to navigate long videos
  - Click segment to seek video to that time
  - Highlight currently active subtitle
  - Show gaps between subtitles
- Segment coloring:
  - Default: Blue
  - Active/current: Highlight color (green)
  - Long segments (>6s): Warning color (yellow)
  - Very short (<1s): Warning color (orange)
- Integration with video player:
  - Sync current time from video player
  - Click segment to seek video
  - Show segment boundaries
- Use React-Konva or similar canvas library for performance
- Responsive: Adjust timeline size based on container width
- Create file: `frontend/src/components/subtitles/SubtitleTimeline.tsx`

### Frontend API Client Functions
- `getSubtitleStyles(videoId: string, language?: string): Promise<SubtitleStyle[]>`
  - Fetch all subtitle styles for a video
- `getSubtitleStyle(styleId: string): Promise<SubtitleStyle>`
  - Fetch single subtitle style
- `createSubtitleStyle(videoId: string, styleData: Partial<SubtitleStyle>): Promise<SubtitleStyle>`
  - Create new subtitle style
- `updateSubtitleStyle(styleId: string, updates: Partial<SubtitleStyle>): Promise<SubtitleStyle>`
  - Update existing style
- `deleteSubtitleStyle(styleId: string): Promise<void>`
  - Delete subtitle style
- `cloneSubtitleStyle(styleId: string, targetVideoId: string): Promise<SubtitleStyle>`
  - Clone style to another video
- `getSubtitlePresets(platform?: string): Promise<SubtitleStylePreset[]>`
  - Fetch available presets
- `getSubtitlePreset(name: string): Promise<SubtitleStylePreset>`
  - Fetch specific preset
- `applySubtitlePreset(videoId: string, presetName: string, language: string): Promise<SubtitleStyle>`
  - Apply preset to video
- `createSubtitlePreset(styleId: string, name: string, description: string, isPublic: boolean): Promise<SubtitleStylePreset>`
  - Create custom preset from style
- `burnSubtitles(videoId: string, language: string, styleId?: string, outputFormat?: string): Promise<{job_id: string, estimated_duration: number}>`
  - Trigger subtitle burning job
- `getBurnProgress(videoId: string): Promise<{progress: number, status: string, estimated_time_remaining: number, current_stage: string}>`
  - Get burning job progress
- `getSubtitledVersions(videoId: string): Promise<Array<{language: string, created_at: string, file_size: number, download_url: string}>>`
  - List all versions with burned subtitles
- `getTranslations(videoId: string): Promise<SubtitleTranslation[]>`
  - Fetch all translations for video
- `createTranslation(videoId: string, targetLanguages: string[], sourceLanguage?: string): Promise<{job_ids: string[], estimated_cost: number}>`
  - Create new translations
- `getTranslation(translationId: string): Promise<SubtitleTranslation>`
  - Fetch single translation
- `updateTranslationSegments(translationId: string, segments: Array<{start_time: number, end_time: number, translated_text: string}>): Promise<SubtitleTranslation>`
  - Update translated segments (manual corrections)
- `deleteTranslation(translationId: string): Promise<void>`
  - Delete translation
- `exportTranslation(videoId: string, language: string, format: 'srt' | 'vtt'): Promise<{download_url: string}>`
  - Export translation as subtitle file
- `generateStylePreview(styleId: string, sampleText?: string): Promise<{preview_url: string, expires_at: string}>`
  - Generate preview image for style
- `getSubtitlePreviewVideo(videoId: string, startTime: number, duration: number, language: string, styleId: string): Promise<{preview_url: string}>`
  - Get preview video with subtitles
- `detectLanguage(videoId: string): Promise<{language: string, confidence: number}>`
  - Auto-detect video language
- `getSupportedLanguages(): Promise<Array<{code: string, name: string, native_name: string}>>`
  - Get list of supported languages
- All functions use apiClient with proper error handling and TypeScript types

### TypeScript Type Definitions
- `SubtitleStyle` interface: All style properties matching database model
  ```typescript
  interface SubtitleStyle {
    id: string;
    video_id: string;
    language_code: string;
    font_family: string;
    font_size: number;
    font_weight: 'normal' | 'bold';
    font_color: string;
    font_alpha: number;
    background_enabled: boolean;
    background_color: string;
    background_alpha: number;
    background_padding: number;
    background_radius: number;
    outline_enabled: boolean;
    outline_color: string;
    outline_width: number;
    position_vertical: 'top' | 'center' | 'bottom';
    position_horizontal: 'left' | 'center' | 'right';
    margin_vertical: number;
    margin_horizontal: number;
    max_width_percent: number;
    words_per_line: number;
    max_lines: number;
    min_display_duration: number;
    max_display_duration: number;
    animation_type: 'none' | 'fade' | 'slide' | 'pop';
    animation_duration: number;
    preset_name: string | null;
    is_template: boolean;
    created_by: string;
    created_at: string;
    updated_at: string;
  }
  ```
- `SubtitleStylePreset` interface:
  ```typescript
  interface SubtitleStylePreset {
    id: string;
    name: string;
    description: string;
    platform: 'youtube' | 'tiktok' | 'instagram' | 'linkedin' | 'custom';
    thumbnail_url: string | null;
    style_config: Partial<SubtitleStyle>;
    usage_count: number;
    is_system_preset: boolean;
    is_public: boolean;
    created_by: string | null;
    created_at: string;
    updated_at: string;
  }
  ```
- `SubtitleTranslation` interface:
  ```typescript
  interface SubtitleTranslation {
    id: string;
    video_id: string;
    source_language: string;
    target_language: string;
    translation_service: string;
    translation_quality: 'machine' | 'reviewed' | 'professional';
    segments: TranslationSegment[];
    character_count: number;
    word_count: number;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    error_message: string | null;
    created_at: string;
    updated_at: string;
  }
  ```
- `TranslationSegment` interface:
  ```typescript
  interface TranslationSegment {
    start_time: number;
    end_time: number;
    original_text: string;
    translated_text: string;
    confidence: number;
  }
  ```
- `BurnSubtitlesProgress` interface:
  ```typescript
  interface BurnSubtitlesProgress {
    progress: number; // 0-100
    status: 'pending' | 'downloading' | 'generating_subtitles' | 'burning' | 'uploading' | 'completed' | 'failed';
    estimated_time_remaining: number; // seconds
    current_stage: string;
    error_message?: string;
  }
  ```
- `SubtitledVersion` interface:
  ```typescript
  interface SubtitledVersion {
    id: string;
    video_id: string;
    language: string;
    style_id: string;
    file_path: string;
    file_size: number;
    download_url: string;
    created_at: string;
  }
  ```
- `LanguageInfo` interface:
  ```typescript
  interface LanguageInfo {
    code: string; // ISO 639-1
    name: string; // English name
    native_name: string; // Native name
    rtl: boolean; // Right-to-left script
    flag_emoji: string; // Unicode flag emoji
  }
  ```
- `TranslationCostEstimate` interface:
  ```typescript
  interface TranslationCostEstimate {
    character_count: number;
    cost_per_language: number;
    total_cost: number;
    currency: string;
    languages: string[];
  }
  ```

### Testing Requirements

**Backend Unit Tests:**
- Test SubtitleStyle model validation (color formats, value ranges)
- Test SubtitleStylingService methods (create, update, apply preset, validate)
- Test SubtitleBurningService ASS/SRT file generation
- Test SubtitleTranslationService batch translation logic
- Test FFmpeg command generation with various style combinations
- Test translation cost estimation accuracy
- Test subtitle timing calculations (grouping words, duration limits)
- Mock FFmpeg and Google Translate API calls

**Backend Integration Tests:**
- Test complete subtitle burning workflow (style → ASS → FFmpeg → output)
- Test translation API endpoints with real/mock Google Translate
- Test subtitle style CRUD operations via API
- Test preset application to videos
- Test concurrent burning jobs (queue management)
- Test translation storage and retrieval
- Test subtitle file export (SRT/VTT formats)

**Worker Tests:**
- Test burn_subtitles_job with sample videos
- Test translate_subtitles_job with multiple languages
- Test batch_burn_subtitles_job with multiple videos
- Test error handling and retry logic
- Test progress tracking in Redis
- Test job cancellation

**Frontend Component Tests:**
- Test SubtitleStyleEditor renders all controls
- Test SubtitleStyleEditor updates preview on changes
- Test SubtitlePreview renders styled text correctly
- Test TranslationPanel language selection and submission
- Test SubtitleBurnDialog configuration and triggering
- Test SubtitleLanguageSelector displays available languages
- Test SubtitleTimeline renders segments correctly

**E2E Tests:**
- User uploads video, creates subtitle style, burns subtitles, downloads video
- User applies preset, customizes style, saves as custom preset
- User translates subtitles to 3 languages, edits translation, exports SRT
- User burns subtitles in multiple languages, compares outputs
- User clones style from one video to another
- Full workflow: Upload → Style → Translate → Burn → Export

**Visual Regression Tests:**
- Test subtitle rendering with various styles
- Test preview accuracy (compare to actual burned output)
- Test preset previews match actual styling
- Test subtitle positioning on different video aspect ratios

**Performance Tests:**
- Test FFmpeg burning speed for different video lengths and resolutions
- Test translation API response time for various character counts
- Test concurrent burning jobs (load testing)
- Test preview generation speed
- Measure memory usage during subtitle burning

**Accessibility Tests:**
- Test color contrast validation
- Test subtitle readability against various backgrounds
- Test keyboard navigation in SubtitleStyleEditor
- Test screen reader compatibility

### Performance Considerations
- **Subtitle Burning:**
  - Use hardware acceleration (GPU) for FFmpeg if available
  - Process videos in chunks for very long videos (>1 hour)
  - Cache generated ASS/SRT files for reuse
  - Optimize FFmpeg settings for speed vs. quality tradeoff
  - Queue management: Limit concurrent burning jobs to avoid overload
- **Translation:**
  - Batch translate up to 100 segments per API call
  - Cache common phrases and translations
  - Use Redis to store in-progress translations
  - Implement pagination for large translation lists
- **Preview Generation:**
  - Cache preview images for 1 hour
  - Generate low-resolution previews for faster loading
  - Lazy load video previews (only when tab is active)
  - Debounce style updates to avoid excessive preview regeneration
- **Frontend:**
  - Memoize SubtitlePreview component to avoid unnecessary re-renders
  - Use virtual scrolling for long language lists
  - Compress preview images before sending to client
  - Use WebSocket for real-time progress updates instead of polling
- **Database:**
  - Index on (video_id, language_code) for fast style lookups
  - Partition SubtitleTranslation table by video_id for large datasets
  - Use JSONB for translation segments to avoid separate table
  - Cache frequently used presets in Redis

### Quality Considerations
- **Subtitle Styling:**
  - Provide accessibility warnings for low contrast
  - Suggest optimal font sizes for different video resolutions
  - Validate color combinations for readability
  - Test styles on various video backgrounds
- **Translation Quality:**
  - Allow users to review and edit machine translations
  - Track edit frequency to improve translation quality over time
  - Preserve special formatting (names, numbers, technical terms)
  - Provide context to translation API for better accuracy
- **Subtitle Timing:**
  - Ensure subtitles don't overlap or appear too quickly
  - Respect reading speed guidelines (15-20 characters per second)
  - Validate minimum display duration (>1 second)
  - Handle long sentences by splitting across multiple subtitles
- **Output Quality:**
  - Verify subtitle alignment and positioning
  - Test on various video resolutions and aspect ratios
  - Ensure subtitle visibility on both light and dark backgrounds
  - Validate output video file integrity

### Integration Points
- **Video Editor:**
  - "Subtitles" tab in editor showing SubtitleStyleEditor
  - SubtitleTimeline integrated into timeline view
  - Quick burn button in export menu
- **Dashboard:**
  - Show "Subtitles Available" badge on video cards
  - Display translated language count
  - Quick access to burn subtitles
- **Export Flow:**
  - Option to "Export with Subtitles" in export dialog
  - Select language and style before export
  - Generate subtitled version alongside original
- **Batch Processing:**
  - Apply same subtitle style to multiple videos
  - Translate multiple videos to same languages
  - Burn subtitles for entire batch
- **Social Media Templates:**
  - Auto-apply platform-appropriate subtitle styles
  - TikTok/Instagram templates include subtitles by default
  - Optimize subtitle positioning for vertical videos
- **Timeline Editor:**
  - Show subtitle segments on timeline
  - Edit subtitle timing by dragging segment boundaries
  - Click subtitle to edit text

### Localization & RTL Support
- **Right-to-Left Languages:**
  - Support RTL languages (Arabic, Hebrew, Persian, Urdu)
  - Automatically detect RTL and adjust alignment
  - Mirror position_horizontal for RTL (right becomes left)
  - Ensure text flows correctly in RTL
- **Font Support:**
  - Include fonts with international character support
  - Google Fonts API for accessing global fonts
  - Fallback fonts for missing characters
  - Test with CJK characters (Chinese, Japanese, Korean)
- **Character Encoding:**
  - UTF-8 encoding for all subtitle files
  - Preserve special characters and emojis
  - Handle accented characters correctly

### Cost Management
- **Translation Costs:**
  - Track character count per user per month
  - Implement usage limits based on pricing tier
  - Free tier: 10,000 characters/month
  - Creator tier ($19): 100,000 characters/month
  - Pro tier ($39): 500,000 characters/month
  - Business tier ($99): 2,000,000 characters/month
  - Overage: $0.02 per 1,000 characters
- **Display cost estimates before translation:**
  - Show cost in user's currency
  - Confirm before proceeding with expensive translations
  - Alert when approaching monthly limit
- **Optimize API usage:**
  - Cache translations to avoid duplicate API calls
  - Reuse translations across similar videos
  - Batch requests to reduce API overhead

### Error Handling & Edge Cases
- **Missing Transcript:**
  - Cannot burn subtitles if transcript doesn't exist
  - Show error message: "Transcribe video first"
  - Provide link to transcription feature
- **Unsupported Languages:**
  - Handle languages not supported by Google Translate
  - Show list of supported languages
  - Allow manual translation upload
- **FFmpeg Errors:**
  - Log detailed FFmpeg errors for debugging
  - Provide user-friendly error messages
  - Retry with fallback settings if initial burn fails
- **API Quotas:**
  - Handle Google Translate API quota exceeded
  - Queue translations for retry when quota resets
  - Notify user of delays
- **Invalid Style Properties:**
  - Validate all inputs before saving
  - Show inline error messages
  - Prevent saving invalid styles
- **Long Processing Times:**
  - Set realistic timeout limits
  - Allow user to cancel long-running jobs
  - Send email notification when job completes
- **File Size Limits:**
  - Burning subtitles increases file size slightly
  - Warn if output will exceed storage limits
  - Optimize compression to minimize size increase

## Success Criteria
- Subtitle burning completes in <3 minutes for 30-minute 1080p video
- Translation completes in <2 minutes for 10,000 characters
- Preview updates in <500ms after style change
- FFmpeg success rate >95% (less than 5% failures)
- Translation accuracy >90% based on user feedback
- Users successfully export videos with subtitles in >80% of attempts
- Subtitle styles meet WCAG 2.1 AA contrast requirements (4.5:1 minimum)
- Support at least 10 languages at launch
- Custom presets created by >20% of active users
- Average of 2.5 languages translated per video
- Subtitle readability score >80% (based on user surveys)
- Test coverage >90% for subtitle-related code
- API response time <200ms for style CRUD operations
- Zero data loss for subtitle styles and translations
