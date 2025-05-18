"""
Global configuration settings for the application.
"""

# Feature flags
# Set to False because your current Azure OpenAI setup doesn't support Responses API
USE_RESPONSES_API = False

# But still run comparisons with fallback mode
ENABLE_API_COMPARISON = True

# Paths
RESPONSES_API_PERSISTENCE_PATH = "data/conversations.json"

# API Settings
AZURE_API_VERSION = "2024-02-01"  # Version that supports Responses API