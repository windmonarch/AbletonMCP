# AbletonMCPLocal/commands_devices.py
# Handlers for device parameter and drum pad commands.
#
# Nested devices are addressed by a device path: a list of indices that
# alternates device and chain, always starting and ending on a device:
#   [device_index]                                  top-level device
#   [device_index, chain_index, device_index]       device inside a rack chain
#   [d0, c0, d1, c1, d2, ...]                       deeper nesting
# Each (chain_index, device_index) pair walks rack.chains[c].devices[d].
from __future__ import absolute_import, print_function, unicode_literals


class DeviceCommands:
    """Mixin providing device parameter and drum pad command handlers."""

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _resolve_track(self, track_index, track_type="track"):
        """Return a track by type: "track" (default), "return" or "master"."""
        track_type = (track_type or "track").lower()
        if track_type == "master":
            return self._song.master_track
        if track_type == "return":
            tracks, label = self._song.return_tracks, "Return track"
        elif track_type == "track":
            tracks, label = self._song.tracks, "Track"
        else:
            raise ValueError(
                "Unknown track_type '{0}' (expected 'track', 'return' or 'master')".format(track_type))
        if track_index < 0 or track_index >= len(tracks):
            raise IndexError("{0} index {1} out of range ({2} available)".format(
                label, track_index, len(tracks)))
        return tracks[track_index]

    def _resolve_device_path(self, track, path):
        """Walk a device path ([device, chain, device, ...]) and return the device."""
        if not path:
            raise ValueError("Device path must be a non-empty list, e.g. [0] or [0, 2, 1]")
        try:
            path = [int(p) for p in path]
        except (TypeError, ValueError):
            raise ValueError("Device path must be a list of integers, got {0!r}".format(path))
        if len(path) % 2 == 0:
            raise ValueError(
                "Device path must have odd length ([device, chain, device, ...]), got {0}".format(path))

        devices = list(track.devices)
        owner = "track '{0}'".format(track.name)
        device = None
        for pos in range(0, len(path), 2):
            dev_idx = path[pos]
            if dev_idx < 0 or dev_idx >= len(devices):
                raise IndexError("path[{0}]={1}: device index out of range ({2} has {3} devices)".format(
                    pos, dev_idx, owner, len(devices)))
            device = devices[dev_idx]
            if pos + 1 < len(path):
                chain_idx = path[pos + 1]
                if not device.can_have_chains:
                    raise ValueError("path[{0}]={1}: device '{2}' is not a rack and has no chains".format(
                        pos + 1, chain_idx, device.name))
                chains = list(device.chains)
                if chain_idx < 0 or chain_idx >= len(chains):
                    raise IndexError("path[{0}]={1}: chain index out of range (rack '{2}' has {3} chains)".format(
                        pos + 1, chain_idx, device.name, len(chains)))
                chain = chains[chain_idx]
                devices = list(chain.devices)
                owner = "chain '{0}'".format(chain.name)
        return device

    @staticmethod
    def _param_display(param, value=None):
        """Display string for a parameter value as Live shows it (e.g. "4.00 : 1").

        Returns None when the Live API cannot format the value.
        """
        if value is None:
            value = param.value
        try:
            return param.str_for_value(value)
        except Exception:
            pass
        if value == param.value:
            try:
                return str(param)
            except Exception:
                pass
        return None

    def _serialize_parameter(self, index, param, detailed=False):
        info = {
            "index": index,
            "name": param.name,
            "value": param.value,
            "display_value": self._param_display(param),
            "min": param.min,
            "max": param.max,
            "is_enabled": param.is_enabled,
            "is_quantized": param.is_quantized,
        }
        if param.is_quantized:
            try:
                info["value_items"] = list(param.value_items)
            except Exception:
                pass
        if detailed:
            info["min_display"] = self._param_display(param, param.min)
            info["max_display"] = self._param_display(param, param.max)
            try:
                if param.original_name != param.name:
                    info["original_name"] = param.original_name
            except Exception:
                pass
        return info

    @staticmethod
    def _find_parameter(device, param_index=None, param_name=None):
        """Return (index, param) by index or by name (case-insensitive exact match).

        When both are given they must refer to the same parameter.
        """
        params = list(device.parameters)
        if param_index is None and param_name is None:
            raise ValueError("Provide param_index or param_name")

        by_index = None
        if param_index is not None:
            param_index = int(param_index)
            if param_index < 0 or param_index >= len(params):
                raise IndexError("Parameter index {0} out of range (device '{1}' has {2} parameters)".format(
                    param_index, device.name, len(params)))
            by_index = param_index

        if param_name is None:
            return by_index, params[by_index]

        wanted = param_name.strip().lower()
        matches = [i for i, p in enumerate(params) if p.name.strip().lower() == wanted]
        if not matches:
            for i, p in enumerate(params):
                try:
                    if p.original_name.strip().lower() == wanted:
                        matches.append(i)
                except Exception:
                    pass
        if not matches:
            close = [p.name for p in params if wanted in p.name.lower()]
            hint = " Did you mean: {0}?".format(", ".join("'{0}'".format(n) for n in close)) if close else ""
            raise ValueError("No parameter named '{0}' on device '{1}'.{2}".format(
                param_name, device.name, hint))

        if by_index is not None:
            if by_index not in matches:
                raise ValueError("param_index {0} is '{1}', which does not match param_name '{2}'".format(
                    by_index, params[by_index].name, param_name))
            return by_index, params[by_index]
        if len(matches) > 1:
            raise ValueError("Parameter name '{0}' is ambiguous on device '{1}' (indices {2}); pass param_index".format(
                param_name, device.name, matches))
        return matches[0], params[matches[0]]

    @staticmethod
    def _apply_parameter_value(param, value):
        if value is None:
            raise ValueError("value is required")
        if value < param.min or value > param.max:
            raise ValueError(
                "Value {0} out of range [{1}, {2}] for '{3}'".format(value, param.min, param.max, param.name))
        param.value = value

    # -------------------------------------------------------------------------
    # Top-level device commands (original index-based API)
    # -------------------------------------------------------------------------

    def _get_device_parameters(self, track_index, device_index):
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")
        track = self._song.tracks[track_index]
        if device_index < 0 or device_index >= len(track.devices):
            raise IndexError("Device index out of range")
        device = track.devices[device_index]
        params = [self._serialize_parameter(i, param) for i, param in enumerate(device.parameters)]
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
        return {
            "param_index": param_index,
            "name": param.name,
            "value": param.value,
            "display_value": self._param_display(param),
        }

    # -------------------------------------------------------------------------
    # Path-addressed device commands (reach devices nested in racks)
    # -------------------------------------------------------------------------

    def _get_device_parameters_at_path(self, track_index, path, track_type="track"):
        track = self._resolve_track(track_index, track_type)
        device = self._resolve_device_path(track, path)
        params = [self._serialize_parameter(i, p, detailed=True) for i, p in enumerate(device.parameters)]
        result = {
            "track_name": track.name,
            "path": [int(p) for p in path],
            "device_name": device.name,
            "class_name": device.class_name,
            "is_active": device.is_active,
            "can_have_chains": bool(device.can_have_chains),
            "parameters": params,
            "count": len(params),
        }
        if device.can_have_chains:
            result["chains"] = [
                {"index": ci, "name": chain.name, "device_count": len(chain.devices)}
                for ci, chain in enumerate(device.chains)
            ]
        return result

    def _set_device_parameter_at_path(self, track_index, path, value,
                                      param_index=None, param_name=None, track_type="track"):
        track = self._resolve_track(track_index, track_type)
        device = self._resolve_device_path(track, path)
        index, param = self._find_parameter(device, param_index, param_name)
        previous_value = param.value
        previous_display = self._param_display(param)
        self._apply_parameter_value(param, value)
        return {
            "track_name": track.name,
            "path": [int(p) for p in path],
            "device_name": device.name,
            "param_index": index,
            "name": param.name,
            "previous_value": previous_value,
            "previous_display_value": previous_display,
            "value": param.value,
            "display_value": self._param_display(param),
        }

    # -------------------------------------------------------------------------
    # Racks
    # -------------------------------------------------------------------------

    def _serialize_rack_device(self, dev, path, depth_remaining, include_parameters):
        info = {
            "index": path[-1],
            "path": path,
            "name": dev.name,
            "class_name": dev.class_name,
            "is_active": dev.is_active,
            "can_have_chains": bool(dev.can_have_chains),
        }
        if include_parameters:
            params = []
            try:
                params = [self._serialize_parameter(i, p) for i, p in enumerate(dev.parameters)]
            except Exception:
                pass
            info["parameters"] = params
        if dev.can_have_chains:
            if depth_remaining > 0:
                info["chains"] = self._serialize_chains(dev, path, depth_remaining, include_parameters)
            else:
                # Depth limit reached: say how much is below so the caller can go deeper.
                info["chain_count"] = len(dev.chains)
        return info

    def _serialize_chains(self, rack, rack_path, depth, include_parameters):
        chains = []
        for chain_index, chain in enumerate(rack.chains):
            chain_devices = [
                self._serialize_rack_device(dev, rack_path + [chain_index, dev_index],
                                            depth - 1, include_parameters)
                for dev_index, dev in enumerate(chain.devices)
            ]
            chains.append({
                "index": chain_index,
                "name": chain.name,
                "devices": chain_devices,
                "device_count": len(chain_devices),
            })
        return chains

    def _get_rack_devices(self, track_index, device_index, depth=1, include_parameters=True,
                          track_type="track", path=None):
        """Return the devices inside a rack's chains, with their parameters.

        depth=1 lists the rack's own chains (original behaviour); each extra level
        descends into nested racks. `path` addresses a nested rack and overrides
        device_index. Every device in the output carries its `path`.
        """
        if depth is None or int(depth) < 1:
            raise ValueError("depth must be >= 1")
        depth = int(depth)
        track = self._resolve_track(track_index, track_type)
        if path:
            rack_path = [int(p) for p in path]
        else:
            if device_index < 0 or device_index >= len(track.devices):
                raise IndexError("Device index out of range")
            rack_path = [device_index]
        device = self._resolve_device_path(track, rack_path)
        if not device.can_have_chains:
            raise Exception("Device does not have chains (not a rack)")

        chains = self._serialize_chains(device, rack_path, depth, include_parameters)
        return {
            "rack_name": device.name,
            "path": rack_path,
            "depth": depth,
            "chain_count": len(chains),
            "chains": chains,
        }

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
