# Changelog

All notable changes to this project will be documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.0] - 2026-04-30

### Added

**Arrangement View**
- `get_cue_points` - list all cue points in the session
- `jump_to_cue` - jump playback to a named cue point
- `get_current_song_time` - get the current playhead position in beats

**Track controls**
- `create_audio_track` - add a new audio track
- `create_return_track` - add a new return track
- `delete_track` - remove a track from the session
- `duplicate_track` - duplicate an existing track
- `set_track_color` - change a track's color
- `set_track_mute` - mute or unmute a track
- `set_track_solo` - solo or unsolo a track
- `set_track_arm` - arm or disarm a track for recording
- `set_track_volume` - set a track's volume
- `set_track_pan` - set a track's panning
- `get_track_sends` - get a track's send levels
- `set_track_send` - set a track's send level

**Clip editing**
- `get_clip_notes` - read MIDI notes from a clip
- `remove_notes_from_clip` - clear notes from a clip
- `set_clip_color` - change a clip's color
- `set_clip_pitch` - transpose a clip's pitch
- `set_clip_gain` - set a clip's gain (audio clips)
- `set_clip_markers` - set a clip's start and end markers

**Device controls**
- `get_device_parameters` - list all parameters of a device
- `set_device_parameter` - set a device parameter value
- `get_drum_pads` - list drum pads in a drum rack

**Session controls**
- `undo` - undo the last action in Ableton
- `redo` - redo the last undone action

---

## [1.0.0] - 2026-04-30

Initial release. Forked from [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp) and extended with Arrangement View support and a refactored multi-file structure.

### Added

**Global / both views**
- `get_session_info` - tempo, time signature, track count, master track info
- `get_track_info` - name, type, mute/solo/arm, volume, panning, devices
- `create_midi_track` - add a new MIDI track
- `set_track_name` - rename a track
- `set_tempo` - change session tempo
- `start_playback` - press Play
- `stop_playback` - press Stop
- `load_instrument_or_effect` - load a device onto a track by URI
- `load_drum_kit` - load a drum rack and kit onto a track
- `get_browser_tree` - browse available instruments, effects, and samples
- `get_browser_items_at_path` - list items at a specific browser path

**Arrangement View**
- `get_arrangement_clips` - list all clips on a track in Arrangement View
- `add_notes_to_arrangement_clip` - write MIDI notes into an Arrangement View clip
- `set_arrangement_clip_name` - rename an Arrangement View clip

**Session View**
- `create_clip` - create an empty MIDI clip in a Session View slot
- `add_notes_to_clip` - write MIDI notes into a Session View clip
- `set_clip_name` - rename a Session View clip
- `fire_clip` - launch a Session View clip
- `stop_clip` - stop a playing Session View clip

### Changed
- Split monolithic `server_arrangement.py` into `ableton/` package (connection.py, tools_session.py, tools_arrangement.py, tools_browser.py)
- Split monolithic remote script `__init__.py` into submodules (commands_session.py, commands_arrangement.py, commands_browser.py)
- Replaced `if/elif` dispatch chain with `READ_DISPATCH` and `WRITE_DISPATCH` dicts
