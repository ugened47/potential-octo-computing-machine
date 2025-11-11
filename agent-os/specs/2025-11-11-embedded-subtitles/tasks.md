# Task Breakdown: Embedded Subtitles

## Overview
Total Tasks: 5 task groups, 60+ sub-tasks

## Task List

### Database Layer

#### Task Group 1: Subtitle Models and Migrations
**Dependencies:** Video Upload (Task Group 1), Automatic Transcription (Task Group 1)

- [ ] 1.0 Complete database layer
  - [ ] 1.1 Write 2-8 focused tests for SubtitleStyle model functionality
    - Test SubtitleStyle model creation with required fields (video_id, language_code)
    - Test SubtitleStyle model validation (color format validation, numeric ranges)
    - Test SubtitleStyle model default values (font_family, font_size, position, etc.)
    - Test SubtitleStyle unique constraint on (video_id, language_code)
    - Test SubtitleStyle relationships with Video and User
    - Test SubtitleStyle cascade delete when video is deleted
    - Test SubtitleStyle enum validation (position_vertical, animation_type, etc.)
  - [ ] 1.2 Create SubtitleStyle model with validations
    - Fields: id (UUID), video_id (foreign key to videos), language_code (string, ISO 639-1)
    - Font properties: font_family (string, default 'Arial'), font_size (integer, default 24, range 12-72)
    - Font properties: font_weight (enum: 'normal', 'bold', default 'bold'), font_color (string, default '#FFFFFF')
    - Font properties: font_alpha (float, default 1.0, range 0.0-1.0)
    - Background properties: background_enabled (boolean, default true), background_color (string, default '#000000')
    - Background properties: background_alpha (float, default 0.7), background_padding (integer, default 10)
    - Background properties: background_radius (integer, default 4)
    - Outline properties: outline_enabled (boolean, default true), outline_color (string, default '#000000')
    - Outline properties: outline_width (integer, default 2, range 0-8)
    - Position properties: position_vertical (enum: 'top', 'center', 'bottom', default 'bottom')
    - Position properties: position_horizontal (enum: 'left', 'center', 'right', default 'center')
    - Position properties: margin_vertical (integer, default 50), margin_horizontal (integer, default 40)
    - Position properties: max_width_percent (integer, default 80, range 20-100)
    - Timing properties: words_per_line (integer, default 7), max_lines (integer, default 2)
    - Timing properties: min_display_duration (float, default 1.0), max_display_duration (float, default 6.0)
    - Animation properties: animation_type (enum: 'none', 'fade', 'slide', 'pop', default 'none')
    - Animation properties: animation_duration (float, default 0.3)
    - Metadata: preset_name (string, nullable), is_template (boolean, default false)
    - Metadata: created_by (UUID, foreign key to User), created_at, updated_at
    - Reuse pattern from: Video model in `backend/app/models/video.py`
  - [ ] 1.3 Write 2-8 focused tests for SubtitleTranslation model functionality
    - Test SubtitleTranslation model creation with required fields (video_id, source_language, target_language)
    - Test SubtitleTranslation unique constraint on (video_id, target_language)
    - Test SubtitleTranslation segments JSONB field storage and retrieval
    - Test SubtitleTranslation status enum validation (pending, processing, completed, failed)
    - Test SubtitleTranslation relationships with Video
    - Test SubtitleTranslation cascade delete when video is deleted
    - Test SubtitleTranslation character and word count calculations
  - [ ] 1.4 Create SubtitleTranslation model with validations
    - Fields: id (UUID), video_id (foreign key to videos), source_language (string, ISO 639-1)
    - Fields: target_language (string, ISO 639-1), translation_service (string, default 'google')
    - Fields: translation_quality (enum: 'machine', 'reviewed', 'professional', default 'machine')
    - Fields: segments (JSONB array with start_time, end_time, original_text, translated_text, confidence)
    - Fields: character_count (integer), word_count (integer)
    - Fields: status (enum: 'pending', 'processing', 'completed', 'failed', default 'pending')
    - Fields: error_message (text, nullable), created_at, updated_at
    - Reuse pattern from: Transcript model in `backend/app/models/transcript.py`
  - [ ] 1.5 Write 2-8 focused tests for SubtitleStylePreset model functionality
    - Test SubtitleStylePreset model creation with system presets
    - Test SubtitleStylePreset unique constraint on name
    - Test SubtitleStylePreset style_config JSONB field storage
    - Test SubtitleStylePreset usage_count tracking
    - Test SubtitleStylePreset system preset protection (cannot delete if is_system_preset is true)
    - Test SubtitleStylePreset relationships with User
    - Test SubtitleStylePreset public/private visibility (is_public flag)
  - [ ] 1.6 Create SubtitleStylePreset model with validations
    - Fields: id (UUID), name (string, unique), description (string)
    - Fields: platform (enum: 'youtube', 'tiktok', 'instagram', 'linkedin', 'custom')
    - Fields: thumbnail_url (string, nullable), style_config (JSONB)
    - Fields: usage_count (integer, default 0), is_system_preset (boolean, default false)
    - Fields: is_public (boolean, default true), created_by (UUID, nullable, foreign key to User)
    - Fields: created_at, updated_at
  - [ ] 1.7 Create migrations for subtitle tables
    - Migration for subtitles_styles table with all fields
    - Add index on video_id for fast lookups
    - Add index on language_code for filtering
    - Add unique constraint on (video_id, language_code)
    - Add foreign key relationships to videos and users tables
    - Migration for subtitles_translations table with all fields
    - Add index on video_id for fast lookups
    - Add index on target_language for filtering
    - Add index on status for filtering
    - Add unique constraint on (video_id, target_language)
    - Migration for subtitles_style_presets table with all fields
    - Add unique constraint on name
    - Add index on platform for filtering
    - Add index on is_public for filtering
  - [ ] 1.8 Seed database with system presets
    - Create YouTube Default preset (Arial bold 32px, white text, black outline, bottom center)
    - Create TikTok Viral preset (Montserrat ExtraBold 48px, yellow with black background, center)
    - Create Instagram Reels preset (Poppins Bold 36px, white with black background, bottom center)
    - Create LinkedIn Professional preset (Roboto 28px, dark gray on white, bottom center)
    - Create Accessibility High Contrast preset (Arial 40px, yellow on black, large margins)
    - Create Minimalist preset (Inter 24px, white with subtle shadow, no background)
    - Mark all system presets with is_system_preset=true
  - [ ] 1.9 Set up associations
    - SubtitleStyle belongs_to Video (video_id foreign key)
    - SubtitleStyle belongs_to User (created_by foreign key)
    - Video has_many SubtitleStyles (relationship defined)
    - SubtitleTranslation belongs_to Video (video_id foreign key)
    - Video has_many SubtitleTranslations (relationship defined)
    - SubtitleStylePreset belongs_to User (created_by foreign key, nullable)
  - [ ] 1.10 Ensure database layer tests pass
    - Run ONLY the 2-8 tests written in 1.1, 1.3, 1.5
    - Verify migrations run successfully
    - Verify system presets are seeded
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1, 1.3, 1.5 pass
- SubtitleStyle, SubtitleTranslation, SubtitleStylePreset models pass validation tests
- Migrations run successfully
- System presets are seeded in database
- Associations work correctly
- Unique constraints and indexes are created

