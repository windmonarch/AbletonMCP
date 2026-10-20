# tests/test_device_paths.py
# Offline tests for path-addressed device commands, using fake Live objects.
# Run: python3 -m unittest discover tests
import importlib.util
import os
import unittest

# Load commands_devices.py directly: importing the AbletonMCPLocal package
# would pull in _Framework, which only exists inside Ableton.
_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "commands_devices", os.path.join(_HERE, "..", "AbletonMCPLocal", "commands_devices.py"))
commands_devices = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(commands_devices)


class FakeParam:
    def __init__(self, name, value=0.0, min=0.0, max=1.0, fmt="{0:.2f}", quantized=False, items=()):
        self.name = name
        self.original_name = name
        self.value = value
        self.min = min
        self.max = max
        self.is_enabled = True
        self.is_quantized = quantized
        self.value_items = list(items)
        self._fmt = fmt

    def str_for_value(self, value):
        return self._fmt.format(value)

    def __str__(self):
        return self.str_for_value(self.value)


class FakeChain:
    def __init__(self, name, devices):
        self.name = name
        self.devices = devices


class FakeDevice:
    def __init__(self, name, class_name="Compressor2", params=None, chains=None):
        self.name = name
        self.class_name = class_name
        self.is_active = True
        self.parameters = params if params is not None else [FakeParam("Device On", 1.0)]
        self.chains = chains or []
        self.can_have_chains = chains is not None


class FakeTrack:
    def __init__(self, name, devices):
        self.name = name
        self.devices = devices


class FakeSong:
    def __init__(self, tracks, return_tracks=(), master_track=None):
        self.tracks = list(tracks)
        self.return_tracks = list(return_tracks)
        self.master_track = master_track


class Commands(commands_devices.DeviceCommands):
    def __init__(self, song):
        self._song = song


def make_deesser():
    return FakeDevice("Compressor", params=[
        FakeParam("Device On", 1.0, quantized=True, items=["Off", "On"]),
        FakeParam("Threshold", 0.85, fmt="{0:.1f} dB"),
        FakeParam("Ratio", 0.5, fmt="{0:.2f} : 1"),
        FakeParam("Release", 0.3, fmt="{0:.1f} ms"),
        FakeParam("S/C EQ Freq", 0.7, fmt="{0:.2f} kHz"),
    ])


def make_song():
    """Lead Vocal -> "Vocal Stem Processing" rack -> sub-racks, de-esser two levels deep."""
    sub_names = ["Gating", "Tuning", "Tonal Changes", "Light Compression", "Deessing", "Utility"]
    sub_racks = []
    for name in sub_names:
        inner = [make_deesser()] if name == "Deessing" else [FakeDevice(name + " FX", "Eq8")]
        sub_racks.append(FakeDevice(name, "AudioEffectGroupDevice",
                                    chains=[FakeChain(name + " Chain", inner)]))
    outer = FakeDevice("Vocal Stem Processing", "AudioEffectGroupDevice",
                       chains=[FakeChain("Main", sub_racks)])
    lead = FakeTrack("Lead Vocal", [outer, FakeDevice("Utility", "StereoGain")])
    ret = FakeTrack("A-Reverb", [FakeDevice("Reverb", "Reverb")])
    master = FakeTrack("Master", [FakeDevice("Limiter", "Limiter")])
    return FakeSong([lead], [ret], master)


DEESSER_PATH = [0, 0, 4, 0, 0]


class ResolvePathTests(unittest.TestCase):
    def setUp(self):
        self.cmd = Commands(make_song())
        self.track = self.cmd._song.tracks[0]

    def test_top_level(self):
        self.assertEqual(self.cmd._resolve_device_path(self.track, [1]).name, "Utility")

    def test_two_levels_deep(self):
        dev = self.cmd._resolve_device_path(self.track, DEESSER_PATH)
        self.assertEqual(dev.name, "Compressor")

    def test_even_length_rejected(self):
        with self.assertRaises(ValueError):
            self.cmd._resolve_device_path(self.track, [0, 0])

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            self.cmd._resolve_device_path(self.track, [])

    def test_chain_on_non_rack_rejected(self):
        with self.assertRaisesRegex(ValueError, "not a rack"):
            self.cmd._resolve_device_path(self.track, [1, 0, 0])

    def test_out_of_range_names_position(self):
        with self.assertRaisesRegex(IndexError, r"path\[3\]=9"):
            self.cmd._resolve_device_path(self.track, [0, 0, 4, 9, 0])

    def test_return_and_master_tracks(self):
        self.assertEqual(self.cmd._resolve_track(0, "return").name, "A-Reverb")
        self.assertEqual(self.cmd._resolve_track(0, "master").name, "Master")
        with self.assertRaises(ValueError):
            self.cmd._resolve_track(0, "bus")


