---
name: ableton
description: >
  Control and interact with Ableton Live via the AbletonMCP server. Use this skill
  whenever the user wants to do anything in Ableton Live — reading their session,
  creating tracks, writing MIDI notes, placing clips in the Arrangement, setting
  tempo, renaming tracks, firing or stopping clips, loading instruments, effects or
  plugins (on tracks, return tracks or the Master), setting device parameters,
  sends and volumes, automation, scenes, locators, or controlling playback. Trigger
  this skill for any request that involves Ableton, Live, a DAW session, MIDI
  programming, beat making, mixing, or music production tasks that can be executed
  directly in the open Ableton session. Even vague requests like "add a kick
  pattern" or "what's in my session?" should use this skill.
---

# Ableton Live Control via AbletonMCP

Covers **AbletonMCP v1.12.0** (72 tools), the user's own fork for Live 12 on macOS.

## Installation Reference

| Component | Location |
|-----------|----------|
| Repo (MCP server + remote script) | `~/Library/CloudStorage/OneDrive-Personal/Claude/Code-macbook/MCP Server/Ableton MCP` |
| MCP server config | `.mcp.json` in the repo root (runs `server_arrangement.py` with `~/.local/bin/uv`) |
| Remote script (deployed) | `~/Music/Ableton/User Library/Remote Scripts/AbletonMCPLocal/` |
| Live log | `~/Library/Preferences/Ableton/Live <version>/Log.txt` |

After any remote-script change, run `./deploy.sh` in the repo, then **fully quit and relaunch Ableton**
(save the set first). Toggling the control surface is not enough: Python keeps the old modules, and new
commands fail with "Unknown command". After a server-side change, the MCP server must restart
(a new Claude session starts a fresh one).

---

You have direct, live access to the user's Ableton session. Changes take effect immediately.
`undo` exists, but read before you write, and confirm destructive actions (deleting tracks, clips,
devices or notes, overwriting clips) with the user first.

## Track addressing

- `track_index` counts regular tracks (groups included) from 0, as in `get_session_info`.
- Return tracks have their own index (0 = first return, e.g. A-ROOM).
- Many device tools take `track_type`: `"track"` (default), `"return"` or `"master"`. For `"master"`,
  `track_index` is ignored. Live 12 calls the Master track **"Main"**.

## Tools

### Session and transport
| Tool | What it does |
|------|-------------|
| `get_session_info` | Tempo, time signature, track count, master info |
| `get_track_info` | Name, type, mute/solo/arm, volume, pan, clip slots, devices |
| `set_tempo` / `set_time_signature` | Tempo (BPM) and time signature |
| `start_playback` / `stop_playback` | Transport |
| `get_current_song_time` / `jump_to_time` | Read or move the playhead (beats) |
| `undo` / `redo` | Live's undo history |

### Tracks and mixer
| Tool | What it does |
|------|-------------|
| `create_midi_track` / `create_audio_track` | Insert a track at an index (-1 = end) |
| `delete_track` / `duplicate_track` | Delete or duplicate a regular track |
| `set_track_name` / `set_track_color` | Rename or recolour |
| `set_track_mute` / `set_track_solo` / `set_track_arm` | Track switches |
| `set_track_volume` / `set_track_pan` | Mixer volume and pan (normalized values) |
| `get_track_sends` | Send levels, with `display_value` and `db` |
| `set_track_send` | Set a send by `db=` (preferred, exact) or raw `value=` |

### Return tracks
| Tool | What it does |
|------|-------------|
| `create_return_track` | Add a return (appended at the end) |
| `get_return_track_info` | Name, volume, pan, devices of a return |
| `set_return_track_name` | Rename a return |
| `load_effect_on_return_track` | Load onto a return (same as `load_instrument_or_effect` with `track_type="return"`) |

### Browser and loading
| Tool | What it does |
|------|-------------|
| `get_browser_tree` | Top-level browser categories |
| `get_browser_items_at_path` | List items at a path, e.g. `audio_effects`, `plugins/VST3/iZotope` |
| `load_instrument_or_effect` | Load by URI **or plain plugin name** onto a track, return or the Master (`track_type`) |
| `load_drum_kit` | Load a Drum Rack and a kit onto a track |

Loads append to the **end** of the target chain, so load a chain in signal-flow order.
A plain plugin name (e.g. `"Ozone Imager 2"`) is matched exactly, VST3 preferred over VST2.

