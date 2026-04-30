# AbletonMCPArrangement/commands_arrangement.py
# Handlers for Arrangement View commands.
# NOTE: create_arrangement_clip and delete_arrangement_clip are NOT implemented.
# The Live ControlSurface Python API exposes no method to create or delete
# arrangement clips - users must do this manually in Ableton's Arrangement View.
from __future__ import absolute_import, print_function, unicode_literals


class ArrangementCommands:
    """Mixin providing Arrangement View command handlers."""

    def _get_arrangement_clips(self, track_index):
        """Return all clips placed in the Arrangement View for a track."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        clips = [
            {
                "index": i,
                "name": clip.name,
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "length": clip.length,
                "is_playing": clip.is_playing,
            }
            for i, clip in enumerate(track.arrangement_clips)
        ]
        return {"clips": clips, "count": len(clips)}

    def _add_notes_to_arrangement_clip(self, track_index, clip_index, notes):
        """Add MIDI notes to a clip in the Arrangement View.

        clip_index is the position of the clip in track.arrangement_clips.
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        arr_clips = list(track.arrangement_clips)
        if clip_index < 0 or clip_index >= len(arr_clips):
            raise IndexError(
                "Arrangement clip index out of range. Track has {0} arrangement clip(s).".format(
                    len(arr_clips)))
        clip = arr_clips[clip_index]
        live_notes = tuple(
            (n.get("pitch", 60), n.get("start_time", 0.0),
             n.get("duration", 0.25), n.get("velocity", 100), n.get("mute", False))
            for n in notes
        )
        clip.set_notes(live_notes)
        return {"note_count": len(notes)}

    def _set_arrangement_clip_name(self, track_index, clip_index, name):
        """Rename a clip in the Arrangement View."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        arr_clips = list(track.arrangement_clips)
        if clip_index < 0 or clip_index >= len(arr_clips):
            raise IndexError("Arrangement clip index out of range")
        arr_clips[clip_index].name = name
        return {"name": arr_clips[clip_index].name}
