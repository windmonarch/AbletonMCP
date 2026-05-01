# AbletonMCPLocal/commands_devices.py
# Handlers for device parameter and drum pad commands.
from __future__ import absolute_import, print_function, unicode_literals


class DeviceCommands:
    """Mixin providing device parameter and drum pad command handlers."""

    def _get_device_parameters(self, track_index, device_index):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        if device_index < 0 or device_index >= len(track.devices):
            raise IndexError("Device index out of range")
        device = track.devices[device_index]
        params = [
            {
                "index": i,
                "name": param.name,
                "value": param.value,
                "min": param.min,
                "max": param.max,
                "is_enabled": param.is_enabled,
            }
            for i, param in enumerate(device.parameters)
        ]
        return {"parameters": params, "count": len(params)}

    def _set_device_parameter(self, track_index, device_index, param_index, value):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        if device_index < 0 or device_index >= len(track.devices):
            raise IndexError("Device index out of range")
        device = track.devices[device_index]
        params = list(device.parameters)
        if param_index < 0 or param_index >= len(params):
            raise IndexError("Parameter index out of range")
        param = params[param_index]
        if value < param.min or value > param.max:
            raise ValueError(
                "Value {0} out of range [{1}, {2}]".format(value, param.min, param.max))
        param.value = value
        return {"param_index": param_index, "name": param.name, "value": param.value}

    def _get_drum_pads(self, track_index, device_index):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        if device_index < 0 or device_index >= len(track.devices):
            raise IndexError("Device index out of range")
        device = track.devices[device_index]
        if not device.can_have_drum_pads:
            raise Exception("Device does not support drum pads")
        pads = [
            {"note": pad.note, "name": pad.name, "mute": pad.mute, "solo": pad.solo}
            for pad in device.drum_pads
        ]
        return {"drum_pads": pads, "count": len(pads)}
