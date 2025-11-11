# Optimized Prompt Template for Parallel Implementation

> **Purpose:** Use this prompt template to implement groups in parallel Claude Code sessions
> **Location:** Copy and paste into new Claude Code chat

---

## Prompt Template

```
You are implementing Group {N} of the AI Video Clipper project.

📋 REFERENCE DOCUMENTS:
- Implementation groups: /IMPLEMENTATION_GROUPS.md
- Detailed tasks: /IMPLEMENTATION_TASKS.md (tasks {START}-{END})
- Project docs: /.claude/CLAUDE.md
- Feature specs: /agent-os/specs/2025-11-11-{FEATURE}/spec.md
- Task breakdown: /agent-os/specs/2025-11-11-{FEATURE}/tasks.md

✅ TEST FILES ALREADY CREATED:
Backend tests are in:
- backend/tests/factories/{FEATURE}_factory.py
- backend/tests/api/test_{FEATURE}_api.py
- backend/tests/services/test_{FEATURE}_service.py
- backend/tests/workers/test_{FEATURE}_worker.py

Frontend tests are in:
- frontend/tests/components/{Component}.test.tsx
- frontend/e2e/{feature}.spec.ts

🎯 YOUR MISSION:
Implement Group {N}: {GROUP_NAME}
Tasks: {START}-{END} ({TOTAL} tasks)
Difficulty: {DIFFICULTY}
Estimated time: {TIME}

📝 IMPLEMENTATION APPROACH:
1. Use Test-Driven Development (TDD):
   - Tests already exist and will FAIL initially (this is expected!)
   - Run tests first to see what needs to be implemented
   - Implement code to make tests pass
   - Refactor and optimize

2. Follow the task order in /IMPLEMENTATION_TASKS.md
   - Tasks are numbered and ordered with dependencies in mind
   - Mark tasks as ✅ completed in IMPLEMENTATION_TASKS.md as you finish them
   - Skip tasks that are blocked and note them as ⚠️

3. Follow existing code patterns:
   - Backend: FastAPI async patterns, SQLModel, ARQ workers
   - Frontend: Next.js 14 App Router, Shadcn/ui components
   - See /.claude/CLAUDE.md for detailed patterns

4. Code quality requirements:
   - Backend: Run `ruff format . && ruff check . && mypy app` before committing
   - Frontend: Run `npm run lint && npm run format && npx tsc --noEmit`
   - Tests must pass: `pytest` for backend, `npm test` for frontend

🔧 SPECIFIC TASKS FOR GROUP {N}:
{DETAILED_GROUP_DESCRIPTION}

⚠️ IMPORTANT REMINDERS:
- DO NOT create new test files (they already exist)
- DO implement the actual code to make existing tests pass
- DO follow TDD: Red → Green → Refactor
- DO update IMPLEMENTATION_TASKS.md with ✅ as you complete tasks
- DO commit frequently with clear messages
- DO ask for clarification if requirements are unclear

🚀 START HERE:
1. Read the group details in /IMPLEMENTATION_GROUPS.md
2. Review the feature spec in /agent-os/specs/2025-11-11-{FEATURE}/spec.md
3. Run the tests to see what fails (expected!)
4. Start with task {START} and work sequentially through {END}
5. Mark tasks complete in /IMPLEMENTATION_TASKS.md

Ready to start? Begin with task {START}!
```

---

## Example: Group 1 (Video Export)

