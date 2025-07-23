# GUI Colors
COLORS = {
    'primary': '#2196F3',      # Main theme color
    'secondary': '#FFC107',    # Secondary accent color
    'background': '#F5F5F5',   # Background color
    'text': '#212121',         # Main text color
    'user_message': '#E3F2FD', # User message background
    'assistant_message': '#FFFFFF', # Assistant message background
    'error': '#F44336',        # Error messages
    'success': '#4CAF50',      # Success messages
    'warning': '#FF9800'       # Warning messages
}

# Status Icons and Emojis
STATUS_EMOJIS = {
    'complete': '✅',
    'in progress': '🔄',
    'on hold': '⏸️',
    'unknown': '❓'
}

# Command Types
COMMAND_TYPES = {
    'UPDATE_STATUS': 'update_status',
    'CREATE_TASK': 'create_task',
    'UPDATE_DATE': 'update_date',
    'DELETE_TASK': 'delete_task'
}

# Task Statuses
TASK_STATUSES = {
    'COMPLETE': 'complete',
    'IN_PROGRESS': 'in progress',
    'ON_HOLD': 'on hold'
}

# Date Formats
DATE_FORMATS = {
    'DISPLAY': "%B %d, %Y",
    'STORAGE': "%Y-%m-%d",
    'LOG': "%Y-%m-%d %H:%M:%S"
}

# File Paths
FILE_PATHS = {
    'TASK_MAPPING': 'task_mapping.json',
    'TASK_STATE': 'task_state.json',
    'TASK_OUTPUT': 'task_output.json',
    'LOG_FILE': 'visa4d.log'
}

# GUI Settings
GUI_SETTINGS = {
    'WINDOW_SIZE': "1000x700",
    'MIN_WIDTH': 800,
    'MIN_HEIGHT': 600,
    'FONT_FAMILY': "Segoe UI",
    'DEFAULT_FONT_SIZE': 12,
    'SMALL_FONT_SIZE': 10,
    'LARGE_FONT_SIZE': 14
}

# Recording Settings
RECORDING_SETTINGS = {
    'TIMEOUT': 8,
    'PHRASE_TIME_LIMIT': 15,
    'CALIBRATION_DURATION': 2
}

# Message Settings
MESSAGE_SETTINGS = {
    'MAX_WIDTH': 700,
    'PADDING_X': 10,
    'PADDING_Y': 5
}

# Default Task Categories
DEFAULT_TASK_MAPPING = {
    "flooring": "Flooring Installation",
    "roofing": "Roofing",
    "concrete": "Concrete Pouring",
    "painting": "Painting and Decorating",
    "plumbing": "Plumbing Installation",
    "electrical": "Electrical Wiring",
    "hvac": "HVAC Installation",
    "drywall": "Drywall Installation"
}

# Error Messages
ERROR_MESSAGES = {
    'INVALID_COMMAND': "I couldn't understand your command. Please try again.",
    'MISSING_TASK': "Please specify a valid task name.",
    'MISSING_DATE': "Please specify a valid date.",
    'MISSING_STATUS': "Please specify a valid status (complete, in progress, or on hold).",
    'RECORDING_ERROR': "An error occurred during recording. Please try again.",
    'PROCESSING_ERROR': "An error occurred while processing your command. Please try again.",
    'FILE_NOT_FOUND': "Required file not found.",
    'INVALID_JSON': "Invalid JSON format in configuration file."
}

# Success Messages
SUCCESS_MESSAGES = {
    'TASK_CREATED': "Task '{}' has been created successfully.",
    'STATUS_UPDATED': "Status for task '{}' has been updated to {}.",
    'DATE_UPDATED': "Schedule for task '{}' has been updated to {}.",
    'TASK_DELETED': "Task '{}' has been deleted successfully."
}

# NLP Settings
NLP_SETTINGS = {
    'MODEL_NAME': "en_core_web_lg",
    'MAX_FEATURES': 5000,
    'N_ESTIMATORS': 100,
    'MAX_DEPTH': 10,
    'RANDOM_STATE': 42,
    'TRANSFORMER_MODEL': 'all-MiniLM-L6-v2'
}

# Logging Settings
LOGGING_CONFIG = {
    'VERSION': 1,
    'LEVEL': 'INFO',
    'FORMAT': '%(asctime)s - %(levelname)s - %(message)s',
    'DATE_FORMAT': '%Y-%m-%d %H:%M:%S'
}



class ThemeColors:
    # Main theme colors
    PRIMARY = "#3B82F6"  # Bright blue
    PRIMARY_HOVER = "#2563EB"  # Darker blue for hover states
    SECONDARY = "#10B981"  # Emerald green
    ACCENT = "#8B5CF6"  # Purple
    
    # Background colors
    BG_DARK = "#1F2937"
    BG_LIGHT = "#F3F4F6"
    
    # Message bubbles
    USER_MSG_BG = "#3B82F6"  # Blue
    USER_MSG_TEXT = "#FFFFFF"
    BOT_MSG_BG = "#F3F4F6"  # Light gray
    BOT_MSG_TEXT = "#1F2937"
    
    # Status colors
    SUCCESS = "#10B981"  # Green
    WARNING = "#F59E0B"  # Yellow
    ERROR = "#EF4444"   # Red
    INFO = "#3B82F6"    # Blue

class UIConfig:
    # Font configurations
    FONTS = {
        "main": "Segoe UI",
        "headers": "Segoe UI Semibold",
        "messages": "Segoe UI"
    }
    
    FONT_SIZES = {
        "tiny": 10,
        "small": 12,
        "medium": 14,
        "large": 16,
        "xlarge": 20
    }
    
    # Spacing and sizing
    PADDING = {
        "small": 5,
        "medium": 10,
        "large": 15,
        "xlarge": 20
    }
    
    CORNERS = {
        "small": 5,
        "medium": 10,
        "large": 15,
        "message": 20
    }
    
    # Animation durations (ms)
    ANIMATIONS = {
        "quick": 150,
        "normal": 250,
        "slow": 350
    }

class StatusEmojis:
    RECORDING = "⏺️"
    SEND = "➤"
    MIC = "🎤"
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    THINKING = "💭"

# Theme presets
THEME_PRESETS = {
    "light": {
        "bg_color": "#FFFFFF",
        "fg_color": "#1F2937",
        "accent_color": ThemeColors.PRIMARY,
        "secondary_bg": "#F3F4F6"
    },
    "dark": {
        "bg_color": "#1F2937",
        "fg_color": "#F3F4F6",
        "accent_color": ThemeColors.PRIMARY,
        "secondary_bg": "#374151"
    },
    "contrast": {
        "bg_color": "#000000",
        "fg_color": "#FFFFFF",
        "accent_color": "#FFD700",
        "secondary_bg": "#1A1A1A"
    }
}