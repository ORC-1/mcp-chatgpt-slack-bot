"""Utility functions for MCP tools."""
from typing import Any

import httpx

from .config import logger, NWS_API_BASE, SLACK_API_BASE, USER_AGENT


async def make_slack_request(endpoint: str, bot_token: str, params: dict = None, json_data: dict = None, method: str = "GET") -> dict[str, Any] | None:
    """Make a request to the Slack API with proper error handling."""
    logger.debug(f"Making {method} request to Slack API: {endpoint}")
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    url = f"{SLACK_API_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params, timeout=30.0)
            else:  # POST
                response = await client.post(url, headers=headers, json=json_data, timeout=30.0)
            response.raise_for_status()
            logger.debug(f"Successfully received response from Slack API: {endpoint}")
            return response.json()
        except Exception as e:
            logger.error(f"Error making request to Slack API: {endpoint} - Error: {str(e)}")
            return None


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    logger.debug(f"Making request to NWS API: {url}")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            logger.debug(f"Successfully received response from NWS API: {url}")
            return response.json()
        except Exception as e:
            logger.error(f"Error making request to NWS API: {url} - Error: {str(e)}")
            return None