class ParameterTests(unittest.TestCase):
    def setUp(self):
        self.cmd = Commands(make_song())

    def test_get_at_path_has_display_values(self):
        result = self.cmd._get_device_parameters_at_path(0, DEESSER_PATH)
        self.assertEqual(result["device_name"], "Compressor")
        ratio = [p for p in result["parameters"] if p["name"] == "Ratio"][0]
        self.assertEqual(ratio["display_value"], "0.50 : 1")
        self.assertEqual(ratio["max_display"], "1.00 : 1")
        device_on = result["parameters"][0]
        self.assertEqual(device_on["value_items"], ["Off", "On"])

    def test_set_by_name(self):
        result = self.cmd._set_device_parameter_at_path(0, DEESSER_PATH, 0.25, param_name="release")
        self.assertEqual(result["param_index"], 3)
        self.assertEqual(result["previous_value"], 0.3)
        self.assertEqual(result["value"], 0.25)
        self.assertEqual(result["display_value"], "0.2 ms")

    def test_set_by_index(self):
        result = self.cmd._set_device_parameter_at_path(0, DEESSER_PATH, 0.9, param_index=2)
        self.assertEqual(result["name"], "Ratio")

    def test_index_and_name_must_agree(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.cmd._set_device_parameter_at_path(0, DEESSER_PATH, 0.5, param_index=1, param_name="Ratio")

    def test_unknown_name_suggests(self):
        with self.assertRaisesRegex(ValueError, "S/C EQ Freq"):
            self.cmd._set_device_parameter_at_path(0, DEESSER_PATH, 0.5, param_name="freq")

    def test_out_of_range_value_rejected(self):
        with self.assertRaises(ValueError):
            self.cmd._set_device_parameter_at_path(0, DEESSER_PATH, 2.0, param_name="Ratio")

    def test_ambiguous_name_rejected(self):
        dev = self.cmd._resolve_device_path(self.cmd._song.tracks[0], DEESSER_PATH)
        dev.parameters.append(FakeParam("Ratio"))
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            self.cmd._set_device_parameter_at_path(0, DEESSER_PATH, 0.5, param_name="Ratio")

    def test_legacy_get_device_parameters_still_works(self):
        result = self.cmd._get_device_parameters(0, 1)
        self.assertEqual(result["count"], 1)
        self.assertIn("display_value", result["parameters"][0])


class RackTests(unittest.TestCase):
    def setUp(self):
        self.cmd = Commands(make_song())

    def test_default_depth_matches_old_shape(self):
        result = self.cmd._get_rack_devices(0, 0)
        self.assertEqual(result["rack_name"], "Vocal Stem Processing")
        deessing = result["chains"][0]["devices"][4]
        self.assertEqual(deessing["name"], "Deessing")
        self.assertEqual(deessing["path"], [0, 0, 4])
        self.assertNotIn("chains", deessing)
        self.assertEqual(deessing["chain_count"], 1)
        self.assertIn("parameters", deessing)

    def test_depth_two_reaches_deesser_with_usable_path(self):
        result = self.cmd._get_rack_devices(0, 0, depth=2, include_parameters=False)
        deesser = result["chains"][0]["devices"][4]["chains"][0]["devices"][0]
        self.assertEqual(deesser["path"], DEESSER_PATH)
        self.assertNotIn("parameters", deesser)
        # The path feeds straight into the setter.
        self.cmd._set_device_parameter_at_path(0, deesser["path"], 0.1, param_name="Threshold")

    def test_start_from_nested_rack_path(self):
        result = self.cmd._get_rack_devices(0, 0, path=[0, 0, 4])
        self.assertEqual(result["rack_name"], "Deessing")
        self.assertEqual(result["chains"][0]["devices"][0]["path"], DEESSER_PATH)

    def test_non_rack_rejected(self):
        with self.assertRaises(Exception):
            self.cmd._get_rack_devices(0, 1)

    def test_bad_depth_rejected(self):
        with self.assertRaises(ValueError):
            self.cmd._get_rack_devices(0, 0, depth=0)


if __name__ == "__main__":
    unittest.main()
