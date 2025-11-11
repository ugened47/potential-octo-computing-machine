# Implementation Guide: Video Export Feature

## Overview

Complete specification and implementation guide for the video export feature, allowing users to export edited videos with custom quality settings.

## Status

- **Current Completion:** 0%
- **Estimated Time:** 8-12 hours
- **Priority:** Medium (nice-to-have for MVP)
- **Complexity:** High

---

## Architecture Overview

```
User Action → API Request → Export Job Created → ARQ Worker Processes → S3 Upload → User Downloads
```

**Components:**
1. Export Model (database)
2. Export Service (business logic)
3. Export Worker (ARQ background job)
4. Export API (REST endpoints)
5. Export UI Components (React)

---

## Phase 1: Database Layer (30 minutes)

### 1.1 Create Export Model

```python
# backend/app/models/export.py

"""Export model for video exports."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, JSON, Column


class ExportStatus(str, Enum):
    """Export processing status."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportQuality(str, Enum):
    """Export quality presets."""
    HIGH = "high"      # CRF 18
    MEDIUM = "medium"  # CRF 23
    LOW = "low"        # CRF 28


class Export(SQLModel, table=True):
    """Export record."""

    __tablename__ = "exports"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    video_id: UUID = Field(foreign_key="videos.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Export settings
    resolution: str = Field(max_length=10)  # "720p", "1080p"
    quality: ExportQuality
    format: str = Field(default="mp4", max_length=10)

    # Segment selection (JSON array of segment objects)
    segments: list[dict] = Field(default=[], sa_column=Column(JSON))

    # Output
    output_s3_key: str | None = Field(default=None, max_length=500)
    output_url: str | None = Field(default=None, max_length=1000)
    file_size: int | None = Field(default=None)  # bytes

    # Status tracking
    status: ExportStatus = Field(default=ExportStatus.QUEUED)
    progress: int = Field(default=0)  # 0-100
    error_message: str | None = Field(default=None, max_length=500)
    estimated_time_remaining: int | None = Field(default=None)  # seconds

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = Field(default=None)
```

### 1.2 Create Migration

```bash
cd backend
alembic revision --autogenerate -m "create exports table"
alembic upgrade head
```

Or manually:

```python
# backend/alembic/versions/XXXXX_create_exports_table.py

def upgrade():
    op.create_table(
        'exports',
        sa.Column('id', sa_utils.UUIDType(), nullable=False),
        sa.Column('video_id', sa_utils.UUIDType(), nullable=False),
        sa.Column('user_id', sa_utils.UUIDType(), nullable=False),
        sa.Column('resolution', sa.String(10), nullable=False),
        sa.Column('quality', sa.String(20), nullable=False),
        sa.Column('format', sa.String(10), nullable=False),
        sa.Column('segments', sa.JSON(), nullable=False),
        sa.Column('output_s3_key', sa.String(500), nullable=True),
        sa.Column('output_url', sa.String(1000), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('estimated_time_remaining', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_exports_video_id', 'exports', ['video_id'])
    op.create_index('ix_exports_user_id', 'exports', ['user_id'])
    op.create_index('ix_exports_status', 'exports', ['status'])

def downgrade():
    op.drop_index('ix_exports_status')
    op.drop_index('ix_exports_user_id')
    op.drop_index('ix_exports_video_id')
    op.drop_table('exports')
```

---

## Phase 2: Export Service (2-3 hours)

### 2.1 Create Export Service

