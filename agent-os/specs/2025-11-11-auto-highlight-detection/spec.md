# Specification: Auto-Highlight Detection

## Goal
Automatically detect and score the most engaging moments in videos using AI-powered analysis of audio energy, scene changes, speech patterns, and keyword presence to help creators quickly find the best clips.

## User Stories
- As a content creator, I want my video's best moments automatically identified so that I can quickly create highlight reels without watching the entire video
- As a podcaster, I want high-energy segments automatically detected so that I can create engaging short clips for social media
- As a user, I want to adjust highlight sensitivity so that I can control how many highlights are suggested
- As a user, I want to see why each moment was highlighted so that I can understand the scoring logic

## Specific Requirements

### Highlight Model & Database
- Create Highlight model with video_id (foreign key), start_time (float, seconds), end_time (float, seconds)
- Scoring: overall_score (integer 0-100), audio_energy_score (0-100), scene_change_score (0-100), speech_density_score (0-100), keyword_score (0-100)
- Metadata: detected_keywords (text array), confidence_level (float 0-1), duration_seconds (float)
- Ranking: rank (integer, 1 = best highlight), highlight_type enum ('high_energy', 'key_moment', 'keyword_match', 'scene_change')
- Context: context_before_seconds (float, default 2), context_after_seconds (float, default 3)
- Status: status enum ('detected', 'reviewed', 'exported', 'rejected')
- Timestamps: created_at, updated_at
- Create database migration with indexes on video_id, overall_score DESC, rank, status

### Audio Analysis Service
- Extract audio waveform from video using PyAV
- Calculate audio energy (RMS) for each 0.5-second window
- Detect high-energy segments (energy > threshold, configurable default 0.6)
- Identify energy peaks and sustained high-energy periods (>3 seconds)
- Detect sudden energy changes (peaks after quiet periods)
- Calculate speech density using voice activity detection (VAD)
- Identify segments with consistent speech (podcasts) vs varied energy (gaming)
- Score audio features on 0-100 scale:
  - High energy: 80-100
  - Medium energy: 50-79  - Quiet/background: 0-49
- Use librosa or similar for audio feature extraction

### Video Analysis Service
- Detect scene changes using PySceneDetect or custom algorithm
- Analyze frame-to-frame differences (histogram comparison, pixel differences)
- Identify significant scene transitions (threshold-based)
- Detect camera motion and cuts
- Calculate scene diversity (frequent changes vs static scenes)
- Score scene changes on 0-100 scale based on:
  - Frequency of changes (more changes = higher score)
  - Significance of changes (visual difference magnitude)
  - Timing (changes aligned with audio energy get bonus)
- Optional: Detect faces and track presence/absence for human-focused content

### Speech Pattern Analysis
- Integrate with existing transcript data (word-level timestamps)
- Analyze speech patterns:
  - Speaking rate (words per minute)
  - Pauses and silence duration
  - Speech intensity variations
- Detect segments with increased speaking rate (excitement)
- Identify segments with emphasized words (louder, slower)
- Calculate speech density score (0-100):
  - High density (fast, no pauses): 80-100
  - Medium density: 50-79
  - Low density (slow, many pauses): 0-49

### Keyword-Based Scoring
- Use existing transcript keyword search functionality
- Maintain list of "highlight keywords" (user-configurable):
  - Default: ["important", "key", "best", "amazing", "wow", "incredible", "watch", "look", "check", "unbelievable"]
  - User can add custom keywords relevant to their content
- Detect keyword matches in transcript within time windows
- Bonus scoring for keyword clusters (multiple keywords nearby)
- Weight keywords by importance (user-defined or ML-based)
- Keyword score (0-100):
  - Multiple important keywords: 80-100
  - Single important keyword: 50-79
  - Related/minor keywords: 30-49
  - No keywords: 0

### Composite Scoring Algorithm
- Calculate overall_score as weighted average of component scores:
  - audio_energy_score: 35% weight
  - scene_change_score: 20% weight
  - speech_density_score: 25% weight
  - keyword_score: 20% weight
- Weights adjustable via configuration (per-user or global)
- Apply bonus multipliers for:
  - Multiple high signals aligned (e.g., high energy + scene change): +10%
  - Sustained high scores (>5 seconds): +15%
  - Keywords + high energy: +20%
- Normalize final score to 0-100 range
- Segments with overall_score >= 70: High priority highlights
- Segments with overall_score 50-69: Medium priority highlights  - Segments with overall_score < 50: Low priority (not shown by default)

