# AbletonMCPLocal/commands_automation.py
# Handlers for clip automation envelope commands.
from __future__ import absolute_import, print_function, unicode_literals


class AutomationCommands:
    """Mixin providing clip automation envelope command handlers."""

    def _get_track_and_clip(self, track_index, clip_index):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        arr_clips = list(track.arrangement_clips)
        if clip_index < 0 or clip_index >= len(arr_clips):
            raise IndexError("Arrangement clip index out of range")
        return track, arr_clips[clip_index]

    def _get_param(self, track, device_index, param_index):
        if device_index < 0 or device_index >= len(track.devices):
            raise IndexError("Device index out of range")
        device = track.devices[device_index]
        params = list(device.parameters)
        if param_index < 0 or param_index >= len(params):
            raise IndexError("Parameter index out of range")
        return params[param_index]

    def _get_clip_envelope(self, track_index, clip_index, device_index, param_index):
        track, clip = self._get_track_and_clip(track_index, clip_index)
        param = self._get_param(track, device_index, param_index)
        envelope = clip.automation_envelope(param)
        if envelope is None:
            return {"has_envelope": False, "param_name": param.name}
        step = clip.length / 16.0 if clip.length > 0 else 0.25
        points = [
            {"time": round(i * step, 4), "value": round(envelope.value_at_time(i * step), 4)}
            for i in range(17)
        ]
        return {
            "has_envelope": True,
            "param_name": param.name,
            "param_min": param.min,
            "param_max": param.max,
            "points": points,
        }

    def _set_clip_envelope_point(self, track_index, clip_index, device_index, param_index, time, value, duration=0.0):
        track, clip = self._get_track_and_clip(track_index, clip_index)
        param = self._get_param(track, device_index, param_index)
        envelope = clip.automation_envelope(param)
        if envelope is None:
            try:
                envelope = clip.create_automation_envelope(param)
            except Exception:
                raise RuntimeError(
                    "No automation envelope exists for '{}' on this clip. "
                    "To create one: in Ableton, right-click the parameter, choose "
                    "'Show Automation in Arrangement Clip', draw at least one breakpoint, "
                    "then call this tool again.".format(param.name)
                )
        envelope.insert_step(float(time), float(duration), float(value))
        return {"inserted": True, "time": time, "value": value}

    def _clear_clip_envelope(self, track_index, clip_index, device_index, param_index):
        track, clip = self._get_track_and_clip(track_index, clip_index)
        param = self._get_param(track, device_index, param_index)
        clip.clear_envelope(param)
        return {"cleared": True, "param_name": param.name}
