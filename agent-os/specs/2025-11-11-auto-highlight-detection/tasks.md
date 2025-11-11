# Task Breakdown: Auto-Highlight Detection

## Overview
Total Tasks: 5 task groups, 40+ sub-tasks

## Task List

### Database Layer

#### Task Group 1: Highlight Model and Migrations
**Dependencies:** Video Upload (Task Group 1), Automatic Transcription (Task Group 1)

- [ ] 1.0 Complete database layer
  - [ ] 1.1 Write 2-8 focused tests for Highlight model functionality
    - Test Highlight model creation with required fields (video_id, start_time, end_time, overall_score)
    - Test Highlight model validation (video_id foreign key, score ranges 0-100)
    - Test Highlight model component scores (audio_energy_score, scene_change_score, speech_density_score, keyword_score)
    - Test Highlight model detected_keywords array field storage and retrieval
    - Test Highlight model highlight_type enum validation ('high_energy', 'key_moment', 'keyword_match', 'scene_change')
    - Test Highlight model status enum validation ('detected', 'reviewed', 'exported', 'rejected')
    - Test Highlight model relationships with Video
    - Test Highlight model timestamps (created_at, updated_at)
  - [ ] 1.2 Create Highlight model with validations
    - Fields: id (UUID), video_id (foreign key to videos), start_time (float, seconds), end_time (float, seconds)
    - Scoring fields: overall_score (integer 0-100), audio_energy_score (0-100), scene_change_score (0-100), speech_density_score (0-100), keyword_score (0-100)
    - Metadata: detected_keywords (text array), confidence_level (float 0-1), duration_seconds (float)
    - Ranking: rank (integer, 1 = best highlight), highlight_type enum ('high_energy', 'key_moment', 'keyword_match', 'scene_change')
    - Context: context_before_seconds (float, default 2), context_after_seconds (float, default 3)
    - Status: status enum ('detected', 'reviewed', 'exported', 'rejected')
    - Timestamps: created_at, updated_at
    - Reuse pattern from: Video model in `backend/app/models/video.py`
  - [ ] 1.3 Create migration for highlights table
    - Add index on video_id for fast lookups
    - Add index on overall_score DESC for sorting by best highlights
    - Add index on rank for ordered retrieval
    - Add composite index on (video_id, status) for filtered queries
    - Foreign key relationship to videos table with cascade delete
    - Add highlight_type enum type ('high_energy', 'key_moment', 'keyword_match', 'scene_change')
    - Add status enum type ('detected', 'reviewed', 'exported', 'rejected')
    - Array column for detected_keywords
  - [ ] 1.4 Set up associations
    - Highlight belongs_to Video (video_id foreign key)
    - Video has_many Highlights (relationship defined)
    - Add cascade delete (when video deleted, highlights deleted)
  - [ ] 1.5 Ensure database layer tests pass
    - Run ONLY the 2-8 tests written in 1.1
    - Verify migrations run successfully
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1 pass
- Highlight model passes validation tests
- Migrations run successfully
- Associations work correctly
- All indexes are created for optimal query performance

### Backend Analysis Services

#### Task Group 2: Audio, Video, Speech, and Keyword Analysis Services
**Dependencies:** Task Group 1, Video Upload (storage), Automatic Transcription (transcripts)

