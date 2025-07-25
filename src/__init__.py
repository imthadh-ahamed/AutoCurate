# AutoCurate Package Initialization
"""
AutoCurate - AI-Powered Personalized Knowledge Feed

A smart agent-based system that scrapes content from websites,
processes it with AI, and delivers personalized summaries to users.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Package metadata
__title__ = "AutoCurate"
__description__ = "AI-Powered Personalized Knowledge Feed from Web Sources"
__url__ = "https://github.com/your-username/autocurate"
__license__ = "MIT"

# Import main components for easy access
from .config.settings import settings
from .core.database import get_db, init_database

# Version info
VERSION = __version__
VERSION_INFO = tuple(map(int, __version__.split('.')))

# Export key components
__all__ = [
    'settings',
    'get_db', 
    'init_database',
    'VERSION',
    'VERSION_INFO',
]
