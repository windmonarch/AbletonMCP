# tests/test_arrangement_clips.py
# Offline tests for create_arrangement_audio_clip and create_arrangement_midi_clip,
# using fake Live objects.
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
        self.notes = ()

    def set_notes(self, notes):
        self.notes = notes


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


class FakeMidiClipTrack:
    def __init__(self, name="Placeholder", returns_none=False, existing=()):
        self.name = name
        self.is_foldable = False
        self.has_midi_input = True
        self.arrangement_clips = [FakeClip(s, l) for s, l in existing]
        self._returns_none = returns_none
        self.calls = []

    def create_midi_clip(self, start_time, length):
        self.calls.append((start_time, length))
        clip = FakeClip(start_time, length)
        self.arrangement_clips.append(clip)
        self.arrangement_clips.sort(key=lambda c: c.start_time)
        return None if self._returns_none else clip


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


class LegacyMidiTrack:
    """A MIDI track from a pre-Live-12 API: no create_midi_clip."""
    name = "Old"
    is_foldable = False
    has_midi_input = True


class CreateArrangementMidiClipTests(unittest.TestCase):
    def test_creates_and_names_empty_clip(self):
        track = FakeMidiClipTrack()
        result = Host([track])._create_arrangement_midi_clip(0, 64.0, 4.0, "Impact")
        self.assertEqual(track.calls, [(64.0, 4.0)])
        self.assertEqual(result["name"], "Impact")
        self.assertEqual(result["length"], 4.0)
        self.assertEqual(result["note_count"], 0)
        self.assertEqual(track.arrangement_clips[0].notes, ())

    def test_writes_notes_in_clip_time(self):
        track = FakeMidiClipTrack()
        notes = [{"pitch": 43, "start_time": 0.0, "duration": 1.0, "velocity": 100}]
        result = Host([track])._create_arrangement_midi_clip(0, 252.0, 4.0, notes=notes)
        self.assertEqual(result["note_count"], 1)
        self.assertEqual(track.arrangement_clips[0].notes, ((43, 0.0, 1.0, 100, False),))

    def test_reports_index_among_existing_clips(self):
        track = FakeMidiClipTrack(existing=[(56.0, 8.0), (300.0, 16.0)])
        result = Host([track])._create_arrangement_midi_clip(0, 64.0, 4.0)
        self.assertEqual(result["clip_index"], 1)

    def test_finds_clip_when_live_returns_none(self):
        track = FakeMidiClipTrack(returns_none=True)
        result = Host([track])._create_arrangement_midi_clip(0, 16.0, 2.0, "PH")
        self.assertEqual(result["start_time"], 16.0)
        self.assertEqual(track.arrangement_clips[0].name, "PH")

    def test_rejects_audio_track(self):
        with self.assertRaisesRegex(ValueError, "not a MIDI track"):
            Host([FakeAudioTrack()])._create_arrangement_midi_clip(0, 0.0, 4.0)

    def test_rejects_group_track(self):
        group = FakeMidiClipTrack()
        group.is_foldable = True
        with self.assertRaisesRegex(ValueError, "not a MIDI track"):
            Host([group])._create_arrangement_midi_clip(0, 0.0, 4.0)

    def test_rejects_zero_length(self):
        with self.assertRaisesRegex(ValueError, "length"):
            Host([FakeMidiClipTrack()])._create_arrangement_midi_clip(0, 0.0, 0.0)

    def test_rejects_bad_track_index(self):
        with self.assertRaises(IndexError):
            Host([FakeMidiClipTrack()])._create_arrangement_midi_clip(3, 0.0, 4.0)

    def test_pre_live_12_api_errors_clearly(self):
        with self.assertRaisesRegex(RuntimeError, "Live 12"):
            Host([LegacyMidiTrack()])._create_arrangement_midi_clip(0, 0.0, 4.0)


if __name__ == "__main__":
    unittest.main()