- [ ] 2.0 Complete analysis services
  - [ ] 2.1 Write 2-8 focused tests for analysis services
    - Test AudioAnalysisService extracts audio energy for test video samples
    - Test AudioAnalysisService detects high-energy segments correctly
    - Test VideoAnalysisService detects scene changes accurately
    - Test SpeechAnalysisService calculates speech density from transcript
    - Test KeywordAnalysisService detects and scores keyword matches
    - Test CompositeScorer calculates weighted overall score correctly
    - Test score normalization to 0-100 range
    - Test bonus multipliers for aligned signals
  - [ ] 2.2 Create AudioAnalysisService for audio feature extraction
    - Extract audio waveform from video using PyAV
    - Calculate audio energy (RMS) for each 0.5-second window
    - Detect high-energy segments (energy > threshold, configurable default 0.6)
    - Identify energy peaks and sustained high-energy periods (>3 seconds)
    - Detect sudden energy changes (peaks after quiet periods)
    - Calculate speech density using voice activity detection (VAD)
    - Identify segments with consistent speech (podcasts) vs varied energy (gaming)
    - Score audio features on 0-100 scale (high energy 80-100, medium 50-79, quiet 0-49)
    - Use librosa or similar for audio feature extraction
    - Return time-series data: List[(start_time, end_time, audio_score)]
    - Create file: `backend/app/services/analysis/audio_analysis.py`
  - [ ] 2.3 Create VideoAnalysisService for scene change detection
    - Detect scene changes using PySceneDetect or custom algorithm
    - Analyze frame-to-frame differences (histogram comparison, pixel differences)
    - Identify significant scene transitions (threshold-based)
    - Detect camera motion and cuts
    - Calculate scene diversity (frequent changes vs static scenes)
    - Score scene changes on 0-100 scale based on frequency and significance
    - Apply timing bonus (changes aligned with audio energy get +10%)
    - Optional: Detect faces and track presence/absence for human-focused content
    - Return time-series data: List[(start_time, end_time, scene_score)]
    - Create file: `backend/app/services/analysis/video_analysis.py`
  - [ ] 2.4 Create SpeechAnalysisService for speech pattern analysis
    - Integrate with existing transcript data (word-level timestamps)
    - Analyze speech patterns: speaking rate (words per minute), pauses, silence duration
    - Detect segments with increased speaking rate (excitement)
    - Identify segments with emphasized words (louder, slower)
    - Calculate speech density score (0-100): high density (fast, no pauses) 80-100, medium 50-79, low 0-49
    - Handle missing transcript gracefully (return neutral scores)
    - Return time-series data: List[(start_time, end_time, speech_score)]
    - Create file: `backend/app/services/analysis/speech_analysis.py`
  - [ ] 2.5 Create KeywordAnalysisService for keyword-based scoring
    - Use existing transcript keyword search functionality
    - Maintain list of "highlight keywords" (user-configurable)
    - Default keywords: ["important", "key", "best", "amazing", "wow", "incredible", "watch", "look", "check", "unbelievable"]
    - Detect keyword matches in transcript within time windows
    - Bonus scoring for keyword clusters (multiple keywords nearby)
    - Weight keywords by importance (user-defined or default weights)
    - Keyword score (0-100): multiple important keywords 80-100, single keyword 50-79, related 30-49, none 0
    - Return time-series data: List[(start_time, end_time, keyword_score, detected_keywords)]
    - Create file: `backend/app/services/analysis/keyword_analysis.py`
  - [ ] 2.6 Create CompositeScorer for weighted score calculation
    - Calculate overall_score as weighted average of component scores
    - Default weights: audio_energy 35%, scene_change 20%, speech_density 25%, keyword 20%
    - Make weights configurable via settings (per-user or global)
    - Apply bonus multipliers: aligned signals +10%, sustained high scores +15%, keywords + high energy +20%
    - Normalize final score to 0-100 range
    - Classify segments: overall_score >= 70 (high), 50-69 (medium), < 50 (low/skip)
    - Return scored segments with all component scores
    - Create file: `backend/app/services/analysis/composite_scorer.py`
  - [ ] 2.7 Implement segment merging and context padding
    - Merge overlapping or adjacent highlights (within 3 seconds)
    - Add context padding (default: 2s before, 3s after)
    - Ensure segments don't exceed video boundaries
    - Prevent duplicate or overlapping final segments
    - Calculate final segment duration_seconds
    - Create file: `backend/app/services/analysis/segment_merger.py`
  - [ ] 2.8 Ensure analysis services tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify all analysis services produce expected output
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- AudioAnalysisService extracts audio features accurately
- VideoAnalysisService detects scene changes reliably
- SpeechAnalysisService analyzes speech patterns correctly
- KeywordAnalysisService detects and scores keywords
- CompositeScorer calculates weighted scores correctly
- Segment merging and padding work as expected
- All services handle edge cases (missing data, errors)

