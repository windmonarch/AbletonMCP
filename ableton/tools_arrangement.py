# ableton/tools_arrangement.py
# MCP tools for Arrangement View operations.
import json
from typing import Dict, List, Union
from mcp.server.fastmcp import FastMCP, Context
from .connection import get_ableton_connection


def register(mcp: FastMCP):
    """Register all Arrangement View tools onto the FastMCP instance."""

    @mcp.tool()
    def get_arrangement_clips(ctx: Context, track_index: int) -> str:
        """
        Get all clips currently placed in the Arrangement View for a track.

        Parameters:
        - track_index: The index of the track to inspect
        """
        try:
            result = get_ableton_connection().send_command("get_arrangement_clips", {
                "track_index": track_index})
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting arrangement clips: {str(e)}"

    @mcp.tool()
    def add_notes_to_arrangement_clip(
        ctx: Context,
        track_index: int,
        clip_index: int,
        notes: List[Dict[str, Union[int, float, bool]]]
    ) -> str:
        """
        Add MIDI notes to a clip in the Arrangement View.

        Parameters:
        - track_index: The index of the track containing the clip
        - clip_index: The position of the clip in the track's arrangement clip list (0 = first clip)
        - notes: List of note dicts — each needs: pitch (MIDI 0-127), start_time (beats from clip
                 start), duration (beats), velocity (0-127), mute (bool, optional)
        """
        try:
            result = get_ableton_connection().send_command("add_notes_to_arrangement_clip", {
                "track_index": track_index,
                "clip_index": clip_index,
                "notes": notes,
            })
            return (f"Added {result.get('note_count', len(notes))} notes to arrangement clip "
                    f"{clip_index} on track {track_index}")
        except Exception as e:
            return f"Error adding notes to arrangement clip: {str(e)}"

    @mcp.tool()
    def set_arrangement_clip_name(
        ctx: Context,
        track_index: int,
        clip_index: int,
        name: str
    ) -> str:
        """
        Rename a clip in the Arrangement View.

        Parameters:
        - track_index: The index of the track containing the clip
        - clip_index: The position of the clip in the track's arrangement clip list (0 = first clip)
        - name: The new name for the clip
        """
        try:
            result = get_ableton_connection().send_command("set_arrangement_clip_name", {
                "track_index": track_index,
                "clip_index": clip_index,
                "name": name,
            })
            return (f"Renamed arrangement clip {clip_index} on track {track_index} "
                    f"to '{result.get('name', name)}'")
        except Exception as e:
            return f"Error setting arrangement clip name: {str(e)}"
