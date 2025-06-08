# front/config.py

# Global configuration settings for the GUI
ENABLE_DRAG_DROP = True
ENABLE_EVALUATION_TAB = True
ENABLE_FULLSCREEN = False
DEFAULT_THEME = "arc"  # Base theme, will be customized with Apple styles

# Animation settings
ENABLE_ANIMATIONS = True  # Can be toggled for performance

# Apple-style color scheme
APPLE_COLORS = {
    'background': '#F2F2F7',           # Light gray background
    'surface': '#FFFFFF',              # White surface
    'primary': '#007AFF',              # System blue
    'primary_dark': '#0051D5',         # Pressed state
    'primary_light': '#34AAFF',        # Hover state
    'text_primary': '#000000',         # Primary text
    'text_secondary': '#3C3C43',       # Secondary text (60% opacity)
    'text_tertiary': '#C7C7CC',        # Tertiary text
    'separator': '#E5E5EA',            # Separator lines
    'error': '#FF3B30',                # System red
    'success': '#34C759',              # System green
    'warning': '#FF9500',              # System orange
    'shadow': 'rgba(0, 0, 0, 0.04)',  # Subtle shadow
    'drop_hover': '#E8F0FE'            # Drop zone hover color
}

# Typography settings (approximating San Francisco)
FONTS = {
    'system': ('SF Pro Text', 'Helvetica Neue', 'Segoe UI', 'Arial'),
    'title_large': 22,
    'title_medium': 17,
    'title_small': 15,
    'body_large': 17,
    'body_medium': 15,
    'body_small': 13,
    'caption': 12
}

# Component sizing
PADDING = {
    'small': 8,
    'medium': 12,
    'large': 16,
    'xlarge': 20
}

CORNER_RADIUS = 12  # Standard corner radius for cards and buttons
BUTTON_HEIGHT = 36  # Standard button height

# Performance settings for Raspberry Pi
MAX_CACHED_IMAGES = 20  # Maximum images to keep in memory
IMAGE_CACHE_SIZE_MB = 200  # Maximum cache size in MB
ANIMATION_DURATION = 200  # Milliseconds for animations
ANIMATION_FPS = 30  # Target FPS for animations
NOTIFICATION_DURATION = 2000  # 2 seconds for notifications
MAX_HISTORY_DISPLAY = 30  # Maximum history entries to display
IMAGE_PREVIEW_SIZE = 600  # Fixed preview size for images and matrices