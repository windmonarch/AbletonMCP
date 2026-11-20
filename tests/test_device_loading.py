# tests/test_device_loading.py
# Offline tests for loading browser items onto tracks, returns and the Master,
# and for deleting devices from any of them, using fake Live objects.
# Run: python3 -m unittest discover tests
import importlib.util
import os
import unittest

# Load the command modules directly: importing the AbletonMCPLocal package
# would pull in _Framework, which only exists inside Ableton.
_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(_HERE, "..", "AbletonMCPLocal", name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


commands_browser = _load("commands_browser")
commands_devices = _load("commands_devices")
commands_session = _load("commands_session")


class FakeDevice:
    def __init__(self, name):
        self.name = name


class FakeTrack:
    def __init__(self, name, devices=()):
        self.name = name
        self.devices = [FakeDevice(d) for d in devices]

    def delete_device(self, index):
        del self.devices[index]


class FakeItem:
    def __init__(self, name, uri=None, children=(), loadable=True):
        self.name = name
        self.uri = uri
        self.children = list(children)
        self.is_loadable = loadable


class FakeBrowser:
    def __init__(self, song):
        self._song = song
        self.loaded = []
        self.audio_effects = FakeItem("Audio Effects", children=[
            FakeItem("Utility", "query:AudioFx#Utility"),
            FakeItem("Limiter", "query:AudioFx#Limiter"),
        ], loadable=False)
        self.plugins = FakeItem("Plugins", children=[
            FakeItem("VST", children=[
                FakeItem("iZotope", children=[FakeItem("Ozone Imager 2", "query:Plugins#VST:iZotope:Ozone%20Imager%202")],
                         loadable=False)], loadable=False),
            FakeItem("VST3", children=[
                FakeItem("iZotope", children=[FakeItem("Ozone Imager 2", "query:Plugins#VST3:iZotope:Ozone%20Imager%202")],
                         loadable=False)], loadable=False),
        ], loadable=False)
        for attr in ("instruments", "sounds", "drums", "midi_effects"):
            setattr(self, attr, FakeItem(attr, children=[], loadable=False))

    def load_item(self, item):
        # Live loads onto whichever track is selected.
        track = self._song.view.selected_track
        track.devices.append(FakeDevice(item.name))
        self.loaded.append((track.name, item.name, item.uri))


class FakeView:
    selected_track = None


class FakeSong:
    def __init__(self):
        self.tracks = [FakeTrack("Lead Vocal", ["EQ Eight"])]
        self.return_tracks = [FakeTrack("A-Reverb", ["Reverb", "Leftover Utility"])]
        self.master_track = FakeTrack("Master")
        self.view = FakeView()


class FakeApp:
    def __init__(self, browser):
        self.browser = browser


class Commands(commands_session.SessionCommands, commands_browser.BrowserCommands,
               commands_devices.DeviceCommands):
    def __init__(self):
        self._song = FakeSong()
        self._app = FakeApp(FakeBrowser(self._song))

    def application(self):
        return self._app

    def log_message(self, msg):
        pass


class LoadTargetTests(unittest.TestCase):
    def setUp(self):
        self.cmd = Commands()

    def test_default_is_regular_track(self):
        track, kind = self.cmd._resolve_load_target("load_browser_item", {"track_index": 0})
        self.assertEqual((track.name, kind), ("Lead Vocal", "track"))

    def test_master_ignores_index(self):
        track, kind = self.cmd._resolve_load_target(
            "load_browser_item", {"track_index": 7, "track_type": "Master"})
        self.assertEqual((track.name, kind), ("Master", "master"))

    def test_return_via_track_type(self):
        track, kind = self.cmd._resolve_load_target(
            "load_browser_item", {"track_index": 0, "track_type": "return"})
        self.assertEqual((track.name, kind), ("A-Reverb", "return"))

    def test_return_command_uses_return_index(self):
        track, kind = self.cmd._resolve_load_target(
            "load_effect_on_return_track", {"return_track_index": 0})
        self.assertEqual((track.name, kind), ("A-Reverb", "return"))

    def test_bad_index_and_type(self):
        with self.assertRaises(IndexError):
            self.cmd._resolve_load_target("load_browser_item", {"track_index": 3})
        with self.assertRaises(ValueError):
            self.cmd._resolve_load_target("load_browser_item", {"track_type": "bus"})


class LoadTests(unittest.TestCase):
    def setUp(self):
        self.cmd = Commands()
        self.browser = self.cmd._app.browser

    def test_load_utility_on_master(self):
        result = self.cmd._load_browser_item(0, "query:AudioFx#Utility", track_type="master")
        self.assertEqual(self.browser.loaded, [("Master", "Utility", "query:AudioFx#Utility")])
        self.assertIs(self.cmd._song.view.selected_track, self.cmd._song.master_track)
        self.assertEqual(result["track_name"], "Master")
        self.assertEqual(result["track_type"], "master")
        self.assertEqual(result["devices_after"], ["Utility"])

    def test_plugin_name_fallback_prefers_vst3(self):
        self.cmd._load_browser_item(0, "Ozone Imager 2", track_type="master")
        self.assertEqual(self.browser.loaded[0][2], "query:Plugins#VST3:iZotope:Ozone%20Imager%202")

    def test_default_track_load_unchanged(self):
        result = self.cmd._load_browser_item(0, "query:AudioFx#Limiter")
        self.assertEqual(result["track_name"], "Lead Vocal")
        self.assertEqual(result["devices_after"], ["EQ Eight", "Limiter"])

    def test_return_loader_still_targets_returns(self):
        result = self.cmd._load_effect_on_return_track(0, "query:AudioFx#Utility")
        self.assertEqual(result["track_name"], "A-Reverb")

    def test_unknown_item_loads_nothing(self):
        with self.assertRaisesRegex(RuntimeError, "not found"):
            self.cmd._load_browser_item(0, "query:AudioFx#Nope", track_type="master")
        self.assertEqual(self.browser.loaded, [])


class DeleteDeviceTests(unittest.TestCase):
    def setUp(self):
        self.cmd = Commands()

    def test_delete_from_return(self):
        result = self.cmd._delete_device(0, 1, track_type="return")
        self.assertEqual(result["device_name"], "Leftover Utility")
        self.assertEqual([d.name for d in self.cmd._song.return_tracks[0].devices], ["Reverb"])
        self.assertEqual(result["device_count"], 1)

    def test_delete_from_master(self):
        self.cmd._load_browser_item(0, "query:AudioFx#Utility", track_type="master")
        result = self.cmd._delete_device(5, 0, track_type="master")
        self.assertEqual((result["track_name"], result["device_count"]), ("Master", 0))

    def test_default_track_and_range_check(self):
        self.assertEqual(self.cmd._delete_device(0, 0)["track_name"], "Lead Vocal")
        with self.assertRaisesRegex(IndexError, "out of range"):
            self.cmd._delete_device(0, 0)


if __name__ == "__main__":
    unittest.main()