### Backend Detection Service and API

#### Task Group 3: Highlight Detection Service, ARQ Worker, and API Endpoints
**Dependencies:** Task Group 1, Task Group 2

- [ ] 3.0 Complete detection service and API
  - [ ] 3.1 Write 2-8 focused tests for detection endpoints
    - Test POST /api/videos/{id}/highlights/detect triggers detection job
    - Test POST /api/videos/{id}/highlights/detect prevents duplicate detection
    - Test GET /api/videos/{id}/highlights returns all highlights sorted by rank
    - Test GET /api/videos/{id}/highlights filters by status and min_score
    - Test GET /api/highlights/{id} returns single highlight with full details
    - Test PATCH /api/highlights/{id} updates highlight status and rank
    - Test DELETE /api/highlights/{id} soft deletes highlight
    - Test GET /api/videos/{id}/highlights/progress returns detection progress
  - [ ] 3.2 Create HighlightDetectionService orchestrating full workflow
    - Orchestrate full highlight detection workflow
    - Process video in chunks (avoid loading entire video in memory)
    - Run audio, video, and speech analysis in parallel where possible
    - Call AudioAnalysisService, VideoAnalysisService, SpeechAnalysisService, KeywordAnalysisService
    - Combine scores using CompositeScorer
    - Identify discrete highlight segments (start/end times)
    - Merge overlapping/adjacent highlights using SegmentMerger
    - Rank highlights by overall_score (1 = best, 2 = second best, etc.)
    - Limit highlights per video based on sensitivity (default: top 10, configurable 5-20)
    - Store Highlight records in database
    - Cache detection results to avoid reprocessing (Redis cache with video_id key)
    - Create file: `backend/app/services/highlight_detection.py`
  - [ ] 3.3 Create ARQ task: detect_highlights for async processing
    - Task function: detect_highlights(video_id: str, sensitivity: str = 'medium', keywords: List[str] = None)
    - Sensitivity levels: 'low' (top 5, threshold 80), 'medium' (top 10, threshold 70), 'high' (top 15, threshold 60), 'max' (top 20, threshold 50)
    - Download video from S3 using video S3 key
    - Call HighlightDetectionService with video file path
    - Process highlights and apply sensitivity filters
    - Store Highlight records in database with all scores
    - Update video metadata with highlight_count
    - Track progress in Redis (0-100%) with stages: downloading (0-20%), analyzing audio (20-40%), analyzing video (40-60%), analyzing speech (60-80%), scoring and ranking (80-100%)
    - Handle errors with retry logic (max 3 attempts)
    - Job timeout: 15 minutes for standard videos
    - Register task in worker.py
    - Create file: Update `backend/app/worker.py` with new task
  - [ ] 3.4 Implement progress tracking in Redis
    - Track detection progress (0-100%) in Redis
    - Key format: highlight_detection_progress:{video_id}
    - Update progress at key stages: downloading, analyzing audio, analyzing video, analyzing speech, scoring
    - Store current stage name and estimated time remaining
    - Set progress to 100% on completion
    - Clear progress key on completion or failure (TTL: 1 hour)
  - [ ] 3.5 Add API endpoint: POST /api/videos/{id}/highlights/detect
    - Trigger highlight detection job
    - Request body: {sensitivity: 'low' | 'medium' | 'high' | 'max', keywords: string[], score_weights?: {audio_energy, scene_change, speech_density, keyword}}
    - Enqueues ARQ job, returns {job_id: string, message: string}
    - Prevents duplicate detection (check if already processing or recently completed)
    - Requires authentication and video ownership
    - Follow pattern from: `backend/app/api/routes/highlights.py`
  - [ ] 3.6 Add API endpoint: GET /api/videos/{id}/highlights
    - List all highlights for video
    - Query params: status (filter by status), min_score (filter by minimum score), limit (default 50), offset (default 0), sort (default 'rank')
    - Returns {highlights: Highlight[], total: number}
    - Highlights sorted by rank (best first) by default
    - Include segment preview URL placeholder (to be implemented later)
    - Requires authentication and video ownership
  - [ ] 3.7 Add API endpoints: GET/PATCH/DELETE /api/highlights/{id}
    - GET /api/highlights/{id}: Get single highlight details with full score breakdown
    - PATCH /api/highlights/{id}: Update highlight (rank, status, start_time, end_time)
    - DELETE /api/highlights/{id}: Soft delete (mark as rejected) or hard delete based on query param
    - All require authentication and video ownership verification
  - [ ] 3.8 Add API endpoint: GET /api/videos/{id}/highlights/progress
    - Get detection progress percentage
    - Returns {progress: number, status: string, estimated_time_remaining: number, current_stage: string}
    - Used for SSE or polling updates in frontend
    - Requires authentication and video ownership
  - [ ] 3.9 Create Pydantic schemas for request/response validation
    - HighlightDetectionRequest schema (sensitivity, keywords, score_weights)
    - HighlightResponse schema (id, video_id, start_time, end_time, all scores, detected_keywords, rank, highlight_type, status, timestamps)
    - HighlightListResponse schema (highlights, total)
    - HighlightUpdateRequest schema (rank, status, start_time, end_time)
    - HighlightProgress schema (progress, status, estimated_time_remaining, current_stage)
    - SensitivityLevel enum ('low', 'medium', 'high', 'max')
    - HighlightType enum ('high_energy', 'key_moment', 'keyword_match', 'scene_change')
    - HighlightStatus enum ('detected', 'reviewed', 'exported', 'rejected')
    - Create file: `backend/app/schemas/highlight.py`
  - [ ] 3.10 Implement authentication/authorization
    - Use existing auth pattern (get_current_user dependency)
    - Add permission checks (users can only access highlights for their own videos)
    - Verify video ownership before detection, retrieval, or modification
  - [ ] 3.11 Ensure detection service and API tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify all endpoints work correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 3.1 pass
