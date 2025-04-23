"""Tests for Slack tools."""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime

from tools.slack_tools import list_slack_channels, send_slack_message, get_channel_messages


@pytest.mark.asyncio
async def test_list_slack_channels_success(mock_slack_bot_token):
    """Test successful channel listing."""
    mock_response = {
        "ok": True,
        "channels": [
            {
                "id": "C1234",
                "name": "general",
                "topic": {"value": "Company-wide announcements"},
                "num_members": 50
            }
        ]
    }
    
    with patch('tools.utils.make_slack_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        result = await list_slack_channels(mock_slack_bot_token)
        
        assert "general" in result
        assert "C1234" in result
        assert "Company-wide announcements" in result
        assert "50" in result
        
        mock_request.assert_called_once_with(
            "conversations.list",
            mock_slack_bot_token,
            params={"limit": 100, "exclude_archived": True}
        )


@pytest.mark.asyncio
async def test_list_slack_channels_failure(mock_slack_bot_token):
    """Test channel listing failure."""
    with patch('tools.utils.make_slack_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"ok": False, "error": "invalid_auth"}
        result = await list_slack_channels(mock_slack_bot_token)
        
        assert "Failed to list channels" in result
        assert "invalid_auth" in result


@pytest.mark.asyncio
async def test_send_slack_message_success(mock_slack_bot_token):
    """Test successful message sending."""
    mock_response = {"ok": True, "ts": "1234.5678"}
    channel_id = "C1234"
    message = "Hello, world!"
    
    with patch('tools.utils.make_slack_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        result = await send_slack_message(mock_slack_bot_token, channel_id, message)
        
        assert "Message sent successfully" in result
        
        mock_request.assert_called_once_with(
            "chat.postMessage",
            mock_slack_bot_token,
            json_data={"channel": channel_id, "text": message},
            method="POST"
        )


@pytest.mark.asyncio
async def test_send_slack_message_failure(mock_slack_bot_token):
    """Test message sending failure."""
    with patch('tools.utils.make_slack_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"ok": False, "error": "channel_not_found"}
        result = await send_slack_message(mock_slack_bot_token, "invalid-channel", "test")
        
        assert "Failed to send message" in result
        assert "channel_not_found" in result


@pytest.mark.asyncio
async def test_get_channel_messages_success(mock_slack_bot_token):
    """Test successful message retrieval."""
    mock_messages_response = {
        "ok": True,
        "messages": [
            {
                "user": "U1234",
                "text": "Hello world",
                "ts": "1617235432.123456",
                "reactions": [
                    {"name": "thumbsup", "count": 3}
                ],
                "thread_ts": "1617235432.123456",
                "reply_count": 2
            }
        ]
    }
    
    mock_user_response = {
        "ok": True,
        "user": {
            "real_name": "John Doe",
            "name": "johndoe"
        }
    }
    
    with patch('tools.utils.make_slack_request', new_callable=AsyncMock) as mock_request:
        # Set up mock to return different responses for different API calls
        async def mock_api_call(*args, **kwargs):
            if args[0] == "conversations.history":
                return mock_messages_response
            elif args[0] == "users.info":
                return mock_user_response
            return None
        
        mock_request.side_effect = mock_api_call
        result = await get_channel_messages(mock_slack_bot_token, "C1234")
        
        assert "John Doe" in result
        assert "Hello world" in result
        assert ":thumbsup: (3)" in result
        assert "Thread: 2 replies" in result
        
        # Verify the API calls
        history_call = [call for call in mock_request.call_args_list if call[0][0] == "conversations.history"][0]
        assert history_call[1]["params"]["channel"] == "C1234"
        assert history_call[1]["params"]["limit"] == 50


@pytest.mark.asyncio
async def test_get_channel_messages_failure(mock_slack_bot_token):
    """Test message retrieval failure."""
    with patch('tools.utils.make_slack_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"ok": False, "error": "channel_not_found"}
        result = await get_channel_messages(mock_slack_bot_token, "invalid-channel")
        
        assert "Failed to get channel messages" in result
        assert "channel_not_found" in result


@pytest.mark.asyncio
async def test_get_channel_messages_no_messages(mock_slack_bot_token):
    """Test when no messages are found."""
    with patch('tools.utils.make_slack_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"ok": True, "messages": []}
        result = await get_channel_messages(mock_slack_bot_token, "C1234")
        
        assert "No messages found in the channel" in result
