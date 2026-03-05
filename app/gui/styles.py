"""Theme configuration and style constants for the GUI."""
import platform

# Detect platform for font selection
_IS_WINDOWS = platform.system() == "Windows"
_IS_MAC = platform.system() == "Darwin"

# Font families
if _IS_WINDOWS:
    FONT_FAMILY = "Segoe UI"
    MONO_FAMILY = "Consolas"
elif _IS_MAC:
    FONT_FAMILY = "SF Pro Display"
    MONO_FAMILY = "SF Mono"
else:
    FONT_FAMILY = "Helvetica"
    MONO_FAMILY = "Courier"

# Font tuples (family, size, weight)
FONTS = {
    "title": (FONT_FAMILY, 20, "bold"),
    "heading": (FONT_FAMILY, 16, "bold"),
    "subheading": (FONT_FAMILY, 13, "bold"),
    "body": (FONT_FAMILY, 12),
    "body_small": (FONT_FAMILY, 11),
    "mono": (MONO_FAMILY, 12),
    "mono_large": (MONO_FAMILY, 28, "bold"),
    "mono_medium": (MONO_FAMILY, 16),
    "label": (FONT_FAMILY, 11, "bold"),
    "value": (FONT_FAMILY, 12),
    "button": (FONT_FAMILY, 12, "bold"),
}

# Color palette
COLORS = {
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "primary_dark": "#1E40AF",
    "success": "#16A34A",
    "success_bg": "#052E16",
    "warning": "#D97706",
    "warning_bg": "#451A03",
    "error": "#DC2626",
    "error_bg": "#450A0A",
    "info": "#0EA5E9",
    "info_bg": "#0C2D48",
    "bg_dark": "#0F172A",
    "bg_card": "#1E293B",
    "bg_input": "#334155",
    "border": "#475569",
    "text": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "passcode_found": "#22C55E",
    "passcode_not_found": "#EF4444",
}

# Widget sizing
PADDING = {
    "window": 16,
    "section": 12,
    "widget": 8,
    "small": 4,
}

SIZES = {
    "window_width": 950,
    "window_height": 680,
    "min_width": 800,
    "min_height": 550,
    "entry_height": 36,
    "button_height": 36,
    "corner_radius": 8,
}