```
You are implementing Group 1 of the AI Video Clipper project.

📋 REFERENCE DOCUMENTS:
- Implementation groups: /IMPLEMENTATION_GROUPS.md
- Detailed tasks: /IMPLEMENTATION_TASKS.md (tasks 001-155)
- Project docs: /.claude/CLAUDE.md
- Feature specs: /agent-os/specs/2025-11-11-video-export-complete/spec.md
- Task breakdown: /agent-os/specs/2025-11-11-video-export-complete/tasks.md

✅ TEST FILES ALREADY CREATED:
Backend tests are in:
- backend/tests/factories/export_factory.py
- backend/tests/api/test_export_api.py (35 tests)
- backend/tests/services/test_export_service.py (28 tests)
- backend/tests/workers/test_export_worker.py (21 tests)

Frontend tests are in:
- frontend/tests/components/ExportModal.test.tsx (15 tests)
- frontend/e2e/export.spec.ts (13 scenarios)

🎯 YOUR MISSION:
Implement Group 1: Video Export - Complete Stack
Tasks: 001-155 (155 tasks)
Difficulty: ⭐⭐⭐ Medium
Estimated time: 25-30 hours
Priority: 🔴 CRITICAL MVP FEATURE

📝 IMPLEMENTATION APPROACH:
1. Use Test-Driven Development (TDD):
   - Tests already exist and will FAIL initially (this is expected!)
   - Run tests first to see what needs to be implemented
   - Implement code to make tests pass
   - Refactor and optimize

2. Follow the task order in /IMPLEMENTATION_TASKS.md
   - Tasks 001-010: Database layer (Export model, migrations)
   - Tasks 011-040: Backend services (FFmpeg, segment extraction)
   - Tasks 041-070: API endpoints
   - Tasks 071-090: Background workers
   - Tasks 091-150: Frontend components
   - Tasks 151-155: Documentation

3. Follow existing code patterns:
   - Backend: FastAPI async patterns, SQLModel, ARQ workers
   - Frontend: Next.js 14 App Router, Shadcn/ui components
   - See /.claude/CLAUDE.md for detailed patterns

4. Code quality requirements:
   - Backend: Run `ruff format . && ruff check . && mypy app` before committing
   - Frontend: Run `npm run lint && npm run format && npx tsc --noEmit`
   - Tests must pass: `pytest backend/tests/api/test_export_api.py`

🔧 SPECIFIC TASKS FOR GROUP 1:

**Phase 1: Database (Tasks 001-010)**
- Create Export model in backend/app/models/export.py
- Fields: id, video_id, user_id, export_type, resolution, format, quality_preset, status, progress, segments (JSONB), output_s3_key, output_url, file_size_bytes
- Create Alembic migration
- Set up relationships with Video and User models

**Phase 2: Services (Tasks 011-040)**
- Create FFmpegService for video processing
- Create SegmentExtractionService for cutting/combining video
- Create ExportProcessingService for orchestration
- Create ProgressTrackingService using Redis

**Phase 3: API (Tasks 041-070)**
- Create schemas in backend/app/schemas/export.py
- Create routes in backend/app/api/routes/export.py
- Implement 7 endpoints: create, get, progress, download, delete, list
- Add authentication and authorization

**Phase 4: Workers (Tasks 071-090)**
- Create export_video ARQ task in backend/app/worker.py
- Implement full export workflow with progress tracking
- Handle errors and cancellation

**Phase 5: Frontend (Tasks 091-150)**
- Create types in frontend/src/types/export.ts
- Create API client in frontend/src/lib/api/export.ts
- Create ExportModal, ExportProgress, ExportsList, ExportSettings components
- Integrate into Timeline Editor, Video Editor, Dashboard

⚠️ IMPORTANT REMINDERS:
- DO NOT create new test files (they already exist in backend/tests/)
- DO implement the actual code to make existing tests pass
- DO follow TDD: Run `pytest backend/tests/api/test_export_api.py` first to see failures
- DO update IMPLEMENTATION_TASKS.md with ✅ as you complete tasks
- DO commit after each phase (database, services, API, workers, frontend)

🚀 START HERE:
1. Read /IMPLEMENTATION_GROUPS.md Group 1 section
2. Review /agent-os/specs/2025-11-11-video-export-complete/spec.md
3. Run: `pytest backend/tests/api/test_export_api.py -v` (will fail - this is expected!)
4. Start with task 001: Create Export model
5. Mark tasks complete in /IMPLEMENTATION_TASKS.md

Ready to start? Begin with task 001!
```

---

## Example: Group 2 (Auto-Highlight Detection)