### Devices
| Tool | What it does |
|------|-------------|
| `get_device_parameters` / `set_device_parameter` | Top-level device params on a regular track, by index |
| `get_rack_devices` | Devices inside a rack's chains (`depth`), each with its `path`; takes `track_type` |
| `get_device_parameters_at_path` | All params of any device, nested or not, with `display_value`; takes `track_type` |
| `set_device_parameter_at_path` | Set a param by `param_name` (case-insensitive exact) or index; takes `track_type` |
| `get_drum_pads` | Drum Rack pads with note and name |
| `delete_device` | Remove a device by index from a track, return or the Master (`track_type`) |

Device paths alternate device and chain indices: `[2]` = third device, `[0, 4, 0]` = rack 0 → chain 4 →
first device. Setters take the raw value and echo the new display value; read `display_value` to
report what Live shows.

### Session View clips and scenes
| Tool | What it does |
|------|-------------|
| `create_clip` / `add_notes_to_clip` / `set_clip_name` | Session clips |
| `fire_clip` / `stop_clip` | Launch or stop a slot |
| `get_scenes` / `create_scene` / `delete_scene` | Scenes |
| `fire_scene` / `set_scene_name` / `set_scene_tempo` | Scene launch, name, tempo |

### Arrangement View
| Tool | What it does |
|------|-------------|
| `get_arrangement_clips` | Clips on a track: start, length, name, `muted`, and `file_path` for audio |
| `create_arrangement_audio_clip` | Place an audio file at a beat position |
| `create_arrangement_midi_clip` | Create a MIDI clip, optionally with notes |
| `add_notes_to_arrangement_clip` / `get_clip_notes` / `remove_notes_from_clip` | MIDI notes |
| `set_arrangement_clip_name` / `set_clip_color` / `set_clip_mute` | Clip name, colour, mute |
| `set_clip_pitch` / `set_clip_gain` / `set_clip_markers` | Transpose, audio gain, start/end markers |
| `quantize_clip` / `duplicate_clip_loop` | Quantize notes; double the loop |
| `get_cue_points` / `create_cue_point` / `delete_cue_point` / `set_cue_point_name` / `jump_to_cue` | Locators |

### Clip automation
| Tool | What it does |
|------|-------------|
| `get_clip_envelope` / `set_clip_envelope_point` | Read or add automation for a device parameter in a clip |
| `clear_clip_envelope` / `clear_clip_envelopes` | Clear one or all envelopes in a clip |

## Working conventions

- **Positions:** the MCP uses beats; tell the user Live's bar.beat.sixteenth (4/4: bar = floor(beat/4)+1,
  beat = beat mod 4 + 1). Beat 204 → **52.1.1**.
- **Sends:** always give and set send levels in dB (`set_track_send(db=-22)`), never the 0–1 knob value.
  The taper is steep: 0.10 is about -54.6 dB.
- **Orient first:** `get_session_info`, then `get_track_info` for any track you'll touch. Match tracks
  by name, not just index.
- **Report back clearly:** say exactly what was created or changed, and where to look in Live.

## Known caveats (verify before reporting)

1. `get_clip_notes` can return the clip open in Live's detail view instead of the addressed one.
   Cross-check with a second read, and trust it only when the target clip is open.
2. A plugin showing only `Device On` has not failed to load: Live auto-exposes params only for some
   plugins. Load status can only be confirmed visually.
3. `remove_notes_from_clip` can report "No data received" on success. Re-read the clip.
4. Arrangement clip indices shift when clips are added earlier on a track. Locate a clip by
   `start_time` from a fresh `get_arrangement_clips` read just before writing.
5. Arrangement MIDI note times are relative to the clip start, not song position, and the MCP can't
   read a clip's start marker. Don't report timing errors derived from clip start + offset as fact.
6. Compressor gain reduction can't be read. Set a starting threshold and ask the user to read the needle.
7. Inserting a track at the index right after a group's **last** member puts it outside the group.
   Insert before the last member instead, and check with a screenshot. The MCP can't report group
   membership or create groups (the user presses Cmd+G).
8. No sidechain routing: `S/C On` can be set, but the source (Audio From) must be chosen by the user.

## MIDI reference

Pitches 0–127; C0 = 12, middle C (C4) = 60, each semitone +1. GM drums: Kick 36, Snare 38, Clap 39,
Closed HH 42, Open HH 46. Velocity 0–127 (64 medium, 100 strong); vary it slightly for feel.
Notes need `pitch`, `start_time` (beats), `duration` (beats), `velocity`. Clip `length` is in beats
(4.0 = one 4/4 bar).
