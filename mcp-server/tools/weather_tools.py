"""Weather-related MCP tools."""
from typing import Any

from .config import logger, NWS_API_BASE
from .utils import make_nws_request


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    logger.debug(f"Formatting alert feature: {feature.get('id', 'unknown_id')}")
    props = feature["properties"]
    return f"""
    Event: {props.get('event', 'Unknown')}
    Area: {props.get('areaDesc', 'Unknown')}
    Severity: {props.get('severity', 'Unknown')}
    Description: {props.get('description', 'No description available')}
    Instructions: {props.get('instruction', 'No specific instructions provided')}
    """


async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)

    Returns:
        Formatted string containing alert information
    """
    logger.info(f"Getting weather alerts for state: {state}")
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        logger.warning(f"Unable to fetch alerts or no alerts found for state: {state}")
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        logger.info(f"No active alerts for state: {state}")
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    logger.info(f"Returning {len(alerts)} alerts for state: {state}")
    return "\n---\n".join(alerts)


async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location

    Returns:
        Formatted string containing forecast information
    """
    logger.info(f"Getting weather forecast for location: ({latitude}, {longitude})")
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        logger.warning(f"Unable to fetch forecast data for location: ({latitude}, {longitude})")
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        logger.warning(f"Unable to fetch detailed forecast for location: ({latitude}, {longitude})")
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
        {period['name']}:
        Temperature: {period['temperature']}°{period['temperatureUnit']}
        Wind: {period['windSpeed']} {period['windDirection']}
        Forecast: {period['detailedForecast']}
        """
        forecasts.append(forecast)

    logger.info(f"Returning forecast for location: ({latitude}, {longitude})")
    return "\n---\n".join(forecasts)
