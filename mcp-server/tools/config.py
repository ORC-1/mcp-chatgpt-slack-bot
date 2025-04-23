"""Configuration module for MCP tools."""
import logging
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs.txt'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('mcp_tools')

# API Constants
NWS_API_BASE = "https://api.weather.gov"
SLACK_API_BASE = "https://slack.com/api"
USER_AGENT = "weather-app/1.0"
