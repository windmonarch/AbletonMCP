# ableton/tools_devices.py
# MCP tools for device parameter and drum pad operations.
import json
from mcp.server.fastmcp import FastMCP, Context
from .connection import get_ableton_connection


def register(mcp: FastMCP):
    """Register all device tools onto the FastMCP instance."""

    @mcp.tool()
    def get_device_parameters(ctx: Context, track_index: int, device_index: int) -> str:
        """
        Get all parameters for a device on a track.

        Parameters:
        - track_index: The index of the track
        - device_index: The index of the device in the track's device chain
        """
        try:
            result = get_ableton_connection().send_command("get_device_parameters", {
                "track_index": track_index,
                "device_index": device_index,
            })
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting device parameters: {str(e)}"

    @mcp.tool()
    def set_device_parameter(
        ctx: Context,
        track_index: int,
        device_index: int,
        param_index: int,
        value: float
    ) -> str:
        """
        Set a parameter value on a device.

        Parameters:
        - track_index: The index of the track
        - device_index: The index of the device in the track's device chain
        - param_index: The index of the parameter (use get_device_parameters to find indices)
        - value: The new value (must be within the parameter's min/max range)
        """
        try:
            result = get_ableton_connection().send_command("set_device_parameter", {
                "track_index": track_index,
                "device_index": device_index,
                "param_index": param_index,
                "value": value,
            })
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error setting device parameter: {str(e)}"

    @mcp.tool()
    def get_rack_devices(ctx: Context, track_index: int, device_index: int) -> str:
        """
        Get all devices nested inside a rack's chains, including their parameters.
        Use this to inspect devices inside Audio Effect Racks, Instrument Racks, etc.

        Parameters:
        - track_index: The index of the track
        - device_index: The index of the rack device on the track
        """
        try:
            result = get_ableton_connection().send_command("get_rack_devices", {
                "track_index": track_index,
                "device_index": device_index,
            })
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting rack devices: {str(e)}"

    @mcp.tool()
    def get_drum_pads(ctx: Context, track_index: int, device_index: int) -> str:
        """
        Get all drum pads for a Drum Rack device.

        Parameters:
        - track_index: The index of the track
        - device_index: The index of the Drum Rack device in the track's device chain
        """
        try:
            result = get_ableton_connection().send_command("get_drum_pads", {
                "track_index": track_index,
                "device_index": device_index,
            })
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting drum pads: {str(e)}"
