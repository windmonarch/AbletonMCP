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

    # -------------------------------------------------------------------------
    # Cue points / song time
    # -------------------------------------------------------------------------

    def _get_cue_points(self):
        cue_points = list(self._song.cue_points)
        return {
            "cue_points": [{"name": cp.name, "time": cp.time} for cp in cue_points],
            "count": len(cue_points),
        }

    def _jump_to_cue(self, direction):
        if direction == "next":
            self._song.jump_to_next_cue()
        elif direction == "prev":
            self._song.jump_to_prev_cue()
        else:
            raise ValueError("direction must be 'next' or 'prev'")
        return {"jumped": True, "direction": direction}

    def _get_current_song_time(self):
        return {"current_song_time": self._song.current_song_time}

    # -------------------------------------------------------------------------
    # Clip note / property commands
    # -------------------------------------------------------------------------

    def _get_clip_notes(self, track_index, clip_index):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        arr_clips = list(track.arrangement_clips)
        if clip_index < 0 or clip_index >= len(arr_clips):
            raise IndexError("Arrangement clip index out of range")
        clip = arr_clips[clip_index]
        raw_notes = clip.get_notes(0.0, 0, clip.length, 128)
        notes = [
            {"pitch": n[0], "start_time": n[1], "duration": n[2], "velocity": n[3], "mute": n[4]}
            for n in raw_notes
        ]
        return {"notes": notes, "count": len(notes)}

    def _remove_notes_from_clip(self, track_index, clip_index):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        arr_clips = list(track.arrangement_clips)
        if clip_index < 0 or clip_index >= len(arr_clips):
            raise IndexError("Arrangement clip index out of range")
        clip = arr_clips[clip_index]
        clip.remove_notes(0.0, 0, clip.length, 128)
        return {"removed": True}

    def _set_clip_color(self, track_index, clip_index, color):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        arr_clips = list(track.arrangement_clips)
        if clip_index < 0 or clip_index >= len(arr_clips):
            raise IndexError("Arrangement clip index out of range")
        clip = arr_clips[clip_index]
        clip.color = color
        return {"color": clip.color}

    def _set_clip_pitch(self, track_index, clip_index, pitch_coarse, pitch_fine=None):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        arr_clips = list(track.arrangement_clips)
        if clip_index < 0 or clip_index >= len(arr_clips):
            raise IndexError("Arrangement clip index out of range")
        clip = arr_clips[clip_index]
        clip.pitch_coarse = pitch_coarse
        if pitch_fine is not None:
            clip.pitch_fine = pitch_fine
        return {"pitch_coarse": clip.pitch_coarse, "pitch_fine": clip.pitch_fine}

    def _set_clip_gain(self, track_index, clip_index, gain):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        arr_clips = list(track.arrangement_clips)
        if clip_index < 0 or clip_index >= len(arr_clips):
            raise IndexError("Arrangement clip index out of range")
        clip = arr_clips[clip_index]
        if not clip.is_audio_clip:
            raise Exception("Clip is not an audio clip")
        clip.gain = gain
        return {"gain": clip.gain}

    def _set_clip_markers(self, track_index, clip_index, start_marker, end_marker):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        arr_clips = list(track.arrangement_clips)
        if clip_index < 0 or clip_index >= len(arr_clips):
            raise IndexError("Arrangement clip index out of range")
        clip = arr_clips[clip_index]
        clip.start_marker = start_marker
        clip.end_marker = end_marker
        return {"start_marker": clip.start_marker, "end_marker": clip.end_marker}
