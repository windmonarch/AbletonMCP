# Changelog

All notable changes to this project will be documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.11.0] - 2026-10-28

### Changed

**Send levels in dB**
- `get_track_sends` now reports each send's `display_value` (what Live shows, e.g. `"-22.0 dB"`) and `db` (that level as a number, `-inf` when off), alongside the existing `value`.
- `set_track_send` takes either `db` or `value`. With `db` it finds the knob position whose displayed level matches, by binary search over Live's own `str_for_value`, so the result tracks Live's taper exactly instead of a hard-coded curve. Targets above the send maximum are rejected; `-inf` turns the send off. The response now includes `display_value` and `db`.
- 8 new offline tests in `tests/test_track_sends.py` (46 total).

### Why

- `value` is the normalized knob position, and Live's send taper is steep: 0.10 displays as **-54.6 dB**. Send levels recommended and set as 0.xx values on How to Die (Lead A-ROOM "0.10") came out effectively silent, and nothing in the old response showed it.

### Notes

- Verified in Live 12.4.6: Lead A-ROOM read back as `-54.6 dB` (matching the GUI); `db=-22`, `-20` and `-32` landed on exactly `-22.0`, `-20.0` and `-32.0 dB`; `db=3` was rejected as above the 0 dB maximum.
- Existing callers that pass `value` are unchanged. `value` is now optional, and passing both or neither is an error.
- Return-track and master sends are not covered; only `get_track_sends` / `set_track_send`.

### Internal

- 72 tools (unchanged).
- Remote Script change: run `deploy.sh` / `deploy.ps1` and fully quit and relaunch Ableton.

---

## [1.10.0] - 2026-10-27

### Added