### Backend Services Layer

#### Task Group 2: Subtitle Services (Styling, Burning, Translation)
**Dependencies:** Task Group 1, ARQ Worker setup, FFmpeg installed

- [ ] 2.0 Complete subtitle services
  - [ ] 2.1 Write 2-8 focused tests for SubtitleStylingService
    - Test get_or_create_default_style creates style with defaults for new video
    - Test get_or_create_default_style returns existing style for video
    - Test apply_preset loads preset and creates SubtitleStyle
    - Test apply_preset increments preset usage_count
    - Test update_style validates and updates properties
    - Test validate_style rejects invalid color formats
    - Test validate_style rejects out-of-range numeric values
    - Test clone_style copies style to new video
  - [ ] 2.2 Create SubtitleStylingService class
    - Create file: `backend/app/services/subtitle_styling.py`
    - Method: get_or_create_default_style(video_id: UUID, language: str) -> SubtitleStyle
    - Method: apply_preset(video_id: UUID, preset_name: str, language: str) -> SubtitleStyle
    - Method: update_style(style_id: UUID, updates: dict) -> SubtitleStyle
    - Method: clone_style(source_style_id: UUID, target_video_id: UUID) -> SubtitleStyle
    - Method: validate_style(style_data: dict) -> dict[str, list[str]]
    - Method: generate_style_preview_image(style: SubtitleStyle, sample_text: str) -> bytes
    - Method: export_style_as_preset(style_id: UUID, name: str, description: str) -> SubtitleStylePreset
    - Validation: Font size (12-72), opacity (0.0-1.0), outline width (0-8), margins (0-200)
    - Validation: Max width percent (20-100), color values (hex format #RRGGBB or #RRGGBBAA)
    - Error handling: Detailed validation error messages
  - [ ] 2.3 Write 2-8 focused tests for SubtitleBurningService
    - Test generate_ass_subtitle_file creates valid ASS format
    - Test generate_srt_subtitle_file creates valid SRT format
    - Test ASS format color conversion (hex to &HAABBGGRR format)
    - Test ASS format position mapping (alignment codes)
    - Test SRT format timing conversion (HH:MM:SS,mmm format)
    - Test subtitle segment grouping (words_per_line, max_lines)
    - Test burn_subtitles end-to-end with sample video
    - Test FFmpeg command generation with various styles
  - [ ] 2.4 Create SubtitleBurningService class
    - Create file: `backend/app/services/subtitle_burning.py`
    - Method: burn_subtitles(video_id: UUID, language: str, output_format: str = 'mp4') -> str
    - Method: generate_ass_subtitle_file(video_id: UUID, style: SubtitleStyle, language: str) -> str
    - Method: generate_srt_subtitle_file(video_id: UUID, language: str) -> str
    - Method: apply_ffmpeg_subtitle_burn(video_path: str, subtitle_path: str, output_path: str, style: SubtitleStyle) -> None
    - Method: estimate_burn_duration(video_duration: float, resolution: str) -> float
    - Method: validate_subtitle_file(subtitle_path: str, format: str) -> bool
    - ASS generation: Create proper header with style definitions
    - ASS generation: Map SubtitleStyle properties to ASS Style format
    - ASS generation: Convert hex colors to ASS color format (&HAABBGGRR)
    - ASS generation: Handle position using Alignment codes (1-9 numpad layout)
    - SRT generation: Standard format with timing and text
    - SRT generation: Group words into lines based on words_per_line
    - SRT generation: Respect max_lines and display duration limits
    - FFmpeg integration: Use subtitles filter to burn subtitles
    - FFmpeg integration: Command: `ffmpeg -i input.mp4 -vf "ass=subtitles.ass" -c:a copy output.mp4`
    - Error handling: Validate FFmpeg installed, check video exists, verify disk space
    - Performance: Hardware acceleration if available, stream processing, cache subtitle files
  - [ ] 2.5 Write 2-8 focused tests for SubtitleTranslationService
    - Test translate_subtitles translates all segments
    - Test translate_batch handles multiple texts in single API call
    - Test detect_language returns ISO 639-1 code
    - Test get_supported_languages returns cached list
    - Test estimate_translation_cost calculates correctly
    - Test validate_translation_quality checks length ratio
    - Test create_manual_translation validates segment structure
    - Mock Google Translate API calls
  - [ ] 2.6 Create SubtitleTranslationService class
    - Create file: `backend/app/services/subtitle_translation.py`
    - Method: translate_subtitles(video_id: UUID, source_lang: str, target_lang: str) -> SubtitleTranslation
    - Method: translate_batch(texts: list[str], source_lang: str, target_lang: str) -> list[dict]
    - Method: detect_language(text: str) -> str
    - Method: get_supported_languages() -> list[dict]
    - Method: estimate_translation_cost(character_count: int) -> float
    - Method: validate_translation_quality(original: str, translated: str, target_lang: str) -> float
    - Method: create_manual_translation(video_id: UUID, target_lang: str, segments: list[dict]) -> SubtitleTranslation
    - Google Translate API integration: Use google-cloud-translate library
    - Batch translation: Up to 100 segments per API call
    - Supported languages: 18+ languages (en, es, fr, de, pt, ru, zh, ja, ko, ar, it, nl, pl, tr, hi, vi, th, id)
    - Cost management: Track character count, estimate cost before translation
    - Quality: Allow manual editing, preserve formatting, handle context
    - Error handling: API quotas, retries with exponential backoff, store partial results
  - [ ] 2.7 Ensure services layer tests pass
    - Run ONLY the 2-8 tests written in 2.1, 2.3, 2.5
    - Verify all services work correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1, 2.3, 2.5 pass
- SubtitleStylingService creates and manages styles correctly
- SubtitleBurningService generates valid ASS/SRT files
- SubtitleBurningService burns subtitles with FFmpeg successfully
- SubtitleTranslationService translates subtitles using Google Translate API
- All validation and error handling works correctly

### Backend API and Worker Layer

#### Task Group 3: API Endpoints and Background Jobs
**Dependencies:** Task Group 2

- [ ] 3.0 Complete API and worker layer
  - [ ] 3.1 Write 2-8 focused tests for style management endpoints
    - Test GET /api/videos/{id}/subtitle-styles returns all styles
    - Test GET /api/videos/{id}/subtitle-styles?language=en filters by language
    - Test GET /api/subtitle-styles/{id} returns single style
    - Test POST /api/videos/{id}/subtitle-styles creates new style
    - Test PATCH /api/subtitle-styles/{id} updates style
    - Test DELETE /api/subtitle-styles/{id} deletes style
    - Test POST /api/subtitle-styles/{id}/clone clones style to another video
    - Test authorization (users can only access their own video styles)
  - [ ] 3.2 Create style management API endpoints
    - GET /api/videos/{id}/subtitle-styles: List all subtitle styles for video
    - GET /api/subtitle-styles/{id}: Get single subtitle style
    - POST /api/videos/{id}/subtitle-styles: Create new subtitle style
    - PATCH /api/subtitle-styles/{id}: Update subtitle style
    - DELETE /api/subtitle-styles/{id}: Delete subtitle style
    - POST /api/subtitle-styles/{id}/clone: Clone style to another video
    - Implement authentication using get_current_user dependency
    - Implement authorization (check video ownership)
    - Validate all style properties using Pydantic schemas
    - Create file: `backend/app/api/routes/subtitle_styles.py`
  - [ ] 3.3 Write 2-8 focused tests for preset management endpoints
    - Test GET /api/subtitle-presets returns all presets
    - Test GET /api/subtitle-presets?platform=youtube filters by platform
    - Test GET /api/subtitle-presets/{name} returns specific preset
    - Test POST /api/videos/{id}/subtitle-styles/apply-preset applies preset
    - Test POST /api/subtitle-presets creates custom preset
    - Test DELETE /api/subtitle-presets/{name} deletes custom preset
    - Test DELETE /api/subtitle-presets/{name} rejects system preset deletion
  - [ ] 3.4 Create preset management API endpoints
    - GET /api/subtitle-presets: List all available presets
    - GET /api/subtitle-presets/{name}: Get specific preset
    - POST /api/videos/{id}/subtitle-styles/apply-preset: Apply preset to video
    - POST /api/subtitle-presets: Create custom preset from style
    - DELETE /api/subtitle-presets/{name}: Delete custom preset (only creator, not system presets)
    - Query params for filtering: platform, is_public, sort (popular, recent, name)
    - Track preset usage_count when applied
    - Create file: `backend/app/api/routes/subtitle_presets.py`
  - [ ] 3.5 Write 2-8 focused tests for subtitle burning endpoints
    - Test POST /api/videos/{id}/burn-subtitles enqueues job
    - Test GET /api/videos/{id}/burn-subtitles/progress returns progress
    - Test GET /api/videos/{id}/subtitled-versions lists versions
    - Test burn-subtitles validates transcript exists
    - Test burn-subtitles validates style exists
    - Test burn-subtitles returns estimated duration
  - [ ] 3.6 Create subtitle burning API endpoints
    - POST /api/videos/{id}/burn-subtitles: Trigger subtitle burning
    - GET /api/videos/{id}/burn-subtitles/progress: Get burning progress
    - GET /api/videos/{id}/subtitled-versions: List all versions with burned subtitles
    - Body for burn: {language, style_id (optional), output_format (default 'mp4')}
    - Return job_id and estimated_duration
    - Track progress in Redis with key format: burn_progress:{video_id}
    - Create file: `backend/app/api/routes/subtitle_burning.py`
  - [ ] 3.7 Write 2-8 focused tests for translation endpoints
    - Test GET /api/videos/{id}/translations lists all translations
    - Test POST /api/videos/{id}/translations creates translations
    - Test POST /api/videos/{id}/translations estimates cost
    - Test GET /api/translations/{id} returns translation details
    - Test PATCH /api/translations/{id}/segments updates segments
    - Test PATCH updates translation_quality to 'reviewed'
    - Test DELETE /api/translations/{id} deletes translation
    - Test POST /api/videos/{id}/translations/export exports SRT/VTT
  - [ ] 3.8 Create translation API endpoints
    - GET /api/videos/{id}/translations: List all translations
    - POST /api/videos/{id}/translations: Create new translation
    - GET /api/translations/{id}: Get translation details
    - PATCH /api/translations/{id}/segments: Update translated segments (manual corrections)
    - DELETE /api/translations/{id}: Delete translation
    - POST /api/videos/{id}/translations/export: Export translation as SRT/VTT file
    - Body for create: {target_languages: string[], source_language (optional)}
    - Return job_ids and estimated_cost
    - Update translation_quality to 'reviewed' when manually edited
    - Create file: `backend/app/api/routes/subtitle_translations.py`
  - [ ] 3.9 Write 2-8 focused tests for preview endpoints
    - Test POST /api/subtitle-styles/{id}/preview generates preview image
    - Test GET /api/videos/{id}/subtitle-preview generates preview clip
    - Test preview caching (returns cached result on second request)
    - Test preview expiration (1 hour TTL)
  - [ ] 3.10 Create preview API endpoints
    - POST /api/subtitle-styles/{id}/preview: Generate preview image
    - GET /api/videos/{id}/subtitle-preview: Preview video segment with subtitles
    - Body for image: {sample_text (optional, default "Sample subtitle text")}
    - Query params for video: start_time, duration, language, style_id
    - Return preview_url and expires_at
    - Cache preview clips for 1 hour in Redis
    - Create file: `backend/app/api/routes/subtitle_previews.py`
  - [ ] 3.11 Create Pydantic schemas for request/response validation
    - SubtitleStyleResponse schema with all style properties
    - SubtitleStyleCreate/Update schemas for validation
    - SubtitleTranslationResponse schema with segments
    - SubtitleTranslationCreate schema for validation
    - TranslationSegment schema (start_time, end_time, original_text, translated_text, confidence)
    - SubtitleStylePresetResponse schema
    - BurnSubtitlesRequest schema (language, style_id, output_format)
    - BurnSubtitlesProgress schema (progress, status, estimated_time_remaining, current_stage)
    - SubtitledVersion schema (language, created_at, file_size, download_url)
    - TranslationCostEstimate schema (character_count, cost_per_language, total_cost, languages)
    - Create file: `backend/app/schemas/subtitles.py`
  - [ ] 3.12 Create ARQ background jobs
    - ARQ task: burn_subtitles_job(video_id: str, language: str, style_id: str = None) -> dict
    - Task stages: Download video (10%), Generate subtitle file (20%), FFmpeg processing (30-90%), Upload (90-100%)
    - Track progress in Redis: burn_progress:{video_id}
    - Update video metadata with subtitle_burned flag
    - Return {status, output_url, duration}
    - ARQ task: translate_subtitles_job(video_id: str, target_languages: list[str]) -> dict
    - Task stages: Detect language (10%), Translate batches (20-80%), Store results (80-100%)
    - Track progress in Redis: translation_progress:{video_id}:{language}
    - Return {status, translations: [{language, segment_count, character_count}]}
    - ARQ task: batch_burn_subtitles_job(video_ids: list[str], language: str, preset_name: str) -> dict
    - Process multiple videos with same styling
    - Generate batch export ZIP file
    - Return {status, processed_count, failed_count, download_url}
    - Register all tasks in worker.py
    - Job timeouts: Burning 20 minutes, Translation 5 minutes per language
    - Retry logic: Max 2 attempts for FFmpeg operations
    - Clean up temporary files on error
  - [ ] 3.13 Ensure API and worker layer tests pass
    - Run ONLY the 2-8 tests written in 3.1, 3.3, 3.5, 3.7, 3.9
    - Verify all endpoints work correctly
    - Verify ARQ jobs process successfully
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 3.1, 3.3, 3.5, 3.7, 3.9 pass
- All API endpoints work correctly with proper authentication and authorization
- Style management endpoints create, read, update, delete styles
- Preset management endpoints list, apply, create presets
- Subtitle burning endpoints trigger jobs and track progress
- Translation endpoints create, retrieve, update, export translations
- Preview endpoints generate images and video clips
- ARQ background jobs process videos and translations successfully
- Progress tracking works in Redis

### Frontend Components Layer

#### Task Group 4: Subtitle UI Components
**Dependencies:** Task Group 3

- [ ] 4.0 Complete subtitle UI components
  - [ ] 4.1 Write 2-8 focused tests for SubtitleStyleEditor component
    - Test SubtitleStyleEditor renders all style control sections
    - Test SubtitleStyleEditor updates preview on style changes
    - Test SubtitleStyleEditor applies preset
    - Test SubtitleStyleEditor saves style to database
    - Test SubtitleStyleEditor resets to last saved state
    - Test SubtitleStyleEditor validates color formats
    - Test SubtitleStyleEditor validates numeric ranges
  - [ ] 4.2 Create TypeScript type definitions
    - Define SubtitleStyle interface with all properties
    - Define SubtitleStylePreset interface
    - Define SubtitleTranslation interface
    - Define TranslationSegment interface
    - Define BurnSubtitlesProgress interface
    - Define SubtitledVersion interface
    - Define LanguageInfo interface
    - Define TranslationCostEstimate interface
    - Create file: `frontend/src/types/subtitles.ts`
  - [ ] 4.3 Create frontend API client functions
    - getSubtitleStyles(videoId, language?): Fetch styles for video
    - getSubtitleStyle(styleId): Fetch single style
    - createSubtitleStyle(videoId, styleData): Create new style
    - updateSubtitleStyle(styleId, updates): Update style
    - deleteSubtitleStyle(styleId): Delete style
    - cloneSubtitleStyle(styleId, targetVideoId): Clone style
    - getSubtitlePresets(platform?): Fetch presets
    - getSubtitlePreset(name): Fetch specific preset
    - applySubtitlePreset(videoId, presetName, language): Apply preset
    - createSubtitlePreset(styleId, name, description, isPublic): Create preset
    - burnSubtitles(videoId, language, styleId?, outputFormat?): Trigger burn job
    - getBurnProgress(videoId): Get burn progress
    - getSubtitledVersions(videoId): List subtitled versions
    - getTranslations(videoId): Fetch translations
    - createTranslation(videoId, targetLanguages, sourceLanguage?): Create translations
    - getTranslation(translationId): Fetch translation
    - updateTranslationSegments(translationId, segments): Update segments
    - deleteTranslation(translationId): Delete translation
    - exportTranslation(videoId, language, format): Export SRT/VTT
    - generateStylePreview(styleId, sampleText?): Generate preview image
    - getSubtitlePreviewVideo(videoId, startTime, duration, language, styleId): Get preview video
    - detectLanguage(videoId): Auto-detect language
    - getSupportedLanguages(): Get supported languages
    - All functions use apiClient with error handling and TypeScript types
    - Create or update: `frontend/src/lib/api/subtitles.ts`
  - [ ] 4.4 Create SubtitleStyleEditor component
    - Client component for customizing subtitle styling
    - Props: videoId (string), language (string, default 'en'), initialStyle (optional), onSave (optional)
    - Layout: Split view - Editor controls (left 40%) + Live preview (right 60%)
    - Editor sections (collapsible accordions):
      1. Font Settings: font_family, font_size, font_weight, font_color
      2. Background Settings: background_enabled, background_color, background_alpha, padding, radius
      3. Outline Settings: outline_enabled, outline_color, outline_width
      4. Position Settings: position_vertical, position_horizontal, margins, max_width
      5. Timing Settings: words_per_line, max_lines, min/max display duration
      6. Animation Settings: animation_type, animation_duration
    - Preset selector: Dropdown with platform presets, quick apply, save as preset
    - Action buttons: Save, Reset, Copy from another video, Export JSON
    - Real-time preview: Debounce updates (300ms), update preview as user adjusts
    - Keyboard shortcuts: Ctrl+S (save), Ctrl+Z (undo), Ctrl+Shift+Z (redo)
    - Undo/redo functionality for style changes
    - Validation with inline error messages
    - Responsive: Stack vertically on mobile
    - Shadcn components: Accordion, Slider, Select, Input, ColorPicker, RadioGroup, Button
    - Create file: `frontend/src/components/subtitles/SubtitleStyleEditor.tsx`
  - [ ] 4.5 Write 2-8 focused tests for SubtitlePreview component
    - Test SubtitlePreview renders static preview with style
    - Test SubtitlePreview updates on style changes
    - Test SubtitlePreview shows video preview mode
    - Test SubtitlePreview applies all style properties correctly
    - Test SubtitlePreview shows contrast warning for low contrast
  - [ ] 4.6 Create SubtitlePreview component
    - Client component for real-time subtitle preview
    - Props: videoId (string), style (SubtitleStyle), sampleText (optional), showVideo (boolean), autoUpdate (boolean)
    - Preview modes: Static image, Video segment, Full timeline
    - Static preview: Canvas or styled HTML div, sample text with all styles applied
    - Video preview: Short video segment with CSS overlay (not burned)
    - Subtitle rendering: Position, font styles, colors, background, outline, margins
    - Multi-line support with proper line breaking
    - Show animation if enabled
    - Accessibility: High contrast warning (<4.5:1), suggest alternative colors
    - Performance: Memoize rendering, throttle updates, lazy load video
    - Create file: `frontend/src/components/subtitles/SubtitlePreview.tsx`
  - [ ] 4.7 Write 2-8 focused tests for TranslationPanel component
    - Test TranslationPanel renders language selection
    - Test TranslationPanel shows cost estimation
    - Test TranslationPanel triggers translation
    - Test TranslationPanel displays translation list
    - Test TranslationPanel opens editor for translation
    - Test TranslationPanel exports translation
  - [ ] 4.8 Create TranslationPanel component
    - Client component for managing subtitle translations
    - Props: videoId (string), sourceLanguage (string), onTranslationComplete (optional)
    - Sections:
      1. Source Language Detection: Auto-detect button, manual override, display confidence
      2. Target Languages Selection: Multi-select with search, popular languages, flags
      3. Translation Settings: Service selection, quality preference, preserve formatting
      4. Cost Estimation: Character count, cost per language, total, remaining quota
      5. Translation List: Table with language, status, segments, actions
    - Translation workflow: Select languages → Show estimate → Confirm → Show progress
    - Translation editor: Modal with side-by-side view (original | translation)
    - Segment-by-segment editing with timing display
    - Export options: SRT, VTT, burn into video
    - Progress tracking: Real-time progress bars, WebSocket or polling, estimated time
    - Error handling: Display errors, retry button, show partial results
    - Shadcn components: Select, Checkbox, Table, Progress, Dialog, Button, Badge, Alert
    - Create file: `frontend/src/components/subtitles/TranslationPanel.tsx`
  - [ ] 4.9 Write 2-8 focused tests for SubtitleBurnDialog component
    - Test SubtitleBurnDialog renders language selection
    - Test SubtitleBurnDialog shows style preview
    - Test SubtitleBurnDialog triggers burn job
    - Test SubtitleBurnDialog displays progress
    - Test SubtitleBurnDialog handles completion
    - Test SubtitleBurnDialog handles errors
  - [ ] 4.10 Create SubtitleBurnDialog component
    - Client component for configuring and triggering subtitle burning
    - Props: videoId (string), onBurnStart (optional), onBurnComplete (optional)
    - Dialog content:
      1. Language Selection: Dropdown for subtitle language (original + translations)
      2. Style Selection: Radio group (use existing vs. apply preset)
      3. Output Settings: Format (MP4, AVI, MOV), quality, filename
      4. Preview: Show preview with selected style
      5. Burn Button: Primary button with estimated time
    - After clicking: Trigger API, close dialog, show progress notification
    - Progress modal: Progress bar, current stage, cancel button, estimated time
    - Completion: Success notification with download link, view/download options
    - Error handling: Display error, retry button, support link
    - Shadcn components: Dialog, Select, RadioGroup, Input, Button, Progress, Alert
    - Create file: `frontend/src/components/subtitles/SubtitleBurnDialog.tsx`
  - [ ] 4.11 Write 2-8 focused tests for SubtitleLanguageSelector component
    - Test SubtitleLanguageSelector displays available languages
    - Test SubtitleLanguageSelector shows original badge
    - Test SubtitleLanguageSelector filters languages
    - Test SubtitleLanguageSelector triggers onChange
    - Test SubtitleLanguageSelector shows add translation option
  - [ ] 4.12 Create SubtitleLanguageSelector component
    - Client component for selecting subtitle language
    - Props: videoId (string), selectedLanguage (optional), onChange (function), showAddTranslation (boolean)
    - Dropdown showing: Original (with badge), all translations (sorted), add new translation
    - Each option: Flag icon, language name (English), native name, segment count/status
    - "Add Translation" option opens TranslationPanel or language picker
    - Keyboard navigation and search/filter support
    - Shadcn components: Select with custom rendering
    - Create file: `frontend/src/components/subtitles/SubtitleLanguageSelector.tsx`
  - [ ] 4.13 Write 2-8 focused tests for SubtitleTimeline component
    - Test SubtitleTimeline renders subtitle segments
    - Test SubtitleTimeline highlights current segment
    - Test SubtitleTimeline handles segment click
    - Test SubtitleTimeline supports zoom controls
    - Test SubtitleTimeline colors segments based on duration
  - [ ] 4.14 Create SubtitleTimeline component
    - Client component showing subtitle segments on timeline
    - Props: videoId (string), language (string), videoDuration (number), currentTime (optional), onSegmentClick (optional)
    - Visual timeline: Horizontal timeline, colored blocks for segments, hover for text
    - Features: Zoom controls, scroll/pan, click to seek, highlight active
    - Segment coloring: Default (blue), active (green), long >6s (yellow), short <1s (orange)
    - Integration: Sync with video player, click to seek
    - Use React-Konva or canvas library for performance
    - Responsive: Adjust size based on container width
    - Create file: `frontend/src/components/subtitles/SubtitleTimeline.tsx`
  - [ ] 4.15 Ensure UI component tests pass
    - Run ONLY the 2-8 tests written in 4.1, 4.5, 4.7, 4.9, 4.11, 4.13
    - Verify all components render correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 4.1, 4.5, 4.7, 4.9, 4.11, 4.13 pass
- SubtitleStyleEditor renders all controls and updates preview
- SubtitlePreview renders styled text with all properties
- TranslationPanel manages translations and shows progress
- SubtitleBurnDialog configures and triggers burning
- SubtitleLanguageSelector displays available languages
- SubtitleTimeline shows segments on timeline
- All components integrate with video player
- Responsive design works on mobile

### Integration and Testing Layer

#### Task Group 5: Integration, E2E Tests, and Quality Assurance
**Dependencies:** Task Groups 1-4

- [ ] 5.0 Complete integration and testing
  - [ ] 5.1 Review tests from Task Groups 1-4
    - Review database layer tests (Task Group 1)
    - Review services layer tests (Task Group 2)
    - Review API and worker layer tests (Task Group 3)
    - Review UI component tests (Task Group 4)
  - [ ] 5.2 Analyze test coverage gaps
    - Identify missing edge cases (empty transcripts, invalid inputs, API failures)
    - Identify missing integration tests (end-to-end workflows)
    - Identify missing error handling tests
    - Check coverage for all API endpoints
    - Check coverage for all UI components
    - Check coverage for all background jobs
  - [ ] 5.3 Write up to 15 additional strategic tests
    - Integration test: Create style → Burn subtitles → Download video
    - Integration test: Apply preset → Customize → Save as custom preset
    - Integration test: Translate subtitles → Edit translation → Export SRT
    - Integration test: Burn subtitles in multiple languages → Compare outputs
    - Integration test: Clone style from one video to another
    - Error handling: Missing transcript error handling
    - Error handling: FFmpeg failure and retry logic
    - Error handling: Translation API quota exceeded
    - Edge case: Very long video (>1 hour) subtitle burning
    - Edge case: Very short subtitles (<1 second display duration)
    - Edge case: RTL language support (Arabic, Hebrew)
    - Edge case: Special characters and emoji in subtitles
    - Performance test: Concurrent subtitle burning jobs
    - Performance test: Translation with large character count (>50k)
    - Visual regression test: Subtitle rendering accuracy
  - [ ] 5.4 Write E2E tests for complete workflows
    - E2E: User uploads video → Transcribes → Creates style → Burns subtitles → Downloads
    - E2E: User applies TikTok preset → Previews → Burns → Exports
    - E2E: User translates to 3 languages → Edits Spanish translation → Burns Spanish version
    - E2E: User creates custom style → Saves as preset → Applies to another video
    - E2E: User burns subtitles in 5 languages → Downloads all versions
    - Create file: `frontend/tests/e2e/embedded-subtitles.spec.ts`
  - [ ] 5.5 Integration tests for video editor
    - Test "Subtitles" tab in video editor shows SubtitleStyleEditor
    - Test SubtitleTimeline integrated into timeline view
    - Test quick burn button in export menu
    - Test subtitle preview in video player
  - [ ] 5.6 Integration tests for dashboard
    - Test "Subtitles Available" badge on video cards
    - Test translated language count display
    - Test quick access to burn subtitles from dashboard
  - [ ] 5.7 Integration tests for export flow
    - Test "Export with Subtitles" option in export dialog
    - Test language and style selection before export
    - Test generated subtitled version alongside original
  - [ ] 5.8 Performance tests
    - Test FFmpeg burning speed for 1080p 30-min video (target: <3 minutes)
    - Test translation speed for 10,000 characters (target: <2 minutes)
    - Test preview generation speed (target: <500ms)
    - Test concurrent burning jobs (5 videos simultaneously)
    - Measure memory usage during subtitle burning
  - [ ] 5.9 Accessibility tests
    - Test color contrast validation (WCAG 2.1 AA: 4.5:1 minimum)
    - Test subtitle readability against various backgrounds
    - Test keyboard navigation in SubtitleStyleEditor
    - Test screen reader compatibility
  - [ ] 5.10 Quality assurance checks
    - Verify subtitle timing accuracy (no overlaps, proper display duration)
    - Verify subtitle positioning on different aspect ratios (16:9, 9:16, 4:3)
    - Verify all 6 system presets render correctly
    - Verify RTL language support (text flow, alignment)
    - Verify special character handling (emojis, accents, CJK)
    - Verify output video quality and file size
  - [ ] 5.11 Run complete test suite
    - Run all backend tests: pytest --cov=app
    - Run all frontend tests: npm test
    - Run E2E tests: npm run test:e2e
    - Verify test coverage >90% for subtitle-related code
    - Fix any failing tests
  - [ ] 5.12 Create test documentation
    - Document test scenarios and expected results
    - Document known limitations and edge cases
    - Document FFmpeg requirements and setup
    - Document Google Translate API setup and quotas
    - Create file: `agent-os/specs/2025-11-11-embedded-subtitles/testing-guide.md`

**Acceptance Criteria:**
- All tests from Task Groups 1-4 pass
- Additional strategic tests are written and pass
- E2E tests cover complete workflows
- Integration tests verify all feature connections
- Performance tests meet target metrics
- Accessibility tests pass WCAG 2.1 AA
- Test coverage >90% for subtitle-related code
- No critical bugs or edge cases remaining
- All system presets work correctly
- Documentation is complete

## Execution Order
1. Database Layer (Task Group 1)
2. Backend Services Layer (Task Group 2)
3. Backend API and Worker Layer (Task Group 3)
4. Frontend Components Layer (Task Group 4)
5. Integration and Testing Layer (Task Group 5)

## Notes
- FFmpeg must be installed and accessible on the system
- Google Cloud Translation API credentials must be configured
- Test with sample videos of various lengths and resolutions
- Monitor API usage and costs during development
- Consider hardware acceleration for faster subtitle burning
- Cache generated subtitle files and previews for performance
- Implement proper error handling for all external dependencies
- Follow CLAUDE.md guidelines for code quality and testing
