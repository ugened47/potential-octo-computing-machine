"""Batch export service for generating batch exports (ZIP, merged video, playlist)."""

import asyncio
import json
import os
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import IO
from uuid import UUID, uuid4

import redis.asyncio as redis
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.models.batch import BatchJob, BatchJobStatus, BatchVideo, BatchVideoStatus
from app.services.s3 import S3Service


class BatchExportService:
    """Service for handling batch export operations."""

    def __init__(self, db: AsyncSession):
        """Initialize batch export service.

        Args:
            db: Database session
        """
        self.db = db
        self.s3_service = S3Service()
        self.redis_client: redis.Redis | None = None

    async def _get_redis_client(self) -> redis.Redis:
        """Get Redis client for caching."""
        if not self.redis_client:
            self.redis_client = await redis.from_url(settings.redis_url)
        return self.redis_client

    async def export_batch(
        self,
        batch_job_id: UUID,
        export_format: str,
        include_failed: bool = False,
        custom_naming: str | None = None,
    ) -> dict:
        """Generate export for batch job.

        Args:
            batch_job_id: Batch job ID
            export_format: Export format ('zip', 'merged', 'playlist')
            include_failed: Include failed videos in export
            custom_naming: Custom naming pattern for files

        Returns:
            Export result dictionary with export_id and download_url

        Raises:
            ValueError: If batch not found or export format invalid
        """
        # Fetch batch job
        batch_result = await self.db.execute(
            select(BatchJob).where(BatchJob.id == batch_job_id)
        )
        batch_job = batch_result.scalar_one_or_none()
        if not batch_job:
            raise ValueError("Batch job not found")

        # Check if batch is completed
        if batch_job.status != BatchJobStatus.COMPLETED:
            raise ValueError("Batch must be completed before exporting")

        # Check cache for existing export
        redis_client = await self._get_redis_client()
        cache_key = f"batch_export:{batch_job_id}:{export_format}"
        cached_export = await redis_client.get(cache_key)
        if cached_export:
            return json.loads(cached_export)

        # Fetch batch videos
        batch_videos_result = await self.db.execute(
            select(BatchVideo)
            .where(BatchVideo.batch_job_id == batch_job_id)
            .order_by(BatchVideo.position)
        )
        batch_videos = batch_videos_result.scalars().all()

        # Filter videos based on status
        videos_to_export = [
            bv
            for bv in batch_videos
            if bv.status == BatchVideoStatus.COMPLETED
            or (include_failed and bv.status == BatchVideoStatus.FAILED)
        ]

        if not videos_to_export:
            raise ValueError("No videos available for export")

        # Generate export based on format
        if export_format == "zip":
            result = await self._export_as_zip(
                batch_job=batch_job,
                batch_videos=videos_to_export,
                custom_naming=custom_naming,
            )
        elif export_format == "merged":
            result = await self._export_merged(
                batch_job=batch_job,
                batch_videos=videos_to_export,
            )
        elif export_format == "playlist":
            result = await self._export_playlist(
                batch_job=batch_job,
                batch_videos=videos_to_export,
            )
        else:
            raise ValueError(f"Invalid export format: {export_format}")

        # Cache result for 24 hours
        await redis_client.setex(cache_key, 86400, json.dumps(result))

        return result

    async def _export_as_zip(
        self,
        batch_job: BatchJob,
        batch_videos: list[BatchVideo],
        custom_naming: str | None = None,
    ) -> dict:
        """Export batch videos as ZIP archive.

        Args:
            batch_job: Batch job
            batch_videos: List of batch videos to export
            custom_naming: Custom naming pattern

        Returns:
            Export result dictionary
        """
        export_id = str(uuid4())

        # Create temporary directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / f"batch_{batch_job.id}.zip"

            # Create ZIP archive
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for idx, batch_video in enumerate(batch_videos):
                    # Generate filename
                    if custom_naming:
                        filename = custom_naming.replace("{position}", str(idx + 1))
                        filename = filename.replace("{name}", f"video_{idx + 1}")
                        filename = filename.replace("{ext}", "mp4")
                    else:
                        filename = f"{idx + 1:03d}_video.mp4"

                    # For now, we'll add a placeholder
                    # In production, this would download from S3 and add to ZIP
                    zipf.writestr(
                        filename,
                        f"Placeholder for video {batch_video.video_id}".encode(),
                    )

            # Upload ZIP to S3
            s3_key = f"batch_exports/{batch_job.user_id}/{batch_job.id}/{export_id}.zip"
            with open(zip_path, "rb") as zip_file:
                self.s3_service.s3_client.upload_fileobj(
                    zip_file,
                    self.s3_service.bucket,
                    s3_key,
                    ExtraArgs={"ContentType": "application/zip"},
                )

            # Generate presigned download URL (24 hours)
            download_url = self.s3_service.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.s3_service.bucket, "Key": s3_key},
                ExpiresIn=86400,  # 24 hours
            )

            file_size = zip_path.stat().st_size

        return {
            "export_job_id": export_id,
            "status": "completed",
            "progress": 100,
            "download_url": download_url,
            "file_size": file_size,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        }

    async def _export_merged(
        self,
        batch_job: BatchJob,
        batch_videos: list[BatchVideo],
    ) -> dict:
        """Export batch videos as single merged video.

        Args:
            batch_job: Batch job
            batch_videos: List of batch videos to export

        Returns:
            Export result dictionary
        """
        export_id = str(uuid4())

        # Placeholder implementation
        # In production, this would use FFmpeg concat demuxer to merge videos
        return {
            "export_job_id": export_id,
            "status": "completed",
            "progress": 100,
            "download_url": f"https://example.com/merged_{export_id}.mp4",
            "file_size": 0,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        }

    async def _export_playlist(
        self,
        batch_job: BatchJob,
        batch_videos: list[BatchVideo],
    ) -> dict:
        """Export batch videos as M3U8 playlist.

        Args:
            batch_job: Batch job
            batch_videos: List of batch videos to export

        Returns:
            Export result dictionary
        """
        export_id = str(uuid4())

        # Generate M3U8 playlist content
        playlist_content = "#EXTM3U\n"
        playlist_content += "#EXT-X-VERSION:3\n"

        for batch_video in batch_videos:
            # Add placeholder entries
            playlist_content += f"#EXTINF:0.0,Video {batch_video.position + 1}\n"
            playlist_content += f"https://example.com/video_{batch_video.video_id}.mp4\n"

        # Upload playlist to S3
        s3_key = f"batch_exports/{batch_job.user_id}/{batch_job.id}/{export_id}.m3u8"
        self.s3_service.s3_client.put_object(
            Bucket=self.s3_service.bucket,
            Key=s3_key,
            Body=playlist_content.encode(),
            ContentType="application/x-mpegURL",
        )

        # Generate presigned download URL
        download_url = self.s3_service.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.s3_service.bucket, "Key": s3_key},
            ExpiresIn=86400,
        )

        return {
            "export_job_id": export_id,
            "status": "completed",
            "progress": 100,
            "download_url": download_url,
            "file_size": len(playlist_content),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        }
