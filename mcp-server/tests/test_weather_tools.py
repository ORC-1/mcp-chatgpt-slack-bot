"""Tests for Weather tools."""
import pytest
from unittest.mock import patch, AsyncMock

from tools.weather_tools import get_alerts, get_forecast


@pytest.mark.asyncio
async def test_get_alerts_success():
    """Test successful weather alerts retrieval."""
    mock_response = {
        "features": [
            {
                "properties": {
                    "event": "Flood Warning",
                    "areaDesc": "Test Area",
                    "severity": "Moderate",
                    "description": "Test description",
                    "instruction": "Test instructions"
                }
            }
        ]
    }
    
    with patch('tools.utils.make_nws_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        result = await get_alerts("CA")
        
        assert "Flood Warning" in result
        assert "Test Area" in result
        assert "Moderate" in result
        assert "Test description" in result
        assert "Test instructions" in result


@pytest.mark.asyncio
async def test_get_alerts_no_alerts():
    """Test when no alerts are found."""
    with patch('tools.utils.make_nws_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"features": []}
        result = await get_alerts("CA")
        
        assert "No active alerts for this state" in result


@pytest.mark.asyncio
async def test_get_forecast_success():
    """Test successful forecast retrieval."""
    mock_points_response = {
        "properties": {
            "forecast": "https://api.weather.gov/gridpoints/TEST/1,1/forecast"
        }
    }
    
    mock_forecast_response = {
        "properties": {
            "periods": [
                {
                    "name": "Tonight",
                    "temperature": 70,
                    "temperatureUnit": "F",
                    "windSpeed": "10 mph",
                    "windDirection": "NE",
                    "detailedForecast": "Clear skies"
                }
            ]
        }
    }
    
    with patch('tools.utils.make_nws_request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [mock_points_response, mock_forecast_response]
        result = await get_forecast(37.7749, -122.4194)
        
        assert "Tonight" in result
        assert "70°F" in result
        assert "10 mph" in result
        assert "NE" in result
        assert "Clear skies" in result


@pytest.mark.asyncio
async def test_get_forecast_points_failure():
    """Test forecast failure at points endpoint."""
    with patch('tools.utils.make_nws_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = None
        result = await get_forecast(37.7749, -122.4194)
        
        assert "Unable to fetch forecast data for this location" in result
