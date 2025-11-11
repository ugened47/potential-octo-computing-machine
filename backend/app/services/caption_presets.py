"""Caption style presets configuration."""

from app.models import StylePreset

CAPTION_STYLE_PRESETS = {
    StylePreset.MINIMAL: {
        "font_family": "Arial",
        "font_size": 24,
        "font_weight": "normal",
        "text_color": "#FFFFFF",
        "background_color": "rgba(0, 0, 0, 0)",
        "stroke_color": "#000000",
        "stroke_width": 2,
        "position": "bottom",
        "y_offset": 80,
        "alignment": "center",
        "animation": "fade",
        "max_chars_per_line": 35,
        "max_lines": 2,
    },
    StylePreset.BOLD: {
        "font_family": "Arial Black",
        "font_size": 32,
        "font_weight": "bold",
        "text_color": "#FFFFFF",
        "background_color": "rgba(255, 215, 0, 0.9)",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "position": "bottom",
        "y_offset": 80,
        "alignment": "center",
        "animation": "pop",
        "max_chars_per_line": 30,
        "max_lines": 2,
    },
    StylePreset.GAMING: {
        "font_family": "Impact",
        "font_size": 36,
        "font_weight": "bold",
        "text_color": "#00FFFF",
        "background_color": "rgba(255, 0, 255, 0.3)",
        "stroke_color": "#FF00FF",
        "stroke_width": 4,
        "position": "center",
        "y_offset": 0,
        "alignment": "center",
        "animation": "word-by-word",
        "max_chars_per_line": 25,
        "max_lines": 2,
    },
    StylePreset.PODCAST: {
        "font_family": "Georgia",
        "font_size": 28,
        "font_weight": "normal",
        "text_color": "#FFFFFF",
        "background_color": "rgba(0, 0, 0, 0.7)",
        "stroke_color": "#000000",
        "stroke_width": 0,
        "position": "center",
        "y_offset": 0,
        "alignment": "center",
        "animation": "fade",
        "max_chars_per_line": 40,
        "max_lines": 3,
    },
    StylePreset.VLOG: {
        "font_family": "Verdana",
        "font_size": 28,
        "font_weight": "normal",
        "text_color": "#FFD700",
        "background_color": "rgba(0, 0, 0, 0.5)",
        "stroke_color": "#FFFFFF",
        "stroke_width": 2,
        "position": "bottom",
        "y_offset": 80,
        "alignment": "center",
        "animation": "slide",
        "max_chars_per_line": 35,
        "max_lines": 2,
    },
    StylePreset.PROFESSIONAL: {
        "font_family": "Helvetica",
        "font_size": 24,
        "font_weight": "normal",
        "text_color": "#000000",
        "background_color": "rgba(255, 255, 255, 0.9)",
        "stroke_color": "#000000",
        "stroke_width": 0,
        "position": "bottom",
        "y_offset": 60,
        "alignment": "center",
        "animation": "fade",
        "max_chars_per_line": 40,
        "max_lines": 2,
    },
    StylePreset.TRENDY: {
        "font_family": "Arial",
        "font_size": 32,
        "font_weight": "bold",
        "text_color": "#FFFFFF",
        "background_color": "rgba(0, 0, 0, 0.6)",
        "stroke_color": "#FFD700",
        "stroke_width": 3,
        "position": "bottom",
        "y_offset": 80,
        "alignment": "center",
        "animation": "word-by-word",
        "max_chars_per_line": 30,
        "max_lines": 2,
    },
    StylePreset.CUSTOM: {
        "font_family": "Arial",
        "font_size": 24,
        "font_weight": "normal",
        "text_color": "#FFFFFF",
        "background_color": "rgba(0, 0, 0, 0.5)",
        "stroke_color": "#000000",
        "stroke_width": 2,
        "position": "bottom",
        "y_offset": 60,
        "alignment": "center",
        "animation": "none",
        "max_chars_per_line": 35,
        "max_lines": 2,
    },
}


def get_caption_style(preset: StylePreset) -> dict:
    """Get caption style configuration for a preset.

    Args:
        preset: Style preset enum value

    Returns:
        dict: Caption style configuration
    """
    return CAPTION_STYLE_PRESETS.get(preset, CAPTION_STYLE_PRESETS[StylePreset.MINIMAL])


def merge_caption_style(preset: StylePreset, custom_overrides: dict) -> dict:
    """Merge preset caption style with custom overrides.

    Args:
        preset: Base style preset
        custom_overrides: Custom style overrides

    Returns:
        dict: Merged caption style configuration
    """
    base_style = get_caption_style(preset).copy()
    base_style.update(custom_overrides)
    return base_style
