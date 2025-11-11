"""Caption style presets for social media platforms."""

from typing import Any

# Caption style presets dictionary
CAPTION_PRESETS: dict[str, dict[str, Any]] = {
    "minimal": {
        "font_family": "Arial",
        "font_size": 4,  # % of video height
        "font_weight": "normal",
        "text_color": "#FFFFFF",
        "background_color": "#00000000",  # Transparent
        "stroke_color": "#000000",
        "stroke_width": 2,
        "position": "bottom",
        "y_offset": 90,  # % from top
        "alignment": "center",
        "animation": "fade",
        "max_chars_per_line": 40,
        "max_lines": 2,
    },
    "bold": {
        "font_family": "Arial Bold",
        "font_size": 6,
        "font_weight": "extra-bold",
        "text_color": "#FFFFFF",
        "background_color": "#FFD700CC",  # Gold with transparency
        "stroke_color": "#000000",
        "stroke_width": 3,
        "position": "bottom",
        "y_offset": 85,
        "alignment": "center",
        "animation": "pop",
        "max_chars_per_line": 30,
        "max_lines": 2,
    },
    "gaming": {
        "font_family": "Impact",
        "font_size": 7,
        "font_weight": "extra-bold",
        "text_color": "#00FFFF",  # Cyan
        "background_color": "#FF00FFCC",  # Magenta with transparency
        "stroke_color": "#000000",
        "stroke_width": 4,
        "position": "center",
        "y_offset": 50,
        "alignment": "center",
        "animation": "word-by-word",
        "max_chars_per_line": 25,
        "max_lines": 3,
    },
    "podcast": {
        "font_family": "Georgia",
        "font_size": 5,
        "font_weight": "normal",
        "text_color": "#FFFFFF",
        "background_color": "#000000AA",  # Semi-transparent black
        "stroke_color": "#FFFFFF",
        "stroke_width": 0,
        "position": "center",
        "y_offset": 50,
        "alignment": "center",
        "animation": "fade",
        "max_chars_per_line": 35,
        "max_lines": 3,
    },
    "vlog": {
        "font_family": "Helvetica Neue",
        "font_size": 5,
        "font_weight": "bold",
        "text_color": "#FFFFFF",
        "background_color": "#FF6B9DCC",  # Pink with transparency
        "stroke_color": "#FFFFFF",
        "stroke_width": 1,
        "position": "bottom",
        "y_offset": 80,
        "alignment": "center",
        "animation": "slide",
        "max_chars_per_line": 32,
        "max_lines": 2,
    },
    "professional": {
        "font_family": "Arial",
        "font_size": 4,
        "font_weight": "normal",
        "text_color": "#000000",
        "background_color": "#FFFFFFCC",  # White with transparency
        "stroke_color": "#FFFFFF",
        "stroke_width": 0,
        "position": "bottom",
        "y_offset": 88,
        "alignment": "center",
        "animation": "fade",
        "max_chars_per_line": 40,
        "max_lines": 2,
    },
    "trendy": {
        "font_family": "Montserrat Bold",
        "font_size": 6,
        "font_weight": "extra-bold",
        "text_color": "#FFFFFF",
        "background_color": "#FF0050CC",  # TikTok pink
        "stroke_color": "#000000",
        "stroke_width": 3,
        "position": "center",
        "y_offset": 50,
        "alignment": "center",
        "animation": "word-by-word",
        "max_chars_per_line": 25,
        "max_lines": 3,
    },
}


def get_caption_preset(preset_name: str) -> dict[str, Any]:
    """Get caption style preset by name.

    Args:
        preset_name: Name of the preset

    Returns:
        Caption style dictionary

    Raises:
        ValueError: If preset name is not found
    """
    preset = CAPTION_PRESETS.get(preset_name.lower())
    if preset is None:
        raise ValueError(f"Unknown caption preset: {preset_name}")
    return preset.copy()


def list_caption_presets() -> list[str]:
    """List all available caption preset names.

    Returns:
        List of preset names
    """
    return list(CAPTION_PRESETS.keys())
