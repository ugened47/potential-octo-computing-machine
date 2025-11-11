"""Video rendering service for Advanced Editor."""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import Project, Track, TrackItem, Transition, TrackType, ItemType


class VideoRenderingService:
    """Service for rendering multi-track video compositions."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db

    async def render_project(
        self,
        project: Project,
        output_path: str,
        quality: str = "high",
        codec: str = "libx264",
        bitrate: str | None = None,
    ) -> str:
        """Orchestrate full project rendering workflow.

        Args:
            project: Project to render
            output_path: Path to output video file
            quality: Quality preset ('low', 'medium', 'high', 'max')
            codec: Video codec (default: libx264)
            bitrate: Video bitrate (e.g., '5M', '10M')

        Returns:
            Path to rendered video file
        """
        # Get all tracks ordered by z_index
        stmt = select(Track).where(Track.project_id == project.id).order_by(Track.z_index)
        result = await self.db.execute(stmt)
        tracks = result.scalars().all()

        if not tracks:
            raise ValueError("Project has no tracks")

        # Build FFmpeg filter complex
        filter_complex = await self.build_ffmpeg_filter_complex(project, tracks)

        # Get all unique source files
        source_files = await self._get_source_files(tracks)

        # Build FFmpeg command
        cmd = ["ffmpeg", "-y"]

        # Add input files
        for source in source_files:
            cmd.extend(["-i", source])

        # Add filter complex
        if filter_complex:
            cmd.extend(["-filter_complex", filter_complex])

        # Set output codec and quality
        if not bitrate:
            bitrate_map = {
                "low": "2M",
                "medium": "5M",
                "high": "10M",
                "max": "20M",
            }
            bitrate = bitrate_map.get(quality, "5M")

        cmd.extend([
            "-map", "[vout]",  # Map final video output
            "-c:v", codec,
            "-b:v", bitrate,
            "-preset", "medium",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
        ])

        # Add audio if present
        # cmd.extend(["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"])

        # Set output file
        cmd.append(output_path)

        # Run FFmpeg
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg rendering failed: {stderr.decode()}")

        return output_path

    async def build_ffmpeg_filter_complex(
        self,
        project: Project,
        tracks: list[Track],
    ) -> str:
        """Build complex FFmpeg filter graph from project structure.

        Args:
            project: Project object
            tracks: List of tracks ordered by z_index

        Returns:
            FFmpeg filter_complex string
        """
        filters = []
        current_output = None
        input_index = 0

        # Create base canvas with background color
        base_filter = f"color=c={project.background_color}:s={project.width}x{project.height}:r={project.frame_rate}:d={project.duration_seconds}[base]"
        filters.append(base_filter)
        current_output = "[base]"

        # Process each track from bottom to top (by z_index)
        for track_idx, track in enumerate(tracks):
            if not track.is_visible:
                continue

            # Get all items in this track
            stmt = select(TrackItem).where(TrackItem.track_id == track.id).order_by(TrackItem.start_time)
            result = await self.db.execute(stmt)
            items = result.scalars().all()

            # Process each item in the track
            for item in items:
                # Apply transforms to this item
                item_filter = await self._build_item_filter(
                    item,
                    track,
                    input_index,
                    project.width,
                    project.height,
                )

                if item_filter:
                    filters.append(item_filter["filter"])
                    item_output = item_filter["output"]

                    # Overlay this item on current output
                    # Calculate position based on item's position_x and position_y
                    x_pos = int(item.position_x * project.width)
                    y_pos = int(item.position_y * project.height)

                    overlay_filter = f"{current_output}{item_output}overlay=x={x_pos}:y={y_pos}:enable='between(t,{item.start_time},{item.end_time})'[out{track_idx}_{input_index}]"
                    filters.append(overlay_filter)
                    current_output = f"[out{track_idx}_{input_index}]"
                    input_index += 1

        # Final output
        if current_output:
            filters.append(f"{current_output}copy[vout]")
        else:
            filters.append("[base]copy[vout]")

        return ";".join(filters)

    async def _build_item_filter(
        self,
        item: TrackItem,
        track: Track,
        input_index: int,
        canvas_width: int,
        canvas_height: int,
    ) -> dict | None:
        """Build filter for individual track item.

        Args:
            item: TrackItem to process
            track: Parent track
            input_index: Input stream index
            canvas_width: Canvas width
            canvas_height: Canvas height

        Returns:
            Dictionary with 'filter' and 'output' keys, or None
        """
        if item.item_type == ItemType.TEXT:
            # Text overlay
            text_content = item.text_content or ""
            text_style = item.text_style or {}
            font_size = text_style.get("font_size", 24)
            font_color = text_style.get("color", "white")

            filter_chain = f"drawtext=text='{text_content}':fontsize={font_size}:fontcolor={font_color}:x=0:y=0[item{input_index}]"
            return {"filter": filter_chain, "output": f"[item{input_index}]"}

        elif item.item_type in [ItemType.VIDEO_CLIP, ItemType.IMAGE]:
            # Video or image item
            filter_chain = f"[{input_index}:v]"

            # Apply trim if video
            if item.item_type == ItemType.VIDEO_CLIP and item.trim_start > 0:
                filter_chain += f"trim=start={item.trim_start}"
                if item.trim_end > 0:
                    duration = (item.end_time - item.start_time) - item.trim_start
                    filter_chain += f":duration={duration}"
                filter_chain += ",setpts=PTS-STARTPTS,"

            # Apply scaling
            if item.scale_x != 1.0 or item.scale_y != 1.0:
                new_width = int(canvas_width * item.scale_x)
                new_height = int(canvas_height * item.scale_y)
                filter_chain += f"scale={new_width}:{new_height},"

            # Apply rotation
            if item.rotation != 0:
                filter_chain += f"rotate={item.rotation}*PI/180,"

            # Apply opacity from track
            if track.opacity < 1.0:
                filter_chain += f"format=rgba,colorchannelmixer=aa={track.opacity},"

            filter_chain += f"[item{input_index}]"
            return {"filter": filter_chain, "output": f"[item{input_index}]"}

        return None

    async def _get_source_files(self, tracks: list[Track]) -> list[str]:
        """Get list of all unique source files needed for rendering.

        Args:
            tracks: List of tracks

        Returns:
            List of source file paths
        """
        source_files = []
        seen_urls = set()

        for track in tracks:
            stmt = select(TrackItem).where(TrackItem.track_id == track.id)
            result = await self.db.execute(stmt)
            items = result.scalars().all()

            for item in items:
                if item.source_url and item.source_url not in seen_urls:
                    source_files.append(item.source_url)
                    seen_urls.add(item.source_url)

        return source_files

    async def apply_transition(
        self,
        clip1_path: str,
        clip2_path: str,
        transition: Transition,
        output_path: str,
    ) -> str:
        """Apply transition effect between two clips.

        Args:
            clip1_path: Path to first clip
            clip2_path: Path to second clip
            transition: Transition object
            output_path: Path to output file

        Returns:
            Path to transitioned output
        """
        duration = transition.default_duration

        # Build xfade filter based on transition type
        transition_map = {
            "fade": "fade",
            "dissolve": "dissolve",
            "slide": "slideleft",
            "wipe": "wipeleft",
            "zoom": "fadein",
            "blur": "fadeblack",
        }

        effect = transition_map.get(transition.transition_type.value, "fade")

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            clip1_path,
            "-i",
            clip2_path,
            "-filter_complex",
            f"[0:v][1:v]xfade=transition={effect}:duration={duration}:offset=0[vout]",
            "-map",
            "[vout]",
            output_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg transition failed: {stderr.decode()}")

        return output_path

    async def render_text_overlay(
        self,
        text_item: TrackItem,
        duration: float,
        output_path: str,
        width: int = 1920,
        height: int = 1080,
    ) -> str:
        """Render text to transparent video overlay.

        Args:
            text_item: TrackItem with text content
            duration: Duration in seconds
            output_path: Path to output file
            width: Output width
            height: Output height

        Returns:
            Path to text overlay video
        """
        text_content = text_item.text_content or ""
        text_style = text_item.text_style or {}

        font_size = text_style.get("font_size", 48)
        font_color = text_style.get("color", "white")
        font_family = text_style.get("font_family", "Arial")
        alignment = text_style.get("alignment", "center")

        # Calculate position based on alignment
        if alignment == "center":
            x_expr = "(w-text_w)/2"
            y_expr = "(h-text_h)/2"
        elif alignment == "left":
            x_expr = "50"
            y_expr = "(h-text_h)/2"
        else:  # right
            x_expr = "w-text_w-50"
            y_expr = "(h-text_h)/2"

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s={width}x{height}:r=30:d={duration}",
            "-vf",
            f"drawtext=text='{text_content}':fontfile={font_family}:fontsize={font_size}:fontcolor={font_color}:x={x_expr}:y={y_expr},format=rgba,colorkey=0x000000:0.01:0.1",
            "-c:v",
            "png",
            output_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg text rendering failed: {stderr.decode()}")

        return output_path

    async def generate_preview_frame(
        self,
        project: Project,
        time: float,
        output_path: str,
    ) -> str:
        """Generate single frame preview at specified time.

        Args:
            project: Project object
            time: Time in seconds
            output_path: Path to output image file

        Returns:
            Path to preview image
        """
        # Get all tracks
        stmt = select(Track).where(Track.project_id == project.id).order_by(Track.z_index)
        result = await self.db.execute(stmt)
        tracks = result.scalars().all()

        # Build filter for single frame at specified time
        filter_complex = await self.build_ffmpeg_filter_complex(project, tracks)

        # Get source files
        source_files = await self._get_source_files(tracks)

        # Build FFmpeg command for single frame
        cmd = ["ffmpeg", "-y"]

        # Add input files with seek
        for source in source_files:
            cmd.extend(["-ss", str(time), "-i", source])

        if filter_complex:
            cmd.extend(["-filter_complex", filter_complex])

        cmd.extend([
            "-map", "[vout]",
            "-frames:v", "1",
            "-q:v", "2",
            output_path,
        ])

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg preview generation failed: {stderr.decode()}")

        return output_path

    def estimate_render_time(self, project: Project) -> float:
        """Estimate rendering time based on project complexity.

        Args:
            project: Project object

        Returns:
            Estimated seconds to render
        """
        # Basic estimation formula
        # Factors: duration, resolution, number of tracks, effects
        base_time = project.duration_seconds * 0.5  # 0.5x realtime as baseline

        # Resolution multiplier
        pixels = project.width * project.height
        if pixels > 1920 * 1080:  # 4K
            base_time *= 2.0
        elif pixels > 1280 * 720:  # 1080p
            base_time *= 1.5

        # Add 10% for each track beyond 2
        # Note: In production, we'd count actual tracks from database
        base_time *= 1.2

        return base_time

    async def cancel_render(self, job_id: str) -> None:
        """Cancel ongoing render job.

        Args:
            job_id: ARQ job ID to cancel
        """
        # In production, this would interact with ARQ to cancel the job
        # For now, this is a placeholder
        pass