- HighlightDetectionService orchestrates full workflow correctly
- ARQ task processes videos asynchronously with proper error handling
- All API endpoints work correctly with proper validation
- Progress tracking works in Redis
- Authentication and authorization work correctly
- Sensitivity levels produce expected number of highlights

### Frontend Components

#### Task Group 4: Highlights UI Components
**Dependencies:** Task Group 3

- [ ] 4.0 Complete highlights UI components
  - [ ] 4.1 Write 2-8 focused tests for highlights components
    - Test HighlightsPanel fetches and displays highlights
    - Test HighlightsPanel handles loading and error states
    - Test HighlightsPanel sorting and filtering functionality
    - Test HighlightCard displays highlight info and scores correctly
    - Test HighlightCard score breakdown expansion
    - Test HighlightDetectionTrigger triggers detection with settings
    - Test HighlightScoreBreakdown displays all component scores
    - Test HighlightPreview loads and plays highlight segment
  - [ ] 4.2 Create TypeScript type definitions
    - Define Highlight interface (id, video_id, start_time, end_time, overall_score, component scores, detected_keywords, confidence_level, duration_seconds, rank, highlight_type, status, timestamps)
    - Define HighlightType type ('high_energy' | 'key_moment' | 'keyword_match' | 'scene_change')
    - Define HighlightStatus type ('detected' | 'reviewed' | 'exported' | 'rejected')
    - Define HighlightScore interface (audio_energy, scene_change, speech_density, keyword - all 0-100)
    - Define HighlightConfig interface (sensitivity, keywords, score_weights)
    - Define HighlightProgress interface (progress, status, estimated_time_remaining, current_stage)
    - Define SensitivityLevel type ('low' | 'medium' | 'high' | 'max')
    - Define ScoreWeights interface (audio_energy, scene_change, speech_density, keyword - percentages)
    - Create file: `frontend/src/types/highlight.ts`
  - [ ] 4.3 Create frontend API client functions
    - triggerHighlightDetection(videoId, config): Triggers detection, returns Promise<{job_id: string}>
    - getVideoHighlights(videoId, params): Fetches highlights, returns Promise<{highlights: Highlight[], total: number}>
    - getHighlight(highlightId): Fetches single highlight, returns Promise<Highlight>
    - updateHighlight(highlightId, updates): Updates highlight, returns Promise<Highlight>
    - deleteHighlight(highlightId): Deletes highlight, returns Promise<void>
    - getHighlightPreviewUrl(highlightId): Gets preview clip URL, returns Promise<{url: string}>
    - getHighlightDetectionProgress(videoId): Gets detection progress, returns Promise<HighlightProgress>
    - All functions use apiClient with proper error handling and TypeScript types
    - Create or update: `frontend/src/lib/api/highlights.ts`
  - [ ] 4.4 Create HighlightsPanel component (main container)
    - Client component ('use client') managing overall highlights state and layout
    - Props: videoId (string), onHighlightClick (function, optional)
    - State management: highlights (Highlight[]), isLoading, error, sortBy, filterStatus, filterMinScore
    - useEffect hook to fetch highlights on videoId change
    - Conditional rendering: loading state (skeleton loaders), error state, empty state ("Detecting highlights..." or "No highlights detected"), or highlights grid
    - Sorting options: By rank (default), by score, by time - dropdown selector
    - Filtering: By type (multi-select), by min score (slider 0-100), by status (dropdown)
    - Sensitivity selector: Dropdown to trigger re-detection with different sensitivity (low, medium, high, max)
    - Auto-refresh: Poll for highlights if detection is in progress (using getHighlightDetectionProgress)
    - Integration with HighlightCard components in grid layout
    - Integration with HighlightDetectionTrigger component in header
    - Shadcn/ui components: Card, Select, Slider, Badge, Button
    - Create file: `frontend/src/components/highlights/HighlightsPanel.tsx`
  - [ ] 4.5 Create HighlightCard component
    - Client component displaying individual highlight info
    - Props: highlight (Highlight), onClick (function, optional), onAction (function)
    - Card layout with thumbnail placeholder, time range display (MM:SS format), score badge
    - Overall score visualization: Progress bar or circular progress showing overall score with color coding
    - Score color coding: Green (>80), Yellow (70-80), Gray (<70)
    - Highlight type badge: Display highlight_type with appropriate icon and color
    - Score breakdown: Expandable section using Accordion or Collapsible component
    - Integration with HighlightScoreBreakdown component when expanded
    - Detected keywords: Display as small badges below main info
    - Explanation text: Why highlighted (e.g., "High energy audio + keyword 'amazing'")
    - Actions dropdown: Play, Create Clip, Export, Edit Times, Reject - using DropdownMenu
    - Hover effect: Scale and shadow effect on hover
    - Selected state: Border highlight when selected (controlled by parent)
    - Shadcn/ui components: Card, Badge, Button, Progress, Accordion, DropdownMenu
    - Create file: `frontend/src/components/highlights/HighlightCard.tsx`
  - [ ] 4.6 Create HighlightDetectionTrigger component
    - Client component for triggering highlight detection
    - Props: videoId (string), onDetectionStart (function, optional)
    - Button: "Detect Highlights" with Sparkles or Zap icon from lucide-react
    - Settings popover: Opens settings dialog/popover when clicked
    - Sensitivity radio group: Low, Medium (default), High, Max - using RadioGroup component
    - Custom keywords input: Textarea for comma-separated keywords with default suggestions shown
    - Score weights sliders: Optional advanced section with sliders for audio_energy, scene_change, speech_density, keyword weights
    - Detect button: Triggers triggerHighlightDetection API call, shows loading spinner during call
    - Progress display: Show HighlightProgress component if detection in progress
    - Estimated time: Display estimated_time_remaining from progress data
    - Error handling: Display error messages using Alert component with retry option
    - Disable trigger if detection already in progress or recently completed
    - Shadcn/ui components: Button, Popover, RadioGroup, Textarea, Slider, Alert, Label
    - Create file: `frontend/src/components/highlights/HighlightDetectionTrigger.tsx`
  - [ ] 4.7 Create HighlightScoreBreakdown component
    - Client component displaying detailed score breakdown
    - Props: highlight (Highlight), className (string, optional)
    - Visual score breakdown with 4 rows:
    - Audio energy: Progress bar showing audio_energy_score percentage with label and value
    - Scene changes: Progress bar showing scene_change_score percentage with label and value
    - Speech density: Progress bar showing speech_density_score percentage with label and value
    - Keywords: Progress bar showing keyword_score percentage with label and value
    - Color coding per score: Green (>70), Yellow (50-70), Gray (<50)
    - Explanation text for each component (e.g., "High energy detected in audio")
    - Overall score calculation: Show formula (weighted average) and result
    - Interactive tooltips: Hover over each component to see detailed explanation
    - Compact mode: Optional prop to show condensed version
    - Shadcn/ui components: Progress, Tooltip, Card, Badge
    - Create file: `frontend/src/components/highlights/HighlightScoreBreakdown.tsx`
  - [ ] 4.8 Create HighlightPreview component
    - Client component for previewing highlight video clip
    - Props: highlightId (string), autoPlay (boolean, default false), onClose (function, optional)
    - Video player showing highlight segment (with context padding)
    - Use existing VideoPlayer component or Video.js integration
    - Playback controls: Play/pause, seek bar, volume, fullscreen
    - Time display: Current time / total duration (highlight duration with context)
    - Highlight range indicator: Visual indicator on seek bar showing actual highlight range (without context)
    - Trim controls: Optional advanced mode to adjust start_time/end_time with Save button
    - Create clip button: Quick action to create clip from highlight (calls parent callback)
    - Export button: Quick action to export highlight (calls parent callback)
    - Close button: Dismiss preview dialog/modal
    - Error handling: Display error if video fails to load
    - Shadcn/ui components: Dialog, Button, Slider, Alert
    - Create file: `frontend/src/components/highlights/HighlightPreview.tsx`
  - [ ] 4.9 Create HighlightProgress component
    - Client component displaying detection progress
    - Props: videoId (string), onComplete (function, optional), pollInterval (number, default 2000ms)
    - Polling mechanism: Polls getHighlightDetectionProgress API every pollInterval milliseconds
    - Progress bar: Shows progress percentage (0-100%) using Progress component
    - Current stage display: Shows current_stage text (e.g., "Analyzing audio...", "Scoring highlights...")
    - Percentage display: Shows progress number (e.g., "45%")
    - Estimated time: Displays estimated_time_remaining in format "~2 minutes remaining"
    - Error handling: Displays error messages using Alert, stops polling on error
    - Completion detection: Stops polling when progress reaches 100%
    - Completion callback: Calls onComplete when detection completes successfully
    - Shadcn/ui components: Progress, Alert, Card
    - Create file: `frontend/src/components/highlights/HighlightProgress.tsx`
  - [ ] 4.10 Ensure highlights UI tests pass
    - Run ONLY the 2-8 tests written in 4.1
    - Verify all components render correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 4.1 pass