```python
# backend/app/services/export.py

"""Video export service."""

import subprocess
import tempfile
from pathlib import Path
from typing import BinaryIO

from app.models.export import ExportQuality


class ExportService:
    """Service for video export operations."""

    # Quality presets (CRF values)
    QUALITY_PRESETS = {
        ExportQuality.HIGH: 18,
        ExportQuality.MEDIUM: 23,
        ExportQuality.LOW: 28,
    }

    # Resolution mappings
    RESOLUTIONS = {
        "720p": (1280, 720),
        "1080p": (1920, 1080),
    }

    @staticmethod
    def get_crf_value(quality: ExportQuality) -> int:
        """Get CRF value for quality preset."""
        return ExportService.QUALITY_PRESETS[quality]

    @staticmethod
    def get_resolution_dimensions(resolution: str) -> tuple[int, int]:
        """Get width and height for resolution."""
        return ExportService.RESOLUTIONS.get(resolution, (1920, 1080))

    @staticmethod
    async def combine_segments(
        video_path: Path,
        segments: list[dict],
        output_path: Path,
    ) -> None:
        """
        Combine video segments into single file.

        Args:
            video_path: Path to source video
            segments: List of {start_time, end_time} dicts
            output_path: Where to save combined video
        """
        if not segments:
            raise ValueError("No segments provided")

        # Create FFmpeg filter for selecting segments
        # Using select filter to extract specific time ranges
        filters = []

        for i, segment in enumerate(segments):
            start = segment["start_time"]
            end = segment["end_time"]

            # Create select filter for this segment
            filter_expr = f"between(t,{start},{end})"
            filters.append(filter_expr)

        # Combine filters with OR
        select_filter = "+".join(filters)

        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vf", f"select='{select_filter}',setpts=N/FRAME_RATE/TB",
            "-af", f"aselect='{select_filter}',asetpts=N/SR/TB",
            "-y",  # Overwrite output
            str(output_path),
        ]

        # Run FFmpeg
        process = await subprocess.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"FFmpeg failed: {error_msg}")

    @staticmethod
    async def re_encode_video(
        input_path: Path,
        output_path: Path,
        resolution: str,
        quality: ExportQuality,
    ) -> None:
        """
        Re-encode video with specified settings.

        Args:
            input_path: Source video file
            output_path: Output video file
            resolution: Target resolution (e.g., "1080p")
            quality: Quality preset
        """
        crf = ExportService.get_crf_value(quality)
        width, height = ExportService.get_resolution_dimensions(resolution)

        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-c:v", "libx264",              # H.264 codec
            "-crf", str(crf),                # Quality setting
            "-preset", "medium",             # Encoding speed
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",  # Scale maintaining aspect ratio
            "-c:a", "aac",                   # AAC audio
            "-b:a", "192k",                  # Audio bitrate
            "-movflags", "+faststart",       # Enable streaming
            "-y",                            # Overwrite output
            str(output_path),
        ]

        # Run FFmpeg with progress tracking
        process = await subprocess.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"FFmpeg encoding failed: {error_msg}")

    @staticmethod
    async def export_video(
        video_path: Path,
        segments: list[dict] | None,
        output_path: Path,
        resolution: str,
        quality: ExportQuality,
    ) -> Path:
        """
        Complete export process: combine segments and re-encode.

        Args:
            video_path: Source video
            segments: List of segments to combine (None = full video)
            output_path: Where to save final export
            resolution: Target resolution
            quality: Quality preset

        Returns:
            Path to exported video
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            # Step 1: Combine segments if needed
            if segments:
                combined_path = temp_dir_path / "combined.mp4"
                await ExportService.combine_segments(
                    video_path, segments, combined_path
                )
                source_for_encoding = combined_path
            else:
                source_for_encoding = video_path

            # Step 2: Re-encode with quality settings
            await ExportService.re_encode_video(
                source_for_encoding,
                output_path,
                resolution,
                quality,
            )

        return output_path
```

---

## Phase 3: Background Worker (2 hours)

### 3.1 Create Export Worker

