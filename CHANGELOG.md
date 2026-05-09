# Changelog

All notable changes to this project will be documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.4.0] - 2026-05-09

### Added

**Return track tools**
- `get_return_track_info` - get name, volume, panning, and device list for a return track (uses `song.return_tracks[]` index, separate from `song.tracks[]`)
- `set_return_track_name` - rename a return track
- `load_effect_on_return_track` - load a browser item onto a return track by URI

**Rack inspection**
- `get_rack_devices` - traverse all chains inside a rack (Audio Effect Rack, Instrument Rack, Drum Rack) and return every nested device with its full parameter list. `get_device_parameters` only returns a rack's macro knobs - use this tool to reach the devices inside.

**Deployment script**
- `deploy.ps1` - copies remote script files to Ableton and syncs server files to all active Claude Code worktrees in one step

### Fixed
- `load_effect_on_return_track` initially called `app.browser.load_item(item, track)` which fails - the Live API's `load_item` takes only a `BrowserItem`. Fixed to select the track via `song.view.selected_track` first, then call `load_item(item)`.
- `.mcp.json` now uses an absolute path for `server_arrangement.py` to prevent Claude Code worktrees from loading stale server files.

---

## [1.3.0] - 2026-05-01

### Changed
- Renamed Remote Script folder from `AbletonMCPArrangement` to `AbletonMCPLocal`
- Renamed Python class from `AbletonMCPArrangement` to `AbletonMCPLocal`

### Migration
Existing users must update their setup:
1. Close Ableton
2. Rename the deployed folder from `AbletonMCPArrangement` to `AbletonMCPLocal` in `Documents\Ableton\User Library\Remote Scripts\`
3. Delete `__pycache__` inside the renamed folder
4. Restart Ableton
5. In Preferences -> Link, Tempo & MIDI -> Control Surface, reselect `AbletonMCPLocal`

---

## [1.2.1] - 2026-05-01

### Fixed
- `get_track_info` no longer crashes when called on a Group track - the Live API throws an exception accessing `track.arm` on non-armable tracks; fixed by checking `track.can_be_armed` before reading the property
- `set_track_arm` now raises a clear error when called on a Group track instead of propagating a Live API exception
- `get_arrangement_clips` no longer crashes when called on a Group track - the Live API throws an exception accessing `track.arrangement_clips` on foldable tracks; fixed by returning an empty clip list for Group tracks
- `load_drum_kit` no longer selects the Drum Rack device itself as the kit to load - the browser item filter now excludes entries where `is_device` is true, so only preset files (.adg) are considered

---

## [1.2.0] - 2026-05-01

### Added

**Scene management**
- `get_scenes` - list all scenes with name, tempo, and triggered state
- `create_scene` - add a new scene at a given index
- `delete_scene` - remove a scene by index
- `fire_scene` - launch all clips in a scene
- `set_scene_name` - rename a scene
- `set_scene_tempo` - assign a tempo to a scene (fires when scene is launched)

**Cue points (locators)**
- `create_cue_point` - create a locator at a beat position in the arrangement
- `delete_cue_point` - remove a locator by index
- `set_cue_point_name` - rename a locator

**Clip operations**
- `quantize_clip` - quantize MIDI notes to a grid (bar, 1/2, 1/4, 1/8, 1/16, 1/32)
- `duplicate_clip_loop` - double a clip's loop length by duplicating its content
- `set_clip_mute` - mute or unmute an Arrangement View clip
- `clear_clip_envelopes` - remove all automation envelopes from a clip

**Session controls**
- `set_time_signature` - set the session time signature (numerator and denominator)
- `jump_to_time` - move the playhead to a specific beat position

**Clip automation envelopes** *(Session View clips only - Live API limitation)*
- `get_clip_envelope` - read automation points for a device parameter in a clip
- `set_clip_envelope_point` - insert an automation breakpoint into a clip envelope
- `clear_clip_envelope` - clear automation for a specific device parameter in a clip

### Fixed
- `jump_to_time` previously returned the pre-move playhead position due to a Live API read-back timing issue - now correctly returns the target position

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