- HighlightsPanel manages state and displays highlights correctly
- HighlightCard displays highlight info with score breakdown
- HighlightDetectionTrigger triggers detection with configurable settings
- HighlightScoreBreakdown visualizes all component scores
- HighlightPreview loads and plays highlight segments
- HighlightProgress displays real-time detection progress
- All components integrate with API client functions
- Error handling and loading states work correctly

### Integration & Testing

#### Task Group 5: Integration Tests and E2E Workflows
**Dependencies:** Task Groups 1-4

- [ ] 5.0 Complete integration and E2E testing
  - [ ] 5.1 Write 2-8 focused integration and E2E tests
    - Integration test: Trigger detection → Wait for completion → Retrieve highlights
    - Integration test: Detection with different sensitivity levels produces expected results
    - Integration test: Custom keywords affect keyword scores appropriately
    - E2E test: Full workflow from video upload → transcription → highlight detection → display highlights
    - E2E test: User adjusts highlight settings → Re-detect → See updated highlights
    - E2E test: User clicks highlight → Preview plays correct segment
    - E2E test: User exports highlight → Clip is created
    - Accuracy test: Compare detected highlights with manually labeled ground truth data
  - [ ] 5.2 Create integration tests for detection workflow
    - Test full detection workflow: Upload video → Trigger detection → Wait for ARQ job → Retrieve highlights
    - Test detection with different sensitivity levels: Verify top N highlights returned
    - Test custom keywords: Verify keywords affect scoring and detected_keywords field
    - Test score weights: Verify custom weights affect overall_score calculation
    - Test concurrent detection prevention: Verify duplicate detection blocked
    - Test detection caching: Verify cached results returned on subsequent calls
    - Test error handling: Verify graceful handling of missing video, API failures
    - Create file: `backend/tests/integration/test_highlight_detection.py`
  - [ ] 5.3 Create accuracy validation tests
    - Create labeled ground truth dataset (5-10 videos with manually identified highlights)
    - Test detection accuracy: Compare detected highlights with ground truth
    - Calculate precision, recall, F1 score for highlight detection
    - Test score correlation: Verify high-scoring highlights align with ground truth
    - Test different video types: Podcasts, vlogs, gaming, tutorials
    - Test edge cases: Very short videos, very long videos, videos with no clear highlights
    - Document accuracy metrics and areas for improvement
    - Create file: `backend/tests/accuracy/test_highlight_accuracy.py`
  - [ ] 5.4 Create E2E tests for frontend workflows
    - E2E test: User uploads video → Waits for transcription → Triggers highlight detection → Sees highlights in HighlightsPanel
    - E2E test: User changes sensitivity to "High" → Triggers re-detection → Sees more highlights
    - E2E test: User adds custom keywords → Triggers detection → Sees keywords highlighted
    - E2E test: User clicks highlight card → HighlightPreview opens and plays correct segment
    - E2E test: User expands score breakdown → Sees all component scores with explanations
    - E2E test: User marks highlight as "Rejected" → Highlight removed from list
    - E2E test: User creates clip from highlight → Clip created with correct time range
    - Create file: `frontend/tests/e2e/highlight-detection.spec.ts`
  - [ ] 5.5 Create performance tests for detection speed
    - Test detection speed for 5-minute video (target: <2 minutes)
    - Test detection speed for 30-minute video (target: <5 minutes)
    - Test detection speed for 60-minute video (target: <8 minutes)
    - Test memory usage during detection (target: <2GB for 30-min video)
    - Test concurrent detection handling (max 2 per user)
    - Identify performance bottlenecks and document optimization opportunities
    - Create file: `backend/tests/performance/test_detection_performance.py`
  - [ ] 5.6 Test video type adaptability
    - Test detection on podcast-style videos (focus on speech_density_score)
    - Test detection on gaming videos (focus on audio_energy_score and scene_change_score)
    - Test detection on vlog-style videos (balanced scoring)
    - Test detection on tutorial videos (focus on keyword_score)
    - Verify detection produces relevant highlights for each video type
    - Document recommended score weights for different video types
  - [ ] 5.7 Run all highlight detection tests
    - Run all tests from Task Groups 1-4
    - Run all integration tests from 5.2-5.3
    - Run all E2E tests from 5.4
    - Run performance tests from 5.5
    - Verify all tests pass
    - Generate test coverage report (target: >90% for highlight detection code)

**Acceptance Criteria:**
- All integration tests pass successfully
- E2E tests cover complete user workflows
- Accuracy validation shows >75% alignment with ground truth
- Performance tests meet speed targets
- Video type adaptability is validated
- Test coverage is >90% for highlight detection code
- All critical workflows are tested end-to-end

## Execution Order
1. Database Layer (Task Group 1)
2. Backend Analysis Services (Task Group 2)
3. Backend Detection Service and API (Task Group 3)
4. Frontend Components (Task Group 4)
5. Integration & Testing (Task Group 5)
