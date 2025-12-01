"""
Configuration settings for Substack Subscriber Analytics.
"""
from pathlib import Path

# Base directory for all user-uploaded data
DATA_DIR = Path(".data")

# Required files for a valid Substack export
REQUIRED_FILES = ["posts.csv"]

# Required file patterns (glob patterns)
REQUIRED_PATTERNS = ["email_list*.csv"]

# Required directories
REQUIRED_DIRS = ["posts"]

# Optional files that enhance the analysis
OPTIONAL_FILES = ["subscriber_details.csv"]

# Manifest filename for dataset metadata
MANIFEST_FILE = "manifest.json"

# App metadata
APP_NAME = "Substack Subscriber Analytics"
APP_VERSION = "1.0.0"