```
You are implementing Group 2 of the AI Video Clipper project.

📋 REFERENCE DOCUMENTS:
- Implementation groups: /IMPLEMENTATION_GROUPS.md
- Detailed tasks: /IMPLEMENTATION_TASKS.md (tasks 200-299)
- Feature specs: /agent-os/specs/2025-11-11-auto-highlight-detection/spec.md
- Task breakdown: /agent-os/specs/2025-11-11-auto-highlight-detection/tasks.md

✅ TEST FILES ALREADY CREATED:
Backend tests are in:
- backend/tests/factories/highlight_factory.py
- backend/tests/api/test_highlights_api.py (23 tests)
- backend/tests/services/test_audio_analysis.py (14 tests)
- backend/tests/services/test_video_analysis.py (12 tests)
- backend/tests/services/test_highlight_detection.py (24 tests)
- backend/tests/workers/test_highlight_worker.py (12 tests)

Frontend tests are in:
- frontend/tests/components/HighlightsPanel.test.tsx (12 tests)
- frontend/e2e/highlights.spec.ts (13 scenarios)

🎯 YOUR MISSION:
Implement Group 2: Auto-Highlight Detection - Complete Stack
Tasks: 200-299 (100 tasks)
Difficulty: ⭐⭐⭐⭐ Hard (AI algorithms)
Estimated time: 20-25 hours
Priority: 🟡 High Value Feature

📝 KEY DELIVERABLES:
- Highlight model with component scores (audio, video, speech, keyword)
- AudioAnalysisService (energy detection, VAD, speech density)
- VideoAnalysisService (PySceneDetect scene detection)
- SpeechAnalysisService (rate, pauses, emphasis)
- KeywordScoringService (keyword matching with bonuses)
- CompositeScorer (weighted algorithm: audio 35%, scene 20%, speech 25%, keyword 20%)
- HighlightDetectionService (orchestrates all analysis)
- 6 REST API endpoints
- ARQ worker: detect_highlights with sensitivity levels
- 5 React components (HighlightsPanel, HighlightCard, etc.)

🔧 ALGORITHM DETAILS:
The composite scoring algorithm should:
1. Calculate individual scores (0-100) for audio, video, speech, keyword
2. Apply weights: audio 35%, scene 20%, speech 25%, keyword 20%
3. Apply bonuses: alignment +10%, sustained +15%, keyword+energy +20%
4. Merge overlapping/adjacent segments (within 3 seconds)
5. Add context padding (2s before, 3s after)
6. Rank highlights by score (1 = best)
7. Limit based on sensitivity: low (5), medium (10), high (15), max (20)

⚠️ DEPENDENCIES:
- Existing Transcript model with word-level timestamps
- PySceneDetect library: `pip install scenedetect`
- librosa for audio: `pip install librosa`
- numpy for array processing

Ready to start? Begin with task 200!
```

---

## Quick Start Commands

### Run Tests for Your Group
```bash
# Group 1: Video Export
pytest backend/tests/api/test_export_api.py backend/tests/services/test_export_service.py backend/tests/workers/test_export_worker.py -v

# Group 2: Auto-Highlight
pytest backend/tests/api/test_highlights_api.py backend/tests/services/test_audio_analysis.py backend/tests/services/test_video_analysis.py backend/tests/services/test_highlight_detection.py backend/tests/workers/test_highlight_worker.py -v

# Group 3: Batch Processing
pytest backend/tests/api/test_batch_api.py backend/tests/services/test_batch_upload.py backend/tests/services/test_batch_processing.py backend/tests/workers/test_batch_worker.py -v

# Group 4: Subtitles
pytest backend/tests/api/test_subtitle_api.py backend/tests/services/test_subtitle_service.py backend/tests/workers/test_subtitle_worker.py -v

# Group 5: Templates
pytest backend/tests/api/test_template_api.py backend/tests/services/test_template_service.py backend/tests/workers/test_template_worker.py -v

# Groups 6-8: Team Collaboration
pytest backend/tests/api/test_organization_api.py backend/tests/api/test_sharing_api.py backend/tests/api/test_comments_api.py backend/tests/api/test_version_api.py backend/tests/services/test_permission_service.py backend/tests/services/test_notification_service.py backend/tests/websocket/test_collaboration_ws.py -v

# Groups 9-10: Advanced Editor
pytest backend/tests/api/test_project_api.py backend/tests/api/test_track_api.py backend/tests/api/test_track_item_api.py backend/tests/api/test_asset_api.py backend/tests/services/test_composition_service.py backend/tests/services/test_audio_mixing_service.py backend/tests/services/test_video_rendering_service.py backend/tests/workers/test_project_worker.py -v
```

### Mark Tasks Complete
```bash
# Open IMPLEMENTATION_TASKS.md and change:
# - **001** 🔴 Create Export model
# to:
# - **001** ✅ Create Export model
```

---

## Tips for Success

1. **Start with tests:** Always run tests first to understand what needs to be implemented
2. **Follow patterns:** Look at existing code (Video, Transcript models) for patterns
3. **Commit often:** Commit after each major milestone (model, service, API, etc.)
4. **Ask questions:** If tests are unclear, check the spec.md files for clarification
5. **Use TodoWrite:** Track your progress with TodoWrite tool for complex groups
6. **Check dependencies:** Ensure required libraries are installed before starting
7. **Run quality checks:** Use ruff/mypy for backend, eslint for frontend before commits

---

## Coordination Across Sessions

If multiple people/sessions are working in parallel:

1. **Communicate task numbers:** "I'm working on tasks 001-050"
2. **Update progress:** Mark tasks in IMPLEMENTATION_TASKS.md
3. **Avoid conflicts:** Don't work on same group simultaneously
4. **Dependencies:** Groups 6→7→8 and 9→10 have dependencies
5. **Integration:** Test integration points after completing related groups

---

**Ready to implement? Copy the template above, fill in your group number, and start coding!**
