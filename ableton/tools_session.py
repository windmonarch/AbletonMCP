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

    @mcp.tool()
    def undo(ctx: Context) -> str:
        """Undo the last action in Ableton."""
        try:
            get_ableton_connection().send_command("undo")
            return "Undone"
        except Exception as e:
            return f"Error undoing: {str(e)}"

    @mcp.tool()
    def redo(ctx: Context) -> str:
        """Redo the last undone action in Ableton."""
        try:
            get_ableton_connection().send_command("redo")
            return "Redone"
        except Exception as e:
            return f"Error redoing: {str(e)}"

    @mcp.tool()
    def create_audio_track(ctx: Context, index: int = -1) -> str:
        """
        Create a new audio track in the Ableton session.

        Parameters:
        - index: The index to insert the track at (-1 = end of list)
        """
        try:
            result = get_ableton_connection().send_command("create_audio_track", {"index": index})
            return f"Created new audio track: {result.get('name', 'unknown')}"
        except Exception as e:
            return f"Error creating audio track: {str(e)}"

    @mcp.tool()
    def create_return_track(ctx: Context) -> str:
        """Create a new return track in the Ableton session (always appended at the end)."""
        try:
            result = get_ableton_connection().send_command("create_return_track")
            return f"Created new return track: {result.get('name', 'unknown')}"
        except Exception as e:
            return f"Error creating return track: {str(e)}"

    @mcp.tool()
    def delete_track(ctx: Context, track_index: int) -> str:
        """
        Delete a track from the Ableton session.

        Parameters:
        - track_index: The index of the track to delete (cannot delete return or master tracks)
        """
        try:
            result = get_ableton_connection().send_command("delete_track", {
                "track_index": track_index})
            return f"Deleted track {track_index}. Session now has {result.get('track_count')} tracks."
        except Exception as e:
            return f"Error deleting track: {str(e)}"

    @mcp.tool()
    def duplicate_track(ctx: Context, track_index: int) -> str:
        """
        Duplicate a track in the Ableton session.

        Parameters:
        - track_index: The index of the track to duplicate
        """
        try:
            result = get_ableton_connection().send_command("duplicate_track", {
                "track_index": track_index})
            return (f"Duplicated track {track_index}. "
                    f"New track '{result.get('name')}' at index {result.get('new_index')}.")
        except Exception as e:
            return f"Error duplicating track: {str(e)}"

    @mcp.tool()
    def set_track_color(ctx: Context, track_index: int, color: int) -> str:
        """
        Set the color of a track.

        Parameters:
        - track_index: The index of the track
        - color: RGB color as a packed integer (e.g. 0xFF0000 for red)
        """
        try:
            result = get_ableton_connection().send_command("set_track_color", {
                "track_index": track_index, "color": color})
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error setting track color: {str(e)}"

    @mcp.tool()
    def set_track_mute(ctx: Context, track_index: int, mute: bool) -> str:
        """
        Mute or unmute a track.

        Parameters:
        - track_index: The index of the track
        - mute: True to mute, False to unmute
        """
        try:
            result = get_ableton_connection().send_command("set_track_mute", {
                "track_index": track_index, "mute": mute})
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error setting track mute: {str(e)}"

    @mcp.tool()
    def set_track_solo(ctx: Context, track_index: int, solo: bool) -> str:
        """
        Solo or unsolo a track.

        Parameters:
        - track_index: The index of the track
        - solo: True to solo, False to unsolo
        """
        try:
            result = get_ableton_connection().send_command("set_track_solo", {
                "track_index": track_index, "solo": solo})
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error setting track solo: {str(e)}"

    @mcp.tool()
    def set_track_arm(ctx: Context, track_index: int, arm: bool) -> str:
        """
        Arm or disarm a track for recording. Only works on MIDI and audio tracks.

        Parameters:
        - track_index: The index of the track
        - arm: True to arm, False to disarm
        """
        try:
            result = get_ableton_connection().send_command("set_track_arm", {
                "track_index": track_index, "arm": arm})
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error setting track arm: {str(e)}"

    @mcp.tool()
    def set_track_volume(ctx: Context, track_index: int, volume: float) -> str:
        """
        Set the volume of a track.

        Parameters:
        - track_index: The index of the track
        - volume: Volume from 0.0 to 1.0 (0.85 = unity / 0 dB)
        """
        try:
            result = get_ableton_connection().send_command("set_track_volume", {
                "track_index": track_index, "volume": volume})
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error setting track volume: {str(e)}"

    @mcp.tool()
    def set_track_pan(ctx: Context, track_index: int, panning: float) -> str:
        """
        Set the panning of a track.

        Parameters:
        - track_index: The index of the track
        - panning: Panning from -1.0 (full left) to 1.0 (full right), 0.0 = center
        """
        try:
            result = get_ableton_connection().send_command("set_track_pan", {
                "track_index": track_index, "panning": panning})
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error setting track pan: {str(e)}"

    @mcp.tool()
    def get_track_sends(ctx: Context, track_index: int) -> str:
        """
        Get all send levels for a track.

        Parameters:
        - track_index: The index of the track
        """
        try:
            result = get_ableton_connection().send_command("get_track_sends", {
                "track_index": track_index})
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting track sends: {str(e)}"

    @mcp.tool()
    def set_track_send(
        ctx: Context,
        track_index: int,
        send_index: int,
        value: float
    ) -> str:
        """
        Set the send level for a track to a return track.

        Parameters:
        - track_index: The index of the track
        - send_index: The index of the send (corresponds to return track order)
        - value: Send level from 0.0 to 1.0
        """
        try:
            result = get_ableton_connection().send_command("set_track_send", {
                "track_index": track_index, "send_index": send_index, "value": value})
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error setting track send: {str(e)}"

    @mcp.tool()
    def delete_device(ctx: Context, track_index: int, device_index: int) -> str:
        """
        Delete a device from a track's device chain.

        Parameters:
        - track_index: The index of the track
        - device_index: The index of the device to delete
        """
        try:
            result = get_ableton_connection().send_command("delete_device", {
                "track_index": track_index, "device_index": device_index})
            return f"Deleted device. Track now has {result.get('device_count')} device(s)."
        except Exception as e:
            return f"Error deleting device: {str(e)}"

    @mcp.tool()
    def set_time_signature(ctx: Context, numerator: int, denominator: int) -> str:
        """
        Set the time signature of the Ableton session.

        Parameters:
        - numerator: The top number (beats per bar, e.g. 3 for 3/4)
        - denominator: The bottom number (beat value, e.g. 4 for quarter note, 8 for eighth note)
        """
        try:
            result = get_ableton_connection().send_command("set_time_signature", {
                "numerator": numerator, "denominator": denominator})
            return f"Time signature set to {result['signature_numerator']}/{result['signature_denominator']}"
        except Exception as e:
            return f"Error setting time signature: {str(e)}"

    @mcp.tool()
    def jump_to_time(ctx: Context, time: float) -> str:
        """
        Move the playhead to a specific position in the arrangement.

        Parameters:
        - time: Position in beats from the start of the arrangement (e.g. 4.0 = bar 2 in 4/4)
        """
        try:
            result = get_ableton_connection().send_command("jump_to_time", {"time": time})
            return f"Playhead moved to {result['current_song_time']} beats"
        except Exception as e:
            return f"Error jumping to time: {str(e)}"
