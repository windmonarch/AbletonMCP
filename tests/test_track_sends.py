# tests/test_track_sends.py
# Offline tests for send reads/writes in dB, using fake Live objects.
# Run: python3 -m unittest discover tests
import importlib.util
import math
import os
import unittest

# Load commands_session.py directly: importing the AbletonMCPLocal package
# would pull in _Framework, which only exists inside Ableton.
_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "commands_session", os.path.join(_HERE, "..", "AbletonMCPLocal", "commands_session.py"))
commands_session = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(commands_session)


def fake_taper_db(value):
    """Steep, monotonic stand-in for Live's send taper: 1.0 = 0 dB, 0.0 = -inf."""
    if value <= 0.0:
        return float("-inf")
    return 60.0 * math.log10(value) + 5.4 * (value - 1.0)


class FakeSend:
    def __init__(self, name, value=0.0, formats=True):
        self.name = name
        self.value = value
        self.min = 0.0
        self.max = 1.0
        self._formats = formats

    def str_for_value(self, value):
        if not self._formats:
            raise RuntimeError("no display")
        db = fake_taper_db(value)
        if db == float("-inf"):
            return "-inf dB"
        return "%.1f dB" % (round(db, 1) + 0.0)  # + 0.0 drops "-0.0", as Live does

    def __str__(self):
        return self.str_for_value(self.value)


class FakeMixer:
    def __init__(self, sends):
        self.sends = sends


class FakeTrack:
    def __init__(self, sends):
        self.mixer_device = FakeMixer(sends)


class FakeSong:
    def __init__(self, tracks):
        self.tracks = tracks


class Host(commands_session.SessionCommands):
    def __init__(self, song):
        self._song = song


def make_host(*sends):
    return Host(FakeSong([FakeTrack(list(sends))]))


class GetTrackSendsTests(unittest.TestCase):
    def test_reports_display_and_db(self):
        host = make_host(FakeSend("A-ROOM", 0.10), FakeSend("B-CHAMBER", 0.0))
        sends = host._get_track_sends(0)["sends"]
        self.assertEqual(sends[0]["value"], 0.10)
        self.assertEqual(sends[0]["display_value"], "%.1f dB" % fake_taper_db(0.10))
        self.assertAlmostEqual(sends[0]["db"], round(fake_taper_db(0.10), 1))
        self.assertEqual(sends[1]["display_value"], "-inf dB")
        self.assertEqual(sends[1]["db"], float("-inf"))

    def test_missing_display_gives_none(self):
        host = make_host(FakeSend("A-ROOM", 0.5, formats=False))
        send = host._get_track_sends(0)["sends"][0]
        self.assertIsNone(send["display_value"])
        self.assertIsNone(send["db"])


class SetTrackSendTests(unittest.TestCase):
    def test_raw_value_still_works(self):
        host = make_host(FakeSend("A-ROOM"))
        result = host._set_track_send(0, 0, value=0.5)
        self.assertEqual(result["value"], 0.5)
        self.assertEqual(result["send_index"], 0)

    def test_db_target_lands_on_displayed_level(self):
        send = FakeSend("A-ROOM")
        host = make_host(send)
        for target in (-22.0, -15.0, -54.6, -6.0, 0.0):
            result = host._set_track_send(0, 0, db=target)
            self.assertAlmostEqual(result["db"], target, places=1)
            self.assertEqual(result["display_value"], "%.1f dB" % target)
            self.assertEqual(send.value, result["value"])

    def test_db_minus_inf_turns_send_off(self):
        send = FakeSend("A-ROOM", 0.7)
        host = make_host(send)
        result = host._set_track_send(0, 0, db=float("-inf"))
        self.assertEqual(send.value, 0.0)
        self.assertEqual(result["db"], float("-inf"))

    def test_db_above_max_is_rejected(self):
        send = FakeSend("A-ROOM", 0.3)
        host = make_host(send)
        with self.assertRaises(ValueError):
            host._set_track_send(0, 0, db=3.0)
        self.assertEqual(send.value, 0.3)

    def test_needs_exactly_one_of_value_or_db(self):
        host = make_host(FakeSend("A-ROOM"))
        with self.assertRaises(ValueError):
            host._set_track_send(0, 0)
        with self.assertRaises(ValueError):
            host._set_track_send(0, 0, value=0.5, db=-10.0)

    def test_db_without_display_raises(self):
        host = make_host(FakeSend("A-ROOM", formats=False))
        with self.assertRaises(RuntimeError):
            host._set_track_send(0, 0, db=-20.0)

    def test_index_errors(self):
        host = make_host(FakeSend("A-ROOM"))
        with self.assertRaises(IndexError):
            host._set_track_send(1, 0, db=-20.0)
        with self.assertRaises(IndexError):
            host._set_track_send(0, 3, db=-20.0)
        with self.assertRaises(IndexError):
            host._get_track_sends(5)


if __name__ == "__main__":
    unittest.main()
