"""Seed script for social media template system presets."""

import asyncio
from datetime import datetime
from uuid import uuid4

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import engine
from app.models import PlatformType, SocialMediaTemplate, StylePreset


async def seed_templates() -> None:
    """Create system preset templates for all major social media platforms."""

    # Define system preset templates
    system_presets = [
        {
            "name": "YouTube Shorts",
            "description": "Optimized for YouTube Shorts - vertical format with bold captions",
            "platform": PlatformType.YOUTUBE_SHORTS,
            "aspect_ratio": "9:16",
            "max_duration_seconds": 60,
            "auto_captions": True,
            "style_preset": StylePreset.BOLD,
            "caption_style": {
                "font_family": "Arial Bold",
                "font_size": 6,  # % of video height
                "font_weight": "extra-bold",
                "text_color": "#FFFFFF",
                "background_color": "#000000CC",  # semi-transparent black
                "stroke_color": "#000000",
                "stroke_width": 2,
                "position": "bottom",
                "y_offset": 85,  # % from top
                "alignment": "center",
                "animation": "pop",
                "max_chars_per_line": 30,
                "max_lines": 2,
            },
            "video_codec": "h264",
            "audio_codec": "aac",
            "bitrate": "8M",
        },
        {
            "name": "TikTok",
            "description": "Optimized for TikTok - vertical format with trendy animated captions",
            "platform": PlatformType.TIKTOK,
            "aspect_ratio": "9:16",
            "max_duration_seconds": 60,
            "auto_captions": True,
            "style_preset": StylePreset.TRENDY,
            "caption_style": {
                "font_family": "Montserrat Bold",
                "font_size": 6,
                "font_weight": "extra-bold",
                "text_color": "#FFFFFF",
                "background_color": "#FF0050CC",  # TikTok pink with transparency
                "stroke_color": "#000000",
                "stroke_width": 3,
                "position": "center",
                "y_offset": 50,
                "alignment": "center",
                "animation": "word-by-word",
                "max_chars_per_line": 25,
                "max_lines": 3,
            },
            "video_codec": "h264",
            "audio_codec": "aac",
            "bitrate": "8M",
        },
        {
            "name": "Instagram Reels",
            "description": "Optimized for Instagram Reels - vertical format with aesthetic captions",
            "platform": PlatformType.INSTAGRAM_REELS,
            "aspect_ratio": "9:16",
            "max_duration_seconds": 90,
            "auto_captions": True,
            "style_preset": StylePreset.VLOG,
            "caption_style": {
                "font_family": "Helvetica Neue",
                "font_size": 5,
                "font_weight": "bold",
                "text_color": "#FFFFFF",
                "background_color": "#405DE680",  # Instagram purple with transparency
                "stroke_color": "#FFFFFF",
                "stroke_width": 1,
                "position": "bottom",
                "y_offset": 80,
                "alignment": "center",
                "animation": "slide",
                "max_chars_per_line": 35,
                "max_lines": 2,
            },
            "video_codec": "h264",
            "audio_codec": "aac",
            "bitrate": "8M",
        },
        {
            "name": "Twitter/X Video",
            "description": "Optimized for Twitter/X - flexible aspect ratio with minimal captions",
            "platform": PlatformType.TWITTER,
            "aspect_ratio": "16:9",
            "max_duration_seconds": 140,
            "auto_captions": True,
            "style_preset": StylePreset.MINIMAL,
            "caption_style": {
                "font_family": "Arial",
                "font_size": 4,
                "font_weight": "normal",
                "text_color": "#FFFFFF",
                "background_color": "#00000000",  # transparent
                "stroke_color": "#000000",
                "stroke_width": 2,
                "position": "bottom",
                "y_offset": 90,
                "alignment": "center",
                "animation": "fade",
                "max_chars_per_line": 40,
                "max_lines": 2,
            },
            "video_codec": "h264",
            "audio_codec": "aac",
            "bitrate": "5M",
        },
        {
            "name": "LinkedIn Video",
            "description": "Optimized for LinkedIn - square format with professional captions",
            "platform": PlatformType.LINKEDIN,
            "aspect_ratio": "1:1",
            "max_duration_seconds": 600,
            "auto_captions": True,
            "style_preset": StylePreset.PROFESSIONAL,
            "caption_style": {
                "font_family": "Georgia",
                "font_size": 4,
                "font_weight": "normal",
                "text_color": "#000000",
                "background_color": "#FFFFFFCC",  # white with transparency
                "stroke_color": "#FFFFFF",
                "stroke_width": 0,
                "position": "bottom",
                "y_offset": 88,
                "alignment": "center",
                "animation": "fade",
                "max_chars_per_line": 40,
                "max_lines": 2,
            },
            "video_codec": "h264",
            "audio_codec": "aac",
            "bitrate": "5M",
        },
    ]

    async with AsyncSession(engine) as session:
        # Check if system presets already exist
        result = await session.execute(
            select(SocialMediaTemplate).where(SocialMediaTemplate.is_system_preset == True)
        )
        existing_presets = result.scalars().all()

        if existing_presets:
            print(f"Found {len(existing_presets)} existing system presets. Skipping seed.")
            return

        # Create system presets
        print("Creating system preset templates...")
        for preset_data in system_presets:
            template = SocialMediaTemplate(
                id=uuid4(),
                **preset_data,
                is_system_preset=True,
                user_id=None,
                is_active=True,
                usage_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(template)
            print(f"  - Created: {template.name}")

        await session.commit()
        print(f"Successfully created {len(system_presets)} system preset templates!")


async def main() -> None:
    """Main entry point."""
    await seed_templates()


if __name__ == "__main__":
    asyncio.run(main())
