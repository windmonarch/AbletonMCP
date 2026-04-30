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

    @mcp.tool()
    def get_cue_points(ctx: Context) -> str:
        """Get all cue points in the current Ableton session."""
        try:
            result = get_ableton_connection().send_command("get_cue_points")
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting cue points: {str(e)}"

    @mcp.tool()
    def jump_to_cue(ctx: Context, direction: str = "next") -> str:
        """
        Jump to the next or previous cue point.

        Parameters:
        - direction: 'next' or 'prev'
        """
        try:
            get_ableton_connection().send_command("jump_to_cue", {"direction": direction})
            return f"Jumped to {direction} cue point"
        except Exception as e:
            return f"Error jumping to cue: {str(e)}"

    @mcp.tool()
    def get_current_song_time(ctx: Context) -> str:
        """Get the current playhead position in beats."""
        try:
            result = get_ableton_connection().send_command("get_current_song_time")
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting current song time: {str(e)}"

    @mcp.tool()
    def get_clip_notes(ctx: Context, track_index: int, clip_index: int) -> str:
        """
        Get all MIDI notes in an Arrangement View clip.

        Parameters:
        - track_index: The index of the track containing the clip
        - clip_index: The position of the clip in the track's arrangement clip list (0 = first clip)
        """
        try:
            result = get_ableton_connection().send_command("get_clip_notes", {
                "track_index": track_index,
                "clip_index": clip_index,
            })
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting clip notes: {str(e)}"

    @mcp.tool()
    def remove_notes_from_clip(ctx: Context, track_index: int, clip_index: int) -> str:
        """
        Remove all MIDI notes from an Arrangement View clip.

        Parameters:
        - track_index: The index of the track containing the clip
        - clip_index: The position of the clip in the track's arrangement clip list (0 = first clip)
        """
        try:
            get_ableton_connection().send_command("remove_notes_from_clip", {
                "track_index": track_index,
                "clip_index": clip_index,
            })
            return f"Removed all notes from arrangement clip {clip_index} on track {track_index}"
        except Exception as e:
            return f"Error removing notes from clip: {str(e)}"

    @mcp.tool()
    def set_clip_color(ctx: Context, track_index: int, clip_index: int, color: int) -> str:
        """
        Set the color of an Arrangement View clip.

        Parameters:
        - track_index: The index of the track containing the clip
        - clip_index: The position of the clip in the track's arrangement clip list (0 = first clip)
        - color: RGB color as a packed integer (e.g. 0xFF0000 for red)
        """
        try:
            result = get_ableton_connection().send_command("set_clip_color", {
                "track_index": track_index,
                "clip_index": clip_index,
                "color": color,
            })
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error setting clip color: {str(e)}"

    @mcp.tool()
    def set_clip_pitch(
        ctx: Context,
        track_index: int,
        clip_index: int,
        pitch_coarse: int,
        pitch_fine: float = 0.0
    ) -> str:
        """
        Set the pitch transpose of an Arrangement View clip.

        Parameters:
        - track_index: The index of the track containing the clip
        - clip_index: The position of the clip in the track's arrangement clip list (0 = first clip)
        - pitch_coarse: Semitone transpose (-48 to 48)
        - pitch_fine: Cent fine-tune (-50.0 to 50.0, default 0.0)
        """
        try:
            result = get_ableton_connection().send_command("set_clip_pitch", {
                "track_index": track_index,
                "clip_index": clip_index,
                "pitch_coarse": pitch_coarse,
                "pitch_fine": pitch_fine,
            })
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error setting clip pitch: {str(e)}"

    @mcp.tool()
    def set_clip_gain(
        ctx: Context,
        track_index: int,
        clip_index: int,
        gain: float
    ) -> str:
        """
        Set the gain of an audio clip in the Arrangement View.

        Parameters:
        - track_index: The index of the track containing the clip
        - clip_index: The position of the clip in the track's arrangement clip list (0 = first clip)
        - gain: Gain value from 0.0 to 1.0 (audio clips only)
        """
        try:
            result = get_ableton_connection().send_command("set_clip_gain", {
                "track_index": track_index,
                "clip_index": clip_index,
                "gain": gain,
            })
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error setting clip gain: {str(e)}"

    @mcp.tool()
    def set_clip_markers(
        ctx: Context,
        track_index: int,
        clip_index: int,
        start_marker: float,
        end_marker: float
    ) -> str:
        """
        Set the start and end markers of an Arrangement View clip.

        Parameters:
        - track_index: The index of the track containing the clip
        - clip_index: The position of the clip in the track's arrangement clip list (0 = first clip)
        - start_marker: Start marker position in beats (within the clip)
        - end_marker: End marker position in beats (within the clip)
        """
        try:
            result = get_ableton_connection().send_command("set_clip_markers", {
                "track_index": track_index,
                "clip_index": clip_index,
                "start_marker": start_marker,
                "end_marker": end_marker,
            })
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error setting clip markers: {str(e)}"