```python
# backend/app/worker.py (add to existing file)

from pathlib import Path
import tempfile
from uuid import UUID

from app.models.export import Export, ExportStatus
from app.services.export import ExportService
from app.services.s3 import S3Service
from app.core.db import get_db_session


async def export_video_task(ctx: dict, export_id: str) -> dict:
    """
    Background task to process video export.

    Args:
        ctx: ARQ context with Redis connection
        export_id: UUID of export record

    Returns:
        Dict with export status
    """
    export_uuid = UUID(export_id)

    async with get_db_session() as db:
        # Get export record
        export = await db.get(Export, export_uuid)

        if not export:
            return {"error": "Export not found"}

        try:
            # Update status
            export.status = ExportStatus.PROCESSING
            export.progress = 10
            db.add(export)
            await db.commit()

            # Get video record
            video = await db.get(Video, export.video_id)

            if not video:
                raise ValueError("Video not found")

            # Download source video from S3
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_input:
                input_path = Path(temp_input.name)

                # Download from S3
                s3_service = S3Service()
                await s3_service.download_file(video.s3_key, str(input_path))

                export.progress = 30
                db.add(export)
                await db.commit()

            # Process export
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_output:
                output_path = Path(temp_output.name)

                # Export video
                await ExportService.export_video(
                    video_path=input_path,
                    segments=export.segments if export.segments else None,
                    output_path=output_path,
                    resolution=export.resolution,
                    quality=export.quality,
                )

                export.progress = 70
                db.add(export)
                await db.commit()

                # Upload to S3
                output_key = f"exports/{export.user_id}/{export.id}.mp4"

                await s3_service.upload_file(
                    str(output_path),
                    output_key,
                    content_type="video/mp4",
                )

                export.progress = 90
                db.add(export)
                await db.commit()

                # Get file size
                export.file_size = output_path.stat().st_size

                # Generate download URL
                export.output_s3_key = output_key
                export.output_url = await s3_service.generate_presigned_url(
                    output_key,
                    expiration=3600,  # 1 hour
                )

            # Mark as completed
            export.status = ExportStatus.COMPLETED
            export.progress = 100
            export.completed_at = datetime.utcnow()

            db.add(export)
            await db.commit()

            # Cleanup temp files
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

            return {
                "export_id": str(export.id),
                "status": "completed",
                "output_url": export.output_url,
            }

        except Exception as e:
            # Mark as failed
            export.status = ExportStatus.FAILED
            export.error_message = str(e)[:500]

            db.add(export)
            await db.commit()

            return {
                "export_id": str(export.id),
                "status": "failed",
                "error": str(e),
            }


# Add to WorkerSettings class
class WorkerSettings:
    functions = [
        # ... existing tasks ...
        export_video_task,
    ]
```

---

## Phase 4: API Endpoints (2 hours)

```python
# backend/app/api/routes/exports.py

"""Export API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID

from app.api.deps import get_current_user, get_db
from app.models.export import Export, ExportStatus, ExportQuality
from app.models.user import User
from app.schemas.export import (
    ExportCreate,
    ExportResponse,
    ExportListResponse,
)
from app.worker import export_video_task

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/", response_model=ExportResponse, status_code=201)
async def create_export(
    export_data: ExportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new export job."""
    # Create export record
    export = Export(
        video_id=export_data.video_id,
        user_id=current_user.id,
        resolution=export_data.resolution,
        quality=export_data.quality,
        format="mp4",
        segments=export_data.segments or [],
        status=ExportStatus.QUEUED,
    )

    db.add(export)
    await db.commit()
    await db.refresh(export)

    # Enqueue background job
    await ctx['redis'].enqueue_job(
        'export_video_task',
        str(export.id),
    )

    return export


@router.get("/{export_id}", response_model=ExportResponse)
async def get_export(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get export status and details."""
    export = await db.get(Export, export_id)

    if not export or export.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Export not found")

    return export


@router.get("/", response_model=ExportListResponse)
async def list_exports(
    video_id: UUID | None = None,
    status: ExportStatus | None = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's exports."""
    query = select(Export).where(Export.user_id == current_user.id)

    if video_id:
        query = query.where(Export.video_id == video_id)

    if status:
        query = query.where(Export.status == status)

    query = query.order_by(Export.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    exports = result.scalars().all()

    return {"exports": exports, "total": len(exports)}


@router.delete("/{export_id}", status_code=204)
async def delete_export(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete export record and file."""
    export = await db.get(Export, export_id)

    if not export or export.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Export not found")

    # TODO: Delete from S3
    # if export.output_s3_key:
    #     await s3_service.delete_file(export.output_s3_key)

    await db.delete(export)
    await db.commit()

    return None
```

---

## Phase 5: Frontend Components (2-3 hours)

### 5.1 Export Types

```typescript
// frontend/src/types/export.ts

export type ExportQuality = 'high' | 'medium' | 'low'
export type ExportResolution = '720p' | '1080p'
export type ExportStatus = 'queued' | 'processing' | 'completed' | 'failed'

export interface ExportSegment {
  start_time: number
  end_time: number
}

export interface Export {
  id: string
  video_id: string
  user_id: string
  resolution: ExportResolution
  quality: ExportQuality
  format: string
  segments: ExportSegment[]
  output_s3_key?: string
  output_url?: string
  file_size?: number
  status: ExportStatus
  progress: number
  error_message?: string
  estimated_time_remaining?: number
  created_at: string
  updated_at: string
  completed_at?: string
}

export interface CreateExportRequest {
  video_id: string
  resolution: ExportResolution
  quality: ExportQuality
  segments?: ExportSegment[]
}
```