**Clip mute state and source file in `get_arrangement_clips`**
- Each clip now reports `muted` (Live's clip activator, the 0 key). Clip mutes were previously invisible to the MCP; only track mutes could be read, so a sweep of the arrangement could not tell which clips had been switched off.
- Audio clips also report `file_path`, the source file on disk. A sample already placed in the arrangement can now be copied to new positions with `create_arrangement_audio_clip` without searching the disk for it (pack and library samples are often not indexed by Spotlight).
- 1 new offline test in `tests/test_arrangement_clips.py` (37 total).

### Notes

- First use: documenting a final-listen pass on the How to Die transitions, where FX clips had been muted by ear across 3 of 11 transitions.
- `file_path` is omitted for MIDI clips. Field additions only; existing keys are unchanged.

### Internal

- 72 tools (unchanged).
- Remote Script change: run `deploy.sh` / `deploy.ps1` and fully quit and relaunch Ableton.

---

## [1.9.0] - 2026-10-27

### Added

**Arrangement MIDI clip creation**
- `create_arrangement_midi_clip(track_index, start_time, length, name, notes)` - creates a MIDI clip on a MIDI track in the Arrangement View at a beat position, optionally names it and fills it with notes in one call. Note times are beats from the clip start, the same as `add_notes_to_arrangement_clip`. Returns the new clip's `clip_index`, start/end time and length so follow-up calls can address it without a separate lookup. Built on `Track.create_midi_clip` from the Live 12 API; earlier Live versions get a clear error.
- First use: render lanes for custom Vital transition sounds (risers, impacts) without drawing empty clips by hand.
- 9 new offline tests in `tests/test_arrangement_clips.py`: empty and note-filled clips, index reporting among existing clips, the `None`-return fallback, audio/group-track rejection, zero length, out-of-range track, and the pre-Live-12 error.

### Changed

- README: the "creating an arrangement clip" limitation now applies only to Live 11 and earlier.

### Notes

- Verified in Live 12.4.6: two 4-beat clips created on a MIDI track with a G1 note each; positions, names, returned `clip_index` and notes all read back as written.
- The command does not check for overlaps with existing clips on the track.
- Arrangement clip indices shift when a clip is added earlier on the track; use the returned `clip_index` straight away or re-read with `get_arrangement_clips`.

### Internal

- 72 tools (was 71).
- `create_arrangement_midi_clip` added to `WRITE_DISPATCH` and `MODIFYING_COMMANDS`.
- Remote Script change: run `deploy.sh` / `deploy.ps1` and fully quit and relaunch Ableton.

---

## [1.8.0] - 2026-10-23

### Added

**Arrangement audio clip placement**
- `create_arrangement_audio_clip(track_index, file_path, start_time, name)` - places an audio file on an audio track in the Arrangement View at a beat position and optionally names the clip. Returns the created clip's name, start/end time and length so the placement can be verified. Built on `Track.create_audio_clip`, which the Live 12 API added; earlier Live versions get a clear error instead of a failure.
- First use: laying out 34 named placeholder transition sounds (sweeps, risers, reverses, crashes, impacts, fills) across a full song so the producer can swap in final samples at known positions and lengths.
- `tests/test_arrangement_clips.py` - offline `unittest` cases with fake Live objects: success path with naming, MIDI/group-track rejection, missing file, out-of-range track, and the pre-Live-12 error.

### Changed

- The "creating an arrangement clip is impossible" limitation now applies to MIDI clips only. README tool table and limitations section updated.

### Notes

- Overlapping an existing clip on the same track replaces that region, the same as dropping audio in Live. The command does not check for overlaps; plan positions so clips don't collide.
- Read clip lengths back after placing. In testing, 33 of 34 clips landed at their file length exactly; one 5-beat file was placed as a 4-beat clip.
- Validation happens before calling Live: the track must be a non-group audio track and the file must exist on disk.

### Internal

- 71 tools (was 70).
- `create_arrangement_audio_clip` added to `WRITE_DISPATCH` (runs on Live's main thread) and to `MODIFYING_COMMANDS` in `ableton/connection.py`.
- New handler `ArrangementCommands._create_arrangement_audio_clip`. Falls back to locating the clip by start time if `create_audio_clip` returns `None`.
- Remote Script change: run `deploy.sh` / `deploy.ps1` and fully quit and relaunch Ableton. Toggling the control surface off and on re-runs the script's init but keeps the old modules cached, so new commands still return "Unknown command".

---

## [1.7.0] - 2026-10-19

### Added

**Nested device addressing**
- Device paths - a list alternating device and chain indices (`[device, chain, device, ...]`) that walks `rack.chains[c].devices[d]` to any depth. Unblocks devices inside sub-racks, e.g. a de-esser Compressor two levels down in a vocal processing rack, which no tool could previously read or set.
- `get_device_parameters_at_path(track_index, path, track_type)` - all parameters of the device at a path, with display strings, min/max display strings, `value_items` for quantized parameters, and a chain summary when the device is itself a rack.
- `set_device_parameter_at_path(track_index, path, value, param_index | param_name, track_type)` - set by parameter index or by name (case-insensitive exact match). Unknown names fail with suggestions, duplicate names fail and ask for an index, and a mismatched index/name pair is rejected. Returns the previous and new raw and display values.
- `track_type` (`"track"`, `"return"`, `"master"`) on the path tools and `get_rack_devices`, so return-track and master-track devices are reachable too.
- `tests/test_device_paths.py` - stdlib `unittest` suite with fake Live objects covering path resolution, name lookup and recursive rack listing. Run with `python3 -m unittest discover tests`.

### Changed

- `get_rack_devices` gains `depth` (default 1, the previous behaviour), `include_parameters` (default true) and `path` (start from a nested rack). Every listed device now includes its `path` and `can_have_chains`; racks at the depth limit report `chain_count`.
- Parameter listings from `get_device_parameters`, `get_rack_devices` and the new path tools add `display_value` (via `DeviceParameter.str_for_value`), `is_quantized`, and `value_items` for quantized parameters. `set_device_parameter` also returns `display_value`. All changes are additive; existing keys and arguments are unchanged.

### Internal

- 70 tools (was 68).
- `set_device_parameter_at_path` added to `MODIFYING_COMMANDS` in `ableton/connection.py` and to `WRITE_DISPATCH` (main thread); `get_device_parameters_at_path` added to `READ_DISPATCH`.
- New `DeviceCommands` helpers: `_resolve_track`, `_resolve_device_path`, `_param_display`, `_serialize_parameter`, `_find_parameter`.
- Remote Script change: run `deploy.sh` / `deploy.ps1` and restart Ableton.

---

## [1.6.0] - 2026-08-22

### Added

**macOS support**
- `deploy.sh` - macOS/Linux counterpart to `deploy.ps1`. Same three jobs (clear `__pycache__`, copy the 7 remote script files, sync server files to active Claude Code worktrees) with matching `--skip-ableton` / `--skip-worktrees` flags, plus `--help`.
- The macOS deploy target is `~/Music/Ableton/User Library/Remote Scripts/AbletonMCPLocal`. `deploy.sh` creates the `Remote Scripts` folder if Ableton has not made it yet.

### Changed

- **The "Windows only" claim is withdrawn.** The server and remote script were already platform-neutral - the transport is plain `socket.AF_INET`/`SOCK_STREAM` on `localhost:9877` with no platform APIs. Only the deploy script, the README and `.mcp.json` path syntax were Windows-specific. Verified working on macOS 15 with Ableton Live 12 Standard: all 68 tools register, and read, write and undo round-trip against a live session.
- `README.md` - platform requirements, project structure, clone step, deploy steps, both `.mcp.json` examples, the deploying-changes section and four troubleshooting references now cover Windows and macOS/Linux side by side.
- `AbletonMCPLocal/__init__.py` - the header comment now names both the macOS and Windows User Library paths.

### Fixed

- **Stale `uv.lock` version** - the lock file declared `version = "1.3.0"` while `pyproject.toml` declared `1.5.0`. Same drift that `93997b8` fixed once before; it regressed at v1.4.0.

### Internal

- No changes to `ableton/` or to any command handler. The 68-tool surface is untouched.
- Plugin URIs are portable across platforms - they derive from vendor and plugin names, not filesystem paths, so `query:Plugins#VST3:Valhalla%20DSP:ValhallaSupermassive` resolves identically on macOS and Windows.
- macOS exposes a third plugin format folder, `AUv2`, alongside `VST` and `VST3`. `_find_plugin_by_name` needs no change: `_PLUGIN_FORMAT_PRIORITY` ranks by substring, so the effective order becomes VST3, then VST, then AUv2 as the fallback bucket. VST3 still wins, and AU-only plugins stay reachable by name.

---

## [1.5.0] - 2026-05-09

### Added

**VST3 and VST2 plugin loading**
- `load_instrument_or_effect`, `load_browser_item`, and `load_effect_on_return_track` now fully support VST3 and VST2 plugins in addition to native Ableton effects. Pass the URI returned by `get_browser_items_at_path` (e.g. `query:Plugins#VST3:Valhalla%20DSP:ValhallaSupermassive`) and it loads correctly.
- When loading by plain plugin name (e.g. `ValhallaSupermassive`), VST3 is automatically preferred over VST2 if both are installed.

### Fixed

- **Main-thread timeout on plugin loading** - previously, any load command that targeted a VST3 or VST2 plugin caused a 10-second timeout and failed. Root cause: Ableton's plugin browser directory scan blocks the main thread, but the 10-second queue timeout expired before the scan finished. Fixed with a two-phase architecture: browser navigation now runs in the client thread (where it is fast), and only the final `load_item()` UI call is scheduled to the main thread.
- **Recursive browser search did not walk plugins** - `_find_browser_item_by_uri` previously only searched native Ableton categories (`audio_effects`, `instruments`, `midi_effects`, `sounds`, `drums`) and could not locate VST3 or VST2 items. Replaced the recursive full-tree walk with `_navigate_uri_directly`, which parses the URI structure (e.g. `query:Plugins#VST3:Vendor:PluginName`) and navigates directly to the item in O(depth) without scanning the entire plugin library.

### Internal

- Added `_navigate_uri_directly` to `BrowserCommands` - O(depth) URI parser covering all standard Live URI formats (`AudioFx`, `Plugins`, `LivePacks`, `M4L`, `Instruments`, `MidiEffects`, `Sounds`, `Drums`).
- Added `_find_plugin_by_name` and `_search_children_by_name` to `BrowserCommands` - name-based plugin search with configurable format priority (VST3 first, then VST).
- Added `LOAD_COMMANDS` frozenset and `_execute_browser_load` to `AbletonMCPLocal` - dedicated dispatch path for all browser load commands that separates navigation (client thread) from UI mutation (main thread).
- `load_browser_item` and `load_effect_on_return_track` removed from `WRITE_DISPATCH` and now handled exclusively by the `LOAD_COMMANDS` branch.

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