### Highlight Detection Service
- Orchestrate full highlight detection workflow
- Process video in chunks (avoid loading entire video in memory)
- Run audio, video, and speech analysis in parallel where possible
- Combine scores using composite algorithm
- Identify discrete highlight segments (start/end times)
- Merge overlapping or adjacent highlights (within 3 seconds)
- Add context padding (default: 2s before, 3s after)
- Rank highlights by overall_score (1 = best, 2 = second best, etc.)
- Limit highlights per video (default: top 10, configurable 5-20)
- Store Highlight records in database
- Cache detection results to avoid reprocessing

### Background Job Processing
- ARQ task: detect_highlights(video_id: str, sensitivity: str = 'medium') for async processing
- Sensitivity levels:
  - 'low': Only top 5 highlights, score threshold 80
  - 'medium': Top 10 highlights, score threshold 70 (default)
  - 'high': Top 15 highlights, score threshold 60
  - 'max': Top 20 highlights, score threshold 50
- Download video from S3
- Run audio, video, speech analysis
- Calculate scores for all potential segments
- Select top N highlights based on sensitivity
- Store Highlight records in database
- Track progress in Redis (0-100%)
- Update video metadata with highlight_count
- Handle errors with retry logic (max 3 attempts)
- Job timeout: 15 minutes for standard videos

### Highlight Detection API Endpoints
- POST /api/videos/{id}/highlights/detect: Trigger highlight detection
  - Body: {sensitivity: 'low' | 'medium' | 'high' | 'max', keywords: string[]}
  - Enqueues ARQ job, returns job_id
  - Prevents duplicate detection (check if already processing)
- GET /api/videos/{id}/highlights: List all highlights for video
  - Query params: status, min_score, limit, offset
  - Returns highlights sorted by rank (best first)
  - Include segment preview URL (video thumbnail or short clip)
- GET /api/highlights/{id}: Get single highlight details
  - Returns full Highlight object with all scores
  - Include score breakdown explanation
- PATCH /api/highlights/{id}: Update highlight
  - Allow user to adjust rank, status (review, reject)
  - Allow user to adjust start/end times
- DELETE /api/highlights/{id}: Delete highlight
  - Soft delete (mark as rejected) or hard delete
- GET /api/highlights/{id}/preview: Generate preview clip
  - Return short video clip (start_time to end_time + context)
  - Cache preview clips for performance
- GET /api/videos/{id}/highlights/progress: Get detection progress
  - Returns {progress, status, estimated_time_remaining}

### HighlightsPanel Component
- Client component displaying all detected highlights for a video
- Props: videoId (string), onHighlightClick (function, optional)
- Fetch highlights on mount using getVideoHighlights
- Display highlights as cards in grid or list layout
- Each highlight card shows:
  - Thumbnail/preview image
  - Start time - end time (formatted as MM:SS)
  - Overall score (badge with color: green >80, yellow 70-80, gray <70)
  - Highlight type badge (high_energy, key_moment, etc.)
  - Score breakdown (expandable): audio, scene, speech, keyword scores
  - Detected keywords (if any)
  - Action buttons: Play, Create Clip, Export, Reject
- Sorting options: By rank, by score, by time
- Filtering: By type, by min score, by status
- Sensitivity selector: Dropdown to trigger re-detection with different sensitivity
- Empty state: "Detecting highlights..." or "No highlights detected"
- Loading state: Skeleton loaders for cards
- Auto-refresh: Poll for highlights if detection is in progress

### HighlightCard Component
- Client component displaying individual highlight info
- Props: highlight (Highlight), onClick (function, optional), onAction (function)
- Card layout with thumbnail, time range, score badge
- Score visualization: Progress bar or radial chart showing overall score
- Score breakdown: Expandable section with all component scores
- Explanation text: Why this was highlighted (e.g., "High energy audio + keyword 'amazing'")
- Actions dropdown: Play, Create Clip, Export, Edit Times, Reject
- Hover effect: Show video preview on hover (animated thumbnail or short clip)
- Selected state: Highlight border when selected
- Shadcn components: Card, Badge, Button, Progress, Popover
- Create file: `frontend/src/components/highlights/HighlightCard.tsx`

### HighlightDetectionTrigger Component
- Client component for triggering highlight detection
- Props: videoId (string), onDetectionStart (function, optional)
- Button: "Detect Highlights" with icon (Sparkles or Zap)
- Settings popover:
  - Sensitivity radio group (Low, Medium, High, Max)
  - Custom keywords input (comma-separated)
  - Score weights sliders (audio, scene, speech, keyword)
- Detect button: Triggers API call, shows loading state
- Progress display: Show detection progress if in progress
- Estimated time: Display estimated time remaining
- Error handling: Display error messages with retry option
- Shadcn components: Button, Popover, RadioGroup, Input, Slider
- Create file: `frontend/src/components/highlights/HighlightDetectionTrigger.tsx`

### HighlightScoreBreakdown Component
- Client component displaying detailed score breakdown
- Props: highlight (Highlight), className (string, optional)
- Visual score breakdown:
  - Audio energy: Progress bar with percentage
  - Scene changes: Progress bar with percentage
  - Speech density: Progress bar with percentage
  - Keywords: Progress bar with percentage
