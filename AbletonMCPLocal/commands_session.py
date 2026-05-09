# AbletonMCPLocal/commands_session.py
# Handlers for Session View and global song commands.
# These run on Ableton's main thread via schedule_message().
from __future__ import absolute_import, print_function, unicode_literals


class SessionCommands:
    """Mixin providing Session View and global song command handlers."""

    # -------------------------------------------------------------------------
    # Session info / track info  (read-only, safe to call from any thread)
    # -------------------------------------------------------------------------

    def _get_session_info(self):
        return {
            "tempo": self._song.tempo,
            "signature_numerator": self._song.signature_numerator,
            "signature_denominator": self._song.signature_denominator,
            "track_count": len(self._song.tracks),
            "return_track_count": len(self._song.return_tracks),
            "master_track": {
                "name": "Master",
                "volume": self._song.master_track.mixer_device.volume.value,
                "panning": self._song.master_track.mixer_device.panning.value,
            },
        }

    def _get_track_info(self, track_index):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]

        clip_slots = []
        for slot_index, slot in enumerate(track.clip_slots):
            clip_info = None
            if slot.has_clip:
                clip = slot.clip
                clip_info = {
                    "name": clip.name,
                    "length": clip.length,
                    "is_playing": clip.is_playing,
                    "is_recording": clip.is_recording,
                }
            clip_slots.append({
                "index": slot_index,
                "has_clip": slot.has_clip,
                "clip": clip_info,
            })

        devices = [
            {
                "index": i,
                "name": device.name,
                "class_name": device.class_name,
                "type": self._get_device_type(device),
            }
            for i, device in enumerate(track.devices)
        ]

        return {
            "index": track_index,
            "name": track.name,
            "is_audio_track": track.has_audio_input,
            "is_midi_track": track.has_midi_input,
            "mute": track.mute,
            "solo": track.solo,
            "arm": track.arm if track.can_be_armed else False,
            "volume": track.mixer_device.volume.value,
            "panning": track.mixer_device.panning.value,
            "clip_slots": clip_slots,
            "devices": devices,
        }

    # -------------------------------------------------------------------------
    # Session View modifying commands (must run on main thread)
    # -------------------------------------------------------------------------

    def _create_midi_track(self, index):
        self._song.create_midi_track(index)
        new_index = len(self._song.tracks) - 1 if index == -1 else index
        new_track = self._song.tracks[new_index]
        return {"index": new_index, "name": new_track.name}

    def _set_track_name(self, track_index, name):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        track.name = name
        return {"name": track.name}

    def _create_clip(self, track_index, clip_index, length):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            raise IndexError("Clip index out of range")
        clip_slot = track.clip_slots[clip_index]
        if clip_slot.has_clip:
            raise Exception("Clip slot already has a clip")
        clip_slot.create_clip(length)
        return {"name": clip_slot.clip.name, "length": clip_slot.clip.length}

    def _add_notes_to_clip(self, track_index, clip_index, notes):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            raise IndexError("Clip index out of range")
        clip_slot = track.clip_slots[clip_index]
        if not clip_slot.has_clip:
            raise Exception("No clip in slot")
        live_notes = tuple(
            (n.get("pitch", 60), n.get("start_time", 0.0),
             n.get("duration", 0.25), n.get("velocity", 100), n.get("mute", False))
            for n in notes
        )
        clip_slot.clip.set_notes(live_notes)
        return {"note_count": len(notes)}

    def _set_clip_name(self, track_index, clip_index, name):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            raise IndexError("Clip index out of range")
        clip_slot = track.clip_slots[clip_index]
        if not clip_slot.has_clip:
            raise Exception("No clip in slot")
        clip_slot.clip.name = name
        return {"name": clip_slot.clip.name}

    def _set_tempo(self, tempo):
        self._song.tempo = tempo
        return {"tempo": self._song.tempo}

    def _fire_clip(self, track_index, clip_index):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            raise IndexError("Clip index out of range")
        clip_slot = track.clip_slots[clip_index]
        if not clip_slot.has_clip:
            raise Exception("No clip in slot")
        clip_slot.fire()
        return {"fired": True}

    def _stop_clip(self, track_index, clip_index):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            raise IndexError("Clip index out of range")
        track.clip_slots[clip_index].stop()
        return {"stopped": True}

    def _start_playback(self):
        self._song.start_playing()
        return {"playing": self._song.is_playing}

    def _stop_playback(self):
        self._song.stop_playing()
        return {"playing": self._song.is_playing}

    # -------------------------------------------------------------------------
    # Undo / redo
    # -------------------------------------------------------------------------

    def _undo(self):
        if not self._song.can_undo:
            raise Exception("Nothing to undo")
        self._song.undo()
        return {"undone": True}

    def _redo(self):
        if not self._song.can_redo:
            raise Exception("Nothing to redo")
        self._song.redo()
        return {"redone": True}

    # -------------------------------------------------------------------------
    # Track creation / deletion
    # -------------------------------------------------------------------------

    def _create_audio_track(self, index):
        self._song.create_audio_track(index)
        new_index = len(self._song.tracks) - 1 if index == -1 else index
        new_track = self._song.tracks[new_index]
        return {"index": new_index, "name": new_track.name}

    def _create_return_track(self):
        self._song.create_return_track()
        new_index = len(self._song.return_tracks) - 1
        new_track = self._song.return_tracks[new_index]
        return {"index": new_index, "name": new_track.name}

    def _delete_track(self, track_index):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        self._song.delete_track(track_index)
        return {"deleted": True, "track_count": len(self._song.tracks)}

    def _duplicate_track(self, track_index):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        self._song.duplicate_track(track_index)
        new_index = track_index + 1
        new_track = self._song.tracks[new_index]
        return {"original_index": track_index, "new_index": new_index, "name": new_track.name}

    # -------------------------------------------------------------------------
    # Track property setters
    # -------------------------------------------------------------------------

    def _set_track_color(self, track_index, color):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        track.color = color
        return {"color": track.color}

    def _set_track_mute(self, track_index, mute):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        track.mute = mute
        return {"mute": track.mute}

    def _set_track_solo(self, track_index, solo):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        track.solo = solo
        return {"solo": track.solo}

    def _set_track_arm(self, track_index, arm):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        if not track.can_be_armed:
            raise RuntimeError("Track '{}' cannot be armed (Group tracks and return tracks do not support arming)".format(track.name))
        track.arm = arm
        return {"arm": track.arm}

    def _set_track_volume(self, track_index, volume):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        track.mixer_device.volume.value = volume
        return {"volume": track.mixer_device.volume.value}

    def _set_track_pan(self, track_index, panning):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        track.mixer_device.panning.value = panning
        return {"panning": track.mixer_device.panning.value}

    # -------------------------------------------------------------------------
    # Send routing
    # -------------------------------------------------------------------------

    def _get_track_sends(self, track_index):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        sends = [
            {"index": i, "name": send.name, "value": send.value}
            for i, send in enumerate(track.mixer_device.sends)
        ]
        return {"sends": sends, "count": len(sends)}

    def _set_track_send(self, track_index, send_index, value):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        sends = list(track.mixer_device.sends)
        if send_index < 0 or send_index >= len(sends):
            raise IndexError("Send index out of range")
        sends[send_index].value = value
        return {"send_index": send_index, "value": sends[send_index].value}

    # -------------------------------------------------------------------------
    # Song-level controls
    # -------------------------------------------------------------------------

    def _set_time_signature(self, numerator, denominator):
        self._song.signature_numerator = numerator
        self._song.signature_denominator = denominator
        return {
            "signature_numerator": self._song.signature_numerator,
            "signature_denominator": self._song.signature_denominator,
        }

    def _jump_to_time(self, time):
        self._song.current_song_time = float(time)
        return {"current_song_time": float(time)}

    # -------------------------------------------------------------------------
    # Device deletion
    # -------------------------------------------------------------------------

    def _delete_device(self, track_index, device_index):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        if device_index < 0 or device_index >= len(track.devices):
            raise IndexError("Device index out of range")
        track.delete_device(device_index)
        return {"deleted": True, "device_count": len(track.devices)}

    # -------------------------------------------------------------------------
    # Return track commands
    # -------------------------------------------------------------------------

    def _set_return_track_name(self, return_track_index, name):
        if return_track_index < 0 or return_track_index >= len(self._song.return_tracks):
            raise IndexError("Return track index out of range")
        track = self._song.return_tracks[return_track_index]
        track.name = name
        return {"name": track.name}

    def _load_effect_on_return_track(self, return_track_index, item_uri):
        if return_track_index < 0 or return_track_index >= len(self._song.return_tracks):
            raise IndexError("Return track index out of range")
        track = self._song.return_tracks[return_track_index]
        app = self.application()
        if not app:
            raise RuntimeError("Could not access Live application")
        # Try exact URI match first (covers native effects + VST3/VST2 URIs).
        item = self._find_browser_item_by_uri(app.browser, item_uri)
        # Fallback: treat item_uri as a plain plugin name and search by name
        # with VST3 preferred over VST2.
        if item is None:
            item = self._find_plugin_by_name(app.browser, item_uri)
        if item is None:
            raise RuntimeError("Browser item not found: " + str(item_uri))
        self._song.view.selected_track = track
        app.browser.load_item(item)
        return {
            "loaded": True,
            "uri": item_uri,
            "item_name": item.name if hasattr(item, "name") else item_uri,
            "track_name": track.name,
        }

    def _get_return_track_info(self, return_track_index):
        if return_track_index < 0 or return_track_index >= len(self._song.return_tracks):
            raise IndexError("Return track index out of range")
        track = self._song.return_tracks[return_track_index]
        devices = [
            {
                "index": i,
                "name": device.name,
                "class_name": device.class_name,
                "type": self._get_device_type(device),
            }
            for i, device in enumerate(track.devices)
        ]
        return {
            "index": return_track_index,
            "name": track.name,
            "volume": track.mixer_device.volume.value,
            "panning": track.mixer_device.panning.value,
            "devices": devices,
        }

    # -------------------------------------------------------------------------
    # Device helper (shared)
    # -------------------------------------------------------------------------

    def _get_device_type(self, device):
        try:
            if device.can_have_drum_pads:
                return "drum_machine"
            elif device.can_have_chains:
                return "rack"
            elif "instrument" in device.class_display_name.lower():
                return "instrument"
            elif "audio_effect" in device.class_name.lower():
                return "audio_effect"
            elif "midi_effect" in device.class_name.lower():
                return "midi_effect"
        except Exception:
            pass
        return "unknown"
