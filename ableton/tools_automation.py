# ableton/tools_automation.py
# MCP tools for clip automation envelope operations.
import json
from mcp.server.fastmcp import FastMCP, Context
from .connection import get_ableton_connection


def register(mcp: FastMCP):
    """Register all automation envelope tools onto the FastMCP instance."""

    @mcp.tool()
    def get_clip_envelope(
        ctx: Context,
        track_index: int,
        clip_index: int,
        device_index: int,
        param_index: int
    ) -> str:
        """
        Read the automation envelope for a device parameter in an Arrangement View clip.
        Use get_device_parameters to find device_index and param_index.

        Parameters:
        - track_index: The index of the track
        - clip_index: The position of the clip in the arrangement clip list (0 = first)
        - device_index: The index of the device on the track
        - param_index: The index of the parameter within the device
        """
        try:
            result = get_ableton_connection().send_command("get_clip_envelope", {
                "track_index": track_index,
                "clip_index": clip_index,
                "device_index": device_index,
                "param_index": param_index,
            })
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting clip envelope: {str(e)}"

    @mcp.tool()
    def set_clip_envelope_point(
        ctx: Context,
        track_index: int,
        clip_index: int,
        device_index: int,
        param_index: int,
        time: float,
        value: float,
        duration: float = 0.0
    ) -> str:
        """
        Insert an automation point into a clip envelope for a device parameter.

        IMPORTANT: The automation envelope for the parameter must already exist in the clip.
        If it does not, an error is returned with instructions. To initialise it manually:
        in Ableton, right-click the parameter, choose 'Show Automation in Arrangement Clip',
        draw at least one breakpoint, then call this tool again.

        Parameters:
        - track_index: The index of the track
        - clip_index: The position of the clip in the arrangement clip list (0 = first)
        - device_index: The index of the device on the track
        - param_index: The index of the parameter within the device
        - time: Position in beats within the clip (0.0 = clip start)
        - value: The parameter value to set at this point
        - duration: Duration of the step in beats (0.0 = instant, default)
        """
        try:
            result = get_ableton_connection().send_command("set_clip_envelope_point", {
                "track_index": track_index,
                "clip_index": clip_index,
                "device_index": device_index,
                "param_index": param_index,
                "time": time,
                "value": value,
                "duration": duration,
            })
            return f"Automation point inserted at beat {time} with value {value}"
        except Exception as e:
            return f"Error setting clip envelope point: {str(e)}"

    @mcp.tool()
    def clear_clip_envelope(
        ctx: Context,
        track_index: int,
        clip_index: int,
        device_index: int,
        param_index: int
    ) -> str:
        """
        Clear the automation envelope for a specific device parameter in a clip.
        Use clear_clip_envelopes to clear all envelopes at once.

        Parameters:
        - track_index: The index of the track
        - clip_index: The position of the clip in the arrangement clip list (0 = first)
        - device_index: The index of the device on the track
        - param_index: The index of the parameter within the device
        """
        try:
            result = get_ableton_connection().send_command("clear_clip_envelope", {
                "track_index": track_index,
                "clip_index": clip_index,
                "device_index": device_index,
                "param_index": param_index,
            })
            return f"Cleared automation envelope for '{result['param_name']}'"
        except Exception as e:
            return f"Error clearing clip envelope: {str(e)}"
