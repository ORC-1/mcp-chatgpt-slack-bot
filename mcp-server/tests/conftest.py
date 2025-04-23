"""Pytest configuration and fixtures."""
import pytest


@pytest.fixture
def mock_slack_bot_token():
    """Return a mock Slack bot token."""
    return "xoxb-mock-token"
