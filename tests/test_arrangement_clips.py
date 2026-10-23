# tests/test_arrangement_clips.py
# Offline tests for create_arrangement_audio_clip, using fake Live objects.
# Run: python3 -m unittest discover tests
import importlib.util
import os
import tempfile
import unittest

# Load commands_arrangement.py directly: importing the AbletonMCPLocal package
# would pull in _Framework, which only exists inside Ableton.
_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "commands_arrangement", os.path.join(_HERE, "..", "AbletonMCPLocal", "commands_arrangement.py"))
commands_arrangement = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(commands_arrangement)


class FakeClip:
    def __init__(self, start, length):
        self.name = ""
        self.start_time = start
        self.end_time = start + length


class FakeAudioTrack:
    def __init__(self, name="Crashes", clip_length=4.0, returns_none=False):
        self.name = name
        self.is_foldable = False
        self.has_midi_input = False
        self.arrangement_clips = []
        self._clip_length = clip_length
        self._returns_none = returns_none
        self.calls = []

    def create_audio_clip(self, file_path, position):
        self.calls.append((file_path, position))
        clip = FakeClip(position, self._clip_length)
        self.arrangement_clips.append(clip)
        return None if self._returns_none else clip


class FakeMidiTrack(FakeAudioTrack):
    def __init__(self):
        super().__init__("Lead")
        self.has_midi_input = True


class FakeGroupTrack(FakeAudioTrack):
    def __init__(self):
        super().__init__("Drums bus")
        self.is_foldable = True


class LegacyAudioTrack:
    """An audio track from a pre-Live-12 API: no create_audio_clip."""
    name = "Old"
    is_foldable = False
    has_midi_input = False


class FakeSong:
    def __init__(self, tracks):
        self.tracks = list(tracks)


class Host(commands_arrangement.ArrangementCommands):
    def __init__(self, tracks):
        self._song = FakeSong(tracks)


class CreateArrangementAudioClipTests(unittest.TestCase):
    def setUp(self):
        fd, self.wav = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

    def tearDown(self):
        os.remove(self.wav)

    def test_places_and_names_clip(self):
        track = FakeAudioTrack()
        result = Host([track])._create_arrangement_audio_clip(0, self.wav, 64, "PH T2 Crash")
        self.assertEqual(track.calls, [(self.wav, 64.0)])
        self.assertEqual(result["name"], "PH T2 Crash")
        self.assertEqual(result["start_time"], 64)
        self.assertEqual(result["length"], 4.0)
        self.assertEqual(result["track_name"], "Crashes")

    def test_finds_clip_when_live_returns_none(self):
        track = FakeAudioTrack(returns_none=True)
        result = Host([track])._create_arrangement_audio_clip(0, self.wav, 16.0, "PH")
        self.assertEqual(result["start_time"], 16.0)
        self.assertEqual(track.arrangement_clips[0].name, "PH")

    def test_rejects_midi_track(self):
        with self.assertRaisesRegex(ValueError, "not an audio track"):
            Host([FakeMidiTrack()])._create_arrangement_audio_clip(0, self.wav, 0.0)

    def test_rejects_group_track(self):
        with self.assertRaisesRegex(ValueError, "not an audio track"):
            Host([FakeGroupTrack()])._create_arrangement_audio_clip(0, self.wav, 0.0)

    def test_rejects_missing_file(self):
        with self.assertRaisesRegex(ValueError, "not found"):
            Host([FakeAudioTrack()])._create_arrangement_audio_clip(0, "/no/such/file.wav", 0.0)

    def test_rejects_bad_track_index(self):
        with self.assertRaises(IndexError):
            Host([FakeAudioTrack()])._create_arrangement_audio_clip(5, self.wav, 0.0)

    def test_pre_live_12_api_errors_clearly(self):
        with self.assertRaisesRegex(RuntimeError, "Live 12"):
            Host([LegacyAudioTrack()])._create_arrangement_audio_clip(0, self.wav, 0.0)


if __name__ == "__main__":
    unittest.main()