### 5.2 Export Modal Component

```typescript
// frontend/src/components/export/ExportModal.tsx

'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Select } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { ExportQuality, ExportResolution, ExportSegment } from '@/types/export'

interface ExportModalProps {
  videoId: string
  segments?: ExportSegment[]
  isOpen: boolean
  onClose: () => void
  onExport: (resolution: ExportResolution, quality: ExportQuality) => void
}

export function ExportModal({
  videoId,
  segments = [],
  isOpen,
  onClose,
  onExport,
}: ExportModalProps) {
  const [resolution, setResolution] = useState<ExportResolution>('1080p')
  const [quality, setQuality] = useState<ExportQuality>('medium')
  const [isExporting, setIsExporting] = useState(false)

  const handleExport = async () => {
    setIsExporting(true)
    try {
      await onExport(resolution, quality)
      onClose()
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  const estimatedSize = calculateEstimatedSize(resolution, quality, segments)

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Export Video</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Resolution Selection */}
          <div>
            <Label>Resolution</Label>
            <RadioGroup value={resolution} onValueChange={(v) => setResolution(v as ExportResolution)}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="720p" id="720p" />
                <Label htmlFor="720p">720p (1280x720)</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="1080p" id="1080p" />
                <Label htmlFor="1080p">1080p (1920x1080)</Label>
              </div>
            </RadioGroup>
          </div>

          {/* Quality Selection */}
          <div>
            <Label>Quality</Label>
            <Select value={quality} onValueChange={(v) => setQuality(v as ExportQuality)}>
              <option value="high">High (Best quality, larger file)</option>
              <option value="medium">Medium (Balanced)</option>
              <option value="low">Low (Smaller file)</option>
            </Select>
          </div>

          {/* Info */}
          <div className="text-sm text-gray-600">
            <p>Estimated file size: {estimatedSize}</p>
            {segments.length > 0 && (
              <p>Exporting {segments.length} segment(s)</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleExport} disabled={isExporting}>
              {isExporting ? 'Exporting...' : 'Export'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function calculateEstimatedSize(
  resolution: ExportResolution,
  quality: ExportQuality,
  segments: ExportSegment[]
): string {
  // Rough estimation logic
  const baseSizePerMinute = {
    high: 60,
    medium: 30,
    low: 15,
  }

  const resolutionMultiplier = {
    '720p': 0.7,
    '1080p': 1.0,
  }

  const duration = segments.reduce(
    (sum, seg) => sum + (seg.end_time - seg.start_time),
    0
  ) / 60 // Convert to minutes

  const estimatedMB =
    baseSizePerMinute[quality] * resolutionMultiplier[resolution] * duration

  return `~${Math.round(estimatedMB)} MB`
}
```

---

## Testing Strategy

### Unit Tests

- Test ExportService methods individually
- Mock FFmpeg calls
- Test segment combining logic
- Test quality preset values

### Integration Tests

- Test full export API flow
- Test worker job execution
- Test S3 upload/download
- Test error handling

### E2E Tests

- Test export through UI
- Verify download works
- Test with different quality settings
- Test progress tracking

---

## Deployment Checklist

- [ ] Ensure FFmpeg is installed on worker servers
- [ ] Configure S3 bucket for exports
- [ ] Set up cleanup job for old exports
- [ ] Configure ARQ worker to handle export tasks
- [ ] Monitor export job success rate
- [ ] Set up alerts for failed exports

---

## Estimated Timeline

- **Phase 1 (Database):** 30 minutes
- **Phase 2 (Service):** 2-3 hours
- **Phase 3 (Worker):** 2 hours
- **Phase 4 (API):** 2 hours
- **Phase 5 (Frontend):** 2-3 hours
- **Testing:** 2 hours
- **Total:** 10-13 hours

---

## Notes

- Start with simple single-video export before implementing segment combining
- Test with small videos first
- Monitor memory usage during processing
- Consider adding queue limits to prevent overload
- Add rate limiting for exports (e.g., 5 per hour per user)

