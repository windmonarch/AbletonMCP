# ableton/tools_devices.py
# MCP tools for device parameter and drum pad operations.
import json
from typing import List, Optional
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
    def get_rack_devices(
        ctx: Context,
        track_index: int,
        device_index: int,
        depth: int = 1,
        include_parameters: bool = True,
        track_type: str = "track",
        path: Optional[List[int]] = None,
    ) -> str:
        """
        Get all devices nested inside a rack's chains, including their parameters.
        Use this to inspect devices inside Audio Effect Racks, Instrument Racks, etc.

        Every device in the output carries a `path` that can be passed straight to
        get_device_parameters_at_path / set_device_parameter_at_path.

        Parameters:
        - track_index: The index of the track (or return track when track_type="return")
        - device_index: The index of the rack device on the track
        - depth: How many rack levels to descend (default 1 = the rack's own chains only).
          Use 2+ to reach racks nested inside racks. Racks at the depth limit report
          `chain_count` instead of `chains`.
        - include_parameters: Set False to get just the device tree (much smaller output)
        - track_type: "track" (default), "return" or "master" (track_index ignored for master)
        - path: Optional device path of a nested rack to start from; overrides device_index
        """
        try:
            params = {
                "track_index": track_index,
                "device_index": device_index,
                "depth": depth,
                "include_parameters": include_parameters,
                "track_type": track_type,
            }
            if path:
                params["path"] = path
            result = get_ableton_connection().send_command("get_rack_devices", params)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting rack devices: {str(e)}"

    @mcp.tool()
    def get_device_parameters_at_path(
        ctx: Context,
        track_index: int,
        path: List[int],
        track_type: str = "track",
    ) -> str:
        """
        Get all parameters of a device anywhere in a track's device tree, including
        devices nested inside racks (and racks inside racks).

        A device path alternates device and chain indices, starting and ending on a device:
        - [2]          -> the track's 3rd top-level device
        - [0, 4, 0]    -> rack at device 0, its chain 4, first device in that chain
        - [0, 4, 0, 0, 1] -> one level deeper (chain 0 of that nested rack, device 1)
        get_rack_devices returns the `path` of every nested device.

        Each parameter includes `value` (raw), `display_value` (as Live shows it, e.g.
        "4.00 : 1", "50.0 ms", "6.00 kHz"), min/max and their display strings.

        Parameters:
        - track_index: The index of the track (or return track when track_type="return")
        - path: Device path, e.g. [0, 4, 0]
        - track_type: "track" (default), "return" or "master" (track_index ignored for master)
        """
        try:
            result = get_ableton_connection().send_command("get_device_parameters_at_path", {
                "track_index": track_index,
                "path": path,
                "track_type": track_type,
            })
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting device parameters at path: {str(e)}"

    @mcp.tool()
    def set_device_parameter_at_path(
        ctx: Context,
        track_index: int,
        path: List[int],
        value: float,
        param_index: Optional[int] = None,
        param_name: Optional[str] = None,
        track_type: str = "track",
    ) -> str:
        """
        Set a parameter on a device anywhere in a track's device tree, including
        devices nested inside racks. See get_device_parameters_at_path for path format.

        Identify the parameter by param_name (case-insensitive exact match, safer) or
        param_index. If both are given they must refer to the same parameter. An unknown
        or ambiguous name is an error, never a guess.

        `value` is the raw parameter value within the parameter's min/max (often 0-1),
        not the display string. The response shows the previous and new display values
        so you can confirm the result (e.g. "4.00 : 1").

        Parameters:
        - track_index: The index of the track (or return track when track_type="return")
        - path: Device path, e.g. [0, 4, 0]
        - value: The new raw value (must be within the parameter's min/max)
        - param_index: The index of the parameter
        - param_name: The name of the parameter, e.g. "Ratio"
        - track_type: "track" (default), "return" or "master" (track_index ignored for master)
        """
        if param_index is None and param_name is None:
            return "Error setting device parameter at path: provide param_index or param_name"
        try:
            params = {
                "track_index": track_index,
                "path": path,
                "value": value,
                "track_type": track_type,
            }
            if param_index is not None:
                params["param_index"] = param_index
            if param_name is not None:
                params["param_name"] = param_name
            result = get_ableton_connection().send_command("set_device_parameter_at_path", params)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error setting device parameter at path: {str(e)}"

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
