"""Subtitle styling service for managing subtitle styles and presets."""

import re
from typing import Any
from uuid import UUID

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subtitle import (
    SubtitleStyle,
    SubtitleStylePreset,
    FontWeight,
    PositionVertical,
    PositionHorizontal,
    AnimationType,
)


class SubtitleStylingService:
    """Service for subtitle styling operations."""

    def __init__(self, db: AsyncSession):
        """Initialize subtitle styling service."""
        self.db = db

    async def get_or_create_default_style(
        self, video_id: UUID, language: str, user_id: UUID
    ) -> SubtitleStyle:
        """Get existing subtitle style or create with default values."""
        # Try to find existing style
        result = await self.db.execute(
            select(SubtitleStyle).where(
                SubtitleStyle.video_id == video_id,
                SubtitleStyle.language_code == language,
            )
        )
        existing_style = result.scalar_one_or_none()

        if existing_style:
            return existing_style

        # Create new style with defaults
        new_style = SubtitleStyle(
            video_id=video_id,
            language_code=language,
            created_by=user_id,
        )
        self.db.add(new_style)
        await self.db.commit()
        await self.db.refresh(new_style)
        return new_style

    async def apply_preset(
        self, video_id: UUID, preset_name: str, language: str, user_id: UUID
    ) -> SubtitleStyle:
        """Apply preset configuration to create or update subtitle style."""
        # Load preset
        result = await self.db.execute(
            select(SubtitleStylePreset).where(SubtitleStylePreset.name == preset_name)
        )
        preset = result.scalar_one_or_none()

        if not preset:
            raise ValueError(f"Preset '{preset_name}' not found")

        # Check if style already exists
        result = await self.db.execute(
            select(SubtitleStyle).where(
                SubtitleStyle.video_id == video_id,
                SubtitleStyle.language_code == language,
            )
        )
        existing_style = result.scalar_one_or_none()

        if existing_style:
            # Update existing style with preset values
            style_config = preset.style_config
            for key, value in style_config.items():
                if hasattr(existing_style, key):
                    setattr(existing_style, key, value)
            existing_style.preset_name = preset_name
            style = existing_style
        else:
            # Create new style with preset values
            style_config = preset.style_config
            style = SubtitleStyle(
                video_id=video_id,
                language_code=language,
                created_by=user_id,
                preset_name=preset_name,
                **style_config,
            )
            self.db.add(style)

        # Increment preset usage count
        preset.usage_count += 1

        await self.db.commit()
        await self.db.refresh(style)
        return style

    async def update_style(
        self, style_id: UUID, updates: dict[str, Any]
    ) -> SubtitleStyle:
        """Update subtitle style with validated properties."""
        # Validate updates
        errors = self.validate_style(updates)
        if errors:
            raise ValueError(f"Validation errors: {errors}")

        # Get existing style
        result = await self.db.execute(
            select(SubtitleStyle).where(SubtitleStyle.id == style_id)
        )
        style = result.scalar_one_or_none()

        if not style:
            raise ValueError(f"Subtitle style {style_id} not found")

        # Apply updates
        for key, value in updates.items():
            if hasattr(style, key):
                setattr(style, key, value)

        await self.db.commit()
        await self.db.refresh(style)
        return style

    async def clone_style(
        self, source_style_id: UUID, target_video_id: UUID, user_id: UUID
    ) -> SubtitleStyle:
        """Clone style from one video to another."""
        # Get source style
        result = await self.db.execute(
            select(SubtitleStyle).where(SubtitleStyle.id == source_style_id)
        )
        source_style = result.scalar_one_or_none()

        if not source_style:
            raise ValueError(f"Source style {source_style_id} not found")

        # Create new style with same properties
        new_style = SubtitleStyle(
            video_id=target_video_id,
            language_code=source_style.language_code,
            created_by=user_id,
            font_family=source_style.font_family,
            font_size=source_style.font_size,
            font_weight=source_style.font_weight,
            font_color=source_style.font_color,
            font_alpha=source_style.font_alpha,
            background_enabled=source_style.background_enabled,
            background_color=source_style.background_color,
            background_alpha=source_style.background_alpha,
            background_padding=source_style.background_padding,
            background_radius=source_style.background_radius,
            outline_enabled=source_style.outline_enabled,
            outline_color=source_style.outline_color,
            outline_width=source_style.outline_width,
            position_vertical=source_style.position_vertical,
            position_horizontal=source_style.position_horizontal,
            margin_vertical=source_style.margin_vertical,
            margin_horizontal=source_style.margin_horizontal,
            max_width_percent=source_style.max_width_percent,
            words_per_line=source_style.words_per_line,
            max_lines=source_style.max_lines,
            min_display_duration=source_style.min_display_duration,
            max_display_duration=source_style.max_display_duration,
            animation_type=source_style.animation_type,
            animation_duration=source_style.animation_duration,
            preset_name=source_style.preset_name,
        )
        self.db.add(new_style)
        await self.db.commit()
        await self.db.refresh(new_style)
        return new_style

    def validate_style(self, style_data: dict[str, Any]) -> dict[str, list[str]]:
        """Validate style properties and return errors."""
        errors: dict[str, list[str]] = {}

        # Validate font_size
        if "font_size" in style_data:
            size = style_data["font_size"]
            if not isinstance(size, int) or not (12 <= size <= 72):
                errors.setdefault("font_size", []).append(
                    "Font size must be between 12 and 72 pixels"
                )

        # Validate opacity values
        for field in ["font_alpha", "background_alpha"]:
            if field in style_data:
                alpha = style_data[field]
                if not isinstance(alpha, (int, float)) or not (0.0 <= alpha <= 1.0):
                    errors.setdefault(field, []).append(f"{field} must be between 0.0 and 1.0")

        # Validate outline_width
        if "outline_width" in style_data:
            width = style_data["outline_width"]
            if not isinstance(width, int) or not (0 <= width <= 8):
                errors.setdefault("outline_width", []).append(
                    "Outline width must be between 0 and 8 pixels"
                )

        # Validate margins
        for field in ["margin_vertical", "margin_horizontal"]:
            if field in style_data:
                margin = style_data[field]
                if not isinstance(margin, int) or not (0 <= margin <= 200):
                    errors.setdefault(field, []).append(
                        f"{field} must be between 0 and 200 pixels"
                    )

        # Validate max_width_percent
        if "max_width_percent" in style_data:
            width = style_data["max_width_percent"]
            if not isinstance(width, int) or not (20 <= width <= 100):
                errors.setdefault("max_width_percent", []).append(
                    "Max width percent must be between 20 and 100"
                )

        # Validate color values (hex format)
        color_fields = ["font_color", "background_color", "outline_color"]
        hex_pattern = re.compile(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})$")
        for field in color_fields:
            if field in style_data:
                color = style_data[field]
                if not isinstance(color, str) or not hex_pattern.match(color):
                    errors.setdefault(field, []).append(
                        f"{field} must be a valid hex color (#RRGGBB or #RRGGBBAA)"
                    )

        return errors

    async def generate_style_preview_image(
        self, style: SubtitleStyle, sample_text: str = "Sample subtitle text"
    ) -> bytes:
        """Generate preview image with styled subtitle text."""
        # Create image (1920x200 for subtitle preview)
        width, height = 1920, 200
        img = Image.new("RGB", (width, height), color=(50, 50, 50))
        draw = ImageDraw.Draw(img, "RGBA")

        # Parse colors
        font_color = self._hex_to_rgb(style.font_color)
        font_alpha = int(style.font_alpha * 255)
        font_color_rgba = (*font_color, font_alpha)

        # Calculate text position
        text_bbox = draw.textbbox((0, 0), sample_text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Horizontal position
        if style.position_horizontal.value == "left":
            x = style.margin_horizontal
        elif style.position_horizontal.value == "right":
            x = width - text_width - style.margin_horizontal
        else:  # center
            x = (width - text_width) // 2

        # Vertical position (for preview, always centered)
        y = (height - text_height) // 2

        # Draw background if enabled
        if style.background_enabled:
            bg_color = self._hex_to_rgb(style.background_color)
            bg_alpha = int(style.background_alpha * 255)
            bg_color_rgba = (*bg_color, bg_alpha)

            padding = style.background_padding
            bg_bbox = (
                x - padding,
                y - padding,
                x + text_width + padding,
                y + text_height + padding,
            )
            draw.rounded_rectangle(
                bg_bbox, radius=style.background_radius, fill=bg_color_rgba
            )

        # Draw text outline if enabled
        if style.outline_enabled:
            outline_color = self._hex_to_rgb(style.outline_color)
            outline_width = style.outline_width
            for offset_x in range(-outline_width, outline_width + 1):
                for offset_y in range(-outline_width, outline_width + 1):
                    if offset_x != 0 or offset_y != 0:
                        draw.text(
                            (x + offset_x, y + offset_y),
                            sample_text,
                            fill=outline_color,
                        )

        # Draw main text
        draw.text((x, y), sample_text, fill=font_color_rgba)

        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()

    async def export_style_as_preset(
        self, style_id: UUID, name: str, description: str, is_public: bool = True
    ) -> SubtitleStylePreset:
        """Convert SubtitleStyle to reusable preset."""
        # Get style
        result = await self.db.execute(
            select(SubtitleStyle).where(SubtitleStyle.id == style_id)
        )
        style = result.scalar_one_or_none()

        if not style:
            raise ValueError(f"Style {style_id} not found")

        # Create preset with style configuration
        preset = SubtitleStylePreset(
            name=name,
            description=description,
            platform="custom",
            style_config={
                "font_family": style.font_family,
                "font_size": style.font_size,
                "font_weight": style.font_weight.value,
                "font_color": style.font_color,
                "font_alpha": style.font_alpha,
                "background_enabled": style.background_enabled,
                "background_color": style.background_color,
                "background_alpha": style.background_alpha,
                "background_padding": style.background_padding,
                "background_radius": style.background_radius,
                "outline_enabled": style.outline_enabled,
                "outline_color": style.outline_color,
                "outline_width": style.outline_width,
                "position_vertical": style.position_vertical.value,
                "position_horizontal": style.position_horizontal.value,
                "margin_vertical": style.margin_vertical,
                "margin_horizontal": style.margin_horizontal,
                "max_width_percent": style.max_width_percent,
                "words_per_line": style.words_per_line,
                "max_lines": style.max_lines,
                "min_display_duration": style.min_display_duration,
                "max_display_duration": style.max_display_duration,
                "animation_type": style.animation_type.value,
                "animation_duration": style.animation_duration,
            },
            is_public=is_public,
            created_by=style.created_by,
        )
        self.db.add(preset)
        await self.db.commit()
        await self.db.refresh(preset)
        return preset

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore
        elif len(hex_color) == 8:
            # Skip alpha channel for RGB
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore
        else:
            return (255, 255, 255)  # Default to white