- Color coding: Green (high), yellow (medium), gray (low)
- Explanation text for each component
- Overall score calculation shown
- Interactive: Click component to see detailed explanation
- Shadcn components: Progress, Tooltip, Card
- Create file: `frontend/src/components/highlights/HighlightScoreBreakdown.tsx`

### HighlightPreview Component
- Client component for previewing highlight video clip
- Props: highlightId (string), autoPlay (boolean, default false)
- Video player showing highlight segment (with context)
- Playback controls: Play/pause, seek, volume
- Time display: Current time / total duration
- Trim controls: Adjust start/end times (with save button)
- Create clip button: Quick action to create clip from highlight
- Export button: Quick action to export highlight
- Use existing VideoPlayer component or Video.js
- Shadcn components: Button, Slider, Dialog
- Create file: `frontend/src/components/highlights/HighlightPreview.tsx`

### Frontend API Client Functions
- triggerHighlightDetection(videoId, config): Triggers detection, returns Promise<{job_id: string}>
  - Config: {sensitivity, keywords, score_weights}
- getVideoHighlights(videoId, params): Fetches highlights, returns Promise<{highlights: Highlight[], total: number}>
  - Params: {status, min_score, limit, offset, sort}
- getHighlight(highlightId): Fetches single highlight, returns Promise<Highlight>
- updateHighlight(highlightId, updates): Updates highlight, returns Promise<Highlight>
  - Updates: {rank, status, start_time, end_time}
- deleteHighlight(highlightId): Deletes highlight, returns Promise<void>
- getHighlightPreviewUrl(highlightId): Gets preview clip URL, returns Promise<{url: string}>
- getHighlightDetectionProgress(videoId): Gets detection progress, returns Promise<HighlightProgress>
- All functions use apiClient with proper error handling and TypeScript types

### TypeScript Type Definitions
- Highlight interface: id, video_id, start_time, end_time, overall_score, component scores, detected_keywords, confidence_level, duration_seconds, rank, highlight_type, status, timestamps
- HighlightType type: 'high_energy' | 'key_moment' | 'keyword_match' | 'scene_change'
- HighlightStatus type: 'detected' | 'reviewed' | 'exported' | 'rejected'
- HighlightScore interface: audio_energy, scene_change, speech_density, keyword (all 0-100)
- HighlightConfig interface: sensitivity, keywords, score_weights
- HighlightProgress interface: progress, status, estimated_time_remaining, current_stage
- SensitivityLevel type: 'low' | 'medium' | 'high' | 'max'
- ScoreWeights interface: audio_energy, scene_change, speech_density, keyword (percentages)

### Testing Requirements
- Backend unit tests: Test scoring algorithms with synthetic data
- Backend integration tests: Test API endpoints with real video samples
- Worker tests: Test highlight detection task with various video types
- Analysis tests: Test audio, video, speech analysis accuracy
- Frontend component tests: Test HighlightsPanel, HighlightCard, HighlightDetectionTrigger
- E2E tests: Full highlight detection workflow (trigger, wait, view, use highlights)
- Accuracy tests: Compare detected highlights with manually labeled ground truth
- Performance tests: Test detection speed for different video lengths

### Performance Considerations
- Process videos in chunks to minimize memory usage
- Cache detection results to avoid reprocessing
- Run analysis components in parallel where possible
- Use GPU acceleration for video analysis if available
- Limit concurrent highlight detection jobs (e.g., 2 per user)
- Store pre-computed scores for segments to enable quick re-ranking
- Generate and cache preview clips for top highlights

### Quality Considerations
- Validation: Compare automatic highlights with user-selected clips to improve algorithm
- Feedback loop: Allow users to rate highlight quality, use for ML training
- Video type detection: Adjust scoring weights based on video type (podcast, gaming, vlog, tutorial)
- Content-aware: Detect video category and optimize detection parameters
- Ground truth: Maintain labeled dataset for testing and improving accuracy

### Integration Points
- Dashboard: Show "Auto-Highlights Available" badge on video cards
- Video Editor: "Highlights" tab showing all detected highlights
- Timeline Editor: Highlight segments highlighted on timeline
- Clips List: Quick action to create clips from highlights
- Export: Option to export "Top 5 Highlights" in bulk

## Success Criteria
- Highlight detection completes in <5 minutes for 30-minute video
- Detection accuracy >75% (based on user feedback/ratings)
- Users find at least 3 usable highlights per video on average
- Algorithm works for different video types (podcasts, vlogs, gaming, tutorials)
- Score explanations are clear and understandable
- UI is intuitive and highlights are easy to review and use
- Test coverage >90% for highlight detection code
