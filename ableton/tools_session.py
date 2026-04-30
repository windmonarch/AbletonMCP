# ableton/tools_session.py
# MCP tools for Session View operations (clips, playback, tracks).
import json
from typing import Dict, List, Union
from mcp.server.fastmcp import FastMCP, Context
from .connection import get_ableton_connection


def register(mcp: FastMCP):
    """Register all Session View tools onto the FastMCP instance."""

    @mcp.tool()
    def get_session_info(ctx: Context) -> str:
        """Get detailed information about the current Ableton session."""
        try:
            result = get_ableton_connection().send_command("get_session_info")
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting session info: {str(e)}"

    @mcp.tool()
    def get_track_info(ctx: Context, track_index: int) -> str:
        """
        Get detailed information about a specific track in Ableton.

        Parameters:
        - track_index: The index of the track to get information about
        """
        try:
            result = get_ableton_connection().send_command("get_track_info", {"track_index": track_index})
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting track info: {str(e)}"

    @mcp.tool()
    def create_midi_track(ctx: Context, index: int = -1) -> str:
        """
        Create a new MIDI track in the Ableton session.

        Parameters:
        - index: The index to insert the track at (-1 = end of list)
        """
        try:
            result = get_ableton_connection().send_command("create_midi_track", {"index": index})
            return f"Created new MIDI track: {result.get('name', 'unknown')}"
        except Exception as e:
            return f"Error creating MIDI track: {str(e)}"

    @mcp.tool()
    def set_track_name(ctx: Context, track_index: int, name: str) -> str:
        """
        Set the name of a track.

        Parameters:
        - track_index: The index of the track to rename
        - name: The new name for the track
        """
        try:
            result = get_ableton_connection().send_command("set_track_name", {
                "track_index": track_index, "name": name})
            return f"Renamed track to: {result.get('name', name)}"
        except Exception as e:
            return f"Error setting track name: {str(e)}"

    @mcp.tool()
    def create_clip(ctx: Context, track_index: int, clip_index: int, length: float = 4.0) -> str:
        """
        Create a new MIDI clip in the specified track and clip slot (Session View).

        Parameters:
        - track_index: The index of the track to create the clip in
        - clip_index: The index of the clip slot to create the clip in
        - length: The length of the clip in beats (default: 4.0)
        """
        try:
            get_ableton_connection().send_command("create_clip", {
                "track_index": track_index, "clip_index": clip_index, "length": length})
            return f"Created new clip at track {track_index}, slot {clip_index} with length {length} beats"
        except Exception as e:
            return f"Error creating clip: {str(e)}"

    @mcp.tool()
    def add_notes_to_clip(
        ctx: Context,
        track_index: int,
        clip_index: int,
        notes: List[Dict[str, Union[int, float, bool]]]
    ) -> str:
        """
        Add MIDI notes to a Session View clip.

        Parameters:
        - track_index: The index of the track containing the clip
        - clip_index: The index of the clip slot containing the clip
        - notes: List of note dicts with pitch, start_time, duration, velocity, mute
        """
        try:
            get_ableton_connection().send_command("add_notes_to_clip", {
                "track_index": track_index, "clip_index": clip_index, "notes": notes})
            return f"Added {len(notes)} notes to clip at track {track_index}, slot {clip_index}"
        except Exception as e:
            return f"Error adding notes to clip: {str(e)}"

    @mcp.tool()
    def set_clip_name(ctx: Context, track_index: int, clip_index: int, name: str) -> str:
        """
        Set the name of a Session View clip.

        Parameters:
        - track_index: The index of the track containing the clip
        - clip_index: The index of the clip slot containing the clip
        - name: The new name for the clip
        """
        try:
            get_ableton_connection().send_command("set_clip_name", {
                "track_index": track_index, "clip_index": clip_index, "name": name})
            return f"Renamed clip at track {track_index}, slot {clip_index} to '{name}'"
        except Exception as e:
            return f"Error setting clip name: {str(e)}"

    @mcp.tool()
    def set_tempo(ctx: Context, tempo: float) -> str:
        """
        Set the tempo of the Ableton session.

        Parameters:
        - tempo: The new tempo in BPM
        """
        try:
            get_ableton_connection().send_command("set_tempo", {"tempo": tempo})
            return f"Set tempo to {tempo} BPM"
        except Exception as e:
            return f"Error setting tempo: {str(e)}"

    @mcp.tool()
    def fire_clip(ctx: Context, track_index: int, clip_index: int) -> str:
        """
        Start playing a Session View clip.

        Parameters:
        - track_index: The index of the track containing the clip
        - clip_index: The index of the clip slot containing the clip
        """
        try:
            get_ableton_connection().send_command("fire_clip", {
                "track_index": track_index, "clip_index": clip_index})
            return f"Started playing clip at track {track_index}, slot {clip_index}"
        except Exception as e:
            return f"Error firing clip: {str(e)}"

    @mcp.tool()
    def stop_clip(ctx: Context, track_index: int, clip_index: int) -> str:
        """
        Stop playing a Session View clip.

        Parameters:
        - track_index: The index of the track containing the clip
        - clip_index: The index of the clip slot containing the clip
        """
        try:
            get_ableton_connection().send_command("stop_clip", {
                "track_index": track_index, "clip_index": clip_index})
            return f"Stopped clip at track {track_index}, slot {clip_index}"
        except Exception as e:
            return f"Error stopping clip: {str(e)}"

    @mcp.tool()
    def start_playback(ctx: Context) -> str:
        """Start playing the Ableton session."""
        try:
            get_ableton_connection().send_command("start_playback")
            return "Started playback"
        except Exception as e:
            return f"Error starting playback: {str(e)}"

    @mcp.tool()
    def stop_playback(ctx: Context) -> str:
        """Stop playing the Ableton session."""
        try:
            get_ableton_connection().send_command("stop_playback")
            return "Stopped playback"
        except Exception as e:
            return f"Error stopping playback: {str(e)}"
