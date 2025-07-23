from tkinter import ttk
from typing import Dict, Any
import logging
import json
from datetime import datetime, timedelta
from dateutil import parser
from constants import COLORS

def configure_styles(style: ttk.Style):
    """Configure ttk styles for the application"""
    try:
        # Configure main styles
        style.configure(
            'Message.TFrame',
            background=COLORS['background']
        )
        
        style.configure(
            'Message.TLabel',
            background=COLORS['background'],
            foreground=COLORS['text'],
            font=('Segoe UI', 10)
        )
        
        # Configure button styles
        style.configure(
            'Accent.TButton',
            padding=5,
            relief='flat',
            background=COLORS['primary']
        )
        
        # Configure entry styles
        style.configure(
            'App.TEntry',
            padding=5,
            relief='flat'
        )
        
    except Exception as e:
        logging.error(f"Error configuring styles: {e}")

def format_date(date_str: str) -> str:
    """Format date string to a standardized format"""
    try:
        date_obj = parser.parse(date_str)
        return date_obj.strftime("%B %d, %Y")
    except Exception as e:
        logging.error(f"Error formatting date: {e}")
        return date_str

def parse_relative_date(date_expression: str) -> str:
    """Parse relative date expressions (e.g., 'next week', 'tomorrow')"""
    try:
        today = datetime.now()
        expression = date_expression.lower()
        
        if 'tomorrow' in expression:
            result = today + timedelta(days=1)
        elif 'next week' in expression:
            result = today + timedelta(weeks=1)
        elif 'next month' in expression:
            if today.month == 12:
                result = today.replace(year=today.year + 1, month=1)
            else:
                result = today.replace(month=today.month + 1)
        else:
            result = today
            
        return result.strftime("%B %d, %Y")
        
    except Exception as e:
        logging.error(f"Error parsing relative date: {e}")
        return None

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Safely load JSON file with error handling"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"File not found: {filepath}")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in file: {filepath}")
        return {}
    except Exception as e:
        logging.error(f"Error loading JSON file: {e}")
        return {}

def save_json_file(data: Dict[str, Any], filepath: str) -> bool:
    """Safely save JSON file with error handling"""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON file: {e}")
        return False

def format_task_info(task_info: Dict[str, Any]) -> str:
    """Format task information for display"""
    try:
        parts = [f"Task: {task_info['task_name']}"]
        
        if task_info.get('date'):
            parts.append(f"Scheduled: {task_info['date']}")
            
        if task_info.get('status'):
            parts.append(f"Status: {task_info['status']}")
            
        return " | ".join(parts)
        
    except Exception as e:
        logging.error(f"Error formatting task info: {e}")
        return str(task_info)

def validate_task_data(task_data: Dict[str, Any]) -> bool:
    """Validate task data structure"""
    required_fields = ['task_name']
    try:
        return all(field in task_data for field in required_fields)
    except Exception as e:
        logging.error(f"Error validating task data: {e}")
        return False

def setup_logging():
    """Configure logging settings"""
    try:
        logging.basicConfig(
            filename='visa4d.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Also log critical errors to console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)
        
    except Exception as e:
        print(f"Error setting up logging: {e}")

def clean_text(text: str) -> str:
    """Clean and normalize text input"""
    try:
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Convert to lowercase
        text = text.lower()
        return text
    except Exception as e:
        logging.error(f"Error cleaning text: {e}")
        return text

def format_status(status: str) -> str:
    """Format status string with emoji"""
    status_emojis = {
        'complete': '✅',
        'in progress': '🔄',
        'on hold': '⏸️'
    }
    try:
        status_lower = status.lower()
        emoji = status_emojis.get(status_lower, '❓')
        return f"{emoji} {status}"
    except Exception as e:
        logging.error(f"Error formatting status: {e}")
        return status