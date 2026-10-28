# AbletonMCP

Control Ableton Live through Claude using the Model Context Protocol (MCP).

## What it does

AbletonMCP connects Claude to a live Ableton session over a local socket connection. You can ask Claude to create tracks, write MIDI, load instruments, set tempo, control playback, manage scenes, automate parameters, and more - all executed directly in your open Ableton session in real time.

---

## Requirements

- Windows or macOS
- Ableton Live 12.2.7 or newer
- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) package manager
- [Claude Code](https://claude.ai/code) - requires MCP protocol support, which is only available in Claude Code. Does not work with Claude.ai or any other Claude interface.

---

## Project structure

```
AbletonMCP\
├── server_arrangement.py        - MCP server entry point
├── deploy.ps1                   - Deploy script, Windows (copies files to Ableton + Claude Code worktrees)
├── deploy.sh                    - Deploy script, macOS/Linux (same job)
├── ableton\
│   ├── connection.py            - TCP connection to Ableton
│   ├── tools_session.py         - Session + global MCP tools
│   ├── tools_arrangement.py     - Arrangement View MCP tools
│   ├── tools_browser.py         - Browser MCP tools
│   ├── tools_devices.py         - Device and drum pad MCP tools
│   ├── tools_scenes.py          - Scene management MCP tools
│   └── tools_automation.py      - Clip automation envelope MCP tools
└── AbletonMCPLocal\
    ├── __init__.py              - Ableton Remote Script entry point
    ├── commands_session.py      - Session command handlers
    ├── commands_arrangement.py  - Arrangement View command handlers
    ├── commands_browser.py      - Browser command handlers
    ├── commands_devices.py      - Device command handlers
    ├── commands_scenes.py       - Scene command handlers
    └── commands_automation.py   - Automation envelope command handlers
└── tests\
    └── test_device_paths.py     - Offline tests for device-path commands (fake Live objects)
```

The MCP server (`server_arrangement.py` + `ableton/`) runs on your PC and Claude connects to it. The Remote Script (`AbletonMCPLocal/`) runs inside Ableton Live and receives commands over a local socket on port 9877.

---

## Setup

### Step 1 - Clone the repo

Clone this repo to the machine running Ableton. This gives you both folders:

- `ableton/` - the MCP server package, stays where you cloned it and runs on your machine
- `AbletonMCPLocal/` - the Ableton Remote Script, needs to be copied into Ableton in Step 2

```bash
git clone https://github.com/windmonarch/AbletonMCP
```

### Step 2 - Install the Remote Script

Run the deploy script from the repo folder.

**Windows:**

```powershell
.\deploy.ps1
```

**macOS / Linux:**

```bash
./deploy.sh
```

This automatically copies all 7 remote script files to your Ableton User Library at:

```
Windows:  C:\Users\[Username]\Documents\Ableton\User Library\Remote Scripts\AbletonMCPLocal\
macOS:    ~/Music/Ableton/User Library/Remote Scripts/AbletonMCPLocal/
```

> **Important:** Ableton scans the **User Library**. On Windows do NOT deploy to the AppData path, and on macOS do NOT deploy to `~/Library/Application Support` - Ableton does not scan either. On macOS the `Remote Scripts` folder may not exist yet; `deploy.sh` creates it for you.

If you prefer to copy manually, paste the entire `AbletonMCPLocal` folder (all 7 files) into the path above.

Then in Ableton: **Preferences -> Link, Tempo & MIDI -> Control Surface** - select `AbletonMCPLocal` and set Input and Output to `None`.

### Step 3 - Configure Claude Code

Create a `.mcp.json` file inside the cloned repo folder. Use the full absolute path to `server_arrangement.py` in both `args` and `cwd`, replacing the example path with wherever you cloned the repo:

**Windows:**

```json
{
  "mcpServers": {
    "AbletonMCP": {
      "command": "uv",
      "args": ["run", "--with", "mcp[cli]", "C:\\Users\\John\\Projects\\AbletonMCP\\server_arrangement.py"],
      "cwd": "C:\\Users\\John\\Projects\\AbletonMCP"
    }
  }
}
```

**macOS / Linux:**

```json
{
  "mcpServers": {
    "AbletonMCP": {
      "command": "uv",
      "args": ["run", "--with", "mcp[cli]", "/Users/john/Projects/AbletonMCP/server_arrangement.py"],
      "cwd": "/Users/john/Projects/AbletonMCP"
    }
  }
}
```

> **Note:** Windows paths in JSON require double backslashes `\\`; POSIX paths use forward slashes as-is. Use an absolute path for the script in `args` - this prevents Claude Code from accidentally running a stale copy from a git worktree.
>
> If `uv` is not on the PATH that Claude Code inherits, use its absolute path as `command` (for example `/Users/john/.local/bin/uv`).

### Step 4 - Start Claude Code

Launch Claude Code from your project folder. It will automatically start the MCP server using the `.mcp.json` config. You should see the Ableton tools available in your Claude session.

Make sure Ableton is open with the `AbletonMCPLocal` control surface active before starting Claude Code.

---

## Available tools

### Session info
| Tool | What it does |
|---|---|
| `get_session_info` | Tempo, time signature, track count, master track info |
| `get_current_song_time` | Current playhead position in beats |
| `get_cue_points` | List all cue points with their names and positions |
| `jump_to_cue` | Jump to the next or previous cue point |
| `set_time_signature` | Set session time signature (e.g. 3/4, 6/8) |
| `jump_to_time` | Move playhead to a specific beat position |

### Tracks
| Tool | What it does |
|---|---|
| `get_track_info` | Name, type, mute/solo/arm, volume, panning, devices |
| `create_midi_track` | Add a new MIDI track at a given index (-1 = end) |
| `create_audio_track` | Add a new audio track at a given index (-1 = end) |
| `create_return_track` | Add a new return track |
| `delete_track` | Delete a track by index (MIDI and audio tracks only) |
| `duplicate_track` | Duplicate a track by index |
| `set_track_name` | Rename a track |
| `set_track_color` | Set a track's color by RGB integer |
| `set_track_mute` | Mute or unmute a track |
| `set_track_solo` | Solo or unsolo a track |
| `set_track_arm` | Arm or disarm a track for recording |
| `set_track_volume` | Set track volume (0.0 to 1.0) |
| `set_track_pan` | Set track panning (-1.0 left to 1.0 right) |
| `get_track_sends` | List all send amounts for a track |
| `set_track_send` | Set a send amount for a track to a return track |

### Playback
| Tool | What it does |
|---|---|
| `start_playback` | Press Play |
| `stop_playback` | Press Stop |
| `set_tempo` | Change session tempo (BPM) |

### History
| Tool | What it does |
|---|---|
| `undo` | Undo the last action |
| `redo` | Redo the last undone action |

### Arrangement View clips
| Tool | What it does |
|---|---|
| `get_arrangement_clips` | List all clips on a track in the Arrangement View, with position, length, mute state and (audio) source file |
| `add_notes_to_arrangement_clip` | Write MIDI notes into an Arrangement View clip |
| `set_arrangement_clip_name` | Rename an Arrangement View clip |
| `create_arrangement_audio_clip` | Place an audio file as a clip on an audio track at a beat position (Live 12+) |
| `create_arrangement_midi_clip` | Create a MIDI clip on a MIDI track at a beat position, optionally with notes (Live 12+) |
| `get_clip_notes` | Read back all MIDI notes from an Arrangement View clip |
| `remove_notes_from_clip` | Clear all notes from an Arrangement View clip |
| `set_clip_color` | Set a clip's color by RGB integer |
| `set_clip_pitch` | Set coarse and fine pitch of an audio clip |
| `set_clip_gain` | Set the gain of an audio clip (0.0 to 1.0) |
| `set_clip_markers` | Set the start and end loop markers on a clip |
| `quantize_clip` | Quantize MIDI notes to a grid (bar, 1/2, 1/4, 1/8, 1/16, 1/32) |
| `duplicate_clip_loop` | Double a clip's loop length by duplicating its content |
| `set_clip_mute` | Mute or unmute a clip |
| `clear_clip_envelopes` | Remove all automation envelopes from a clip |

### Session View clips
| Tool | What it does |
|---|---|
| `create_clip` | Create an empty MIDI clip in a Session View slot |
| `add_notes_to_clip` | Write MIDI notes into a Session View clip |
| `set_clip_name` | Rename a Session View clip |
| `fire_clip` | Launch a Session View clip |
| `stop_clip` | Stop a playing Session View clip |

### Scenes
| Tool | What it does |
|---|---|
| `get_scenes` | List all scenes with name and tempo |
| `create_scene` | Add a new scene at a given index (-1 = end) |
| `delete_scene` | Remove a scene by index |
| `fire_scene` | Launch all clips in a scene |
| `set_scene_name` | Rename a scene |
| `set_scene_tempo` | Assign a tempo to a scene (0.0 = clear) |

### Cue points
| Tool | What it does |
|---|---|
| `create_cue_point` | Create a locator at a specific beat position |
| `delete_cue_point` | Remove a locator by index |
| `set_cue_point_name` | Rename a locator |

### Return tracks
| Tool | What it does |
|---|---|
| `get_return_track_info` | Name, volume, panning, and devices for a return track |
| `set_return_track_name` | Rename a return track |
| `load_effect_on_return_track` | Load a native effect or VST3/VST2 plugin onto a return track by URI |

Return tracks use a separate index (0 = first return track, e.g. A-Reverb). They are accessed via `song.return_tracks[]`, not `song.tracks[]`.

### Devices
| Tool | What it does |
|---|---|
| `get_device_parameters` | List all parameters for a device on a track |
| `set_device_parameter` | Set a device parameter value by parameter index |
| `delete_device` | Remove a device from a track by index |
| `get_drum_pads` | List all pads in a Drum Rack with their note and name |
| `get_rack_devices` | List devices inside a rack's chains, optionally recursing into nested racks (`depth`); every device carries its `path` |
| `get_device_parameters_at_path` | List all parameters of any device, including ones nested inside racks, addressed by device path |
| `set_device_parameter_at_path` | Set a parameter on any device by device path, by parameter name or index |

Parameter listings include `display_value` (as Live shows it, e.g. `4.00 : 1`, `50.0 ms`, `6.00 kHz`) alongside the raw `value`. Setters take the raw value and echo the new display value back.

**Device paths**

Devices nested inside racks are addressed by a path that alternates device and chain indices, starting and ending on a device:

| Path | Device |
|---|---|
| `[2]` | Third top-level device on the track |
| `[0, 4, 0]` | Rack at device 0 → chain 4 → first device |
| `[0, 0, 4, 0, 0]` | Rack at device 0 → chain 0 → sub-rack 4 → its chain 0 → first device |

Find paths with `get_rack_devices(track_index, device_index, depth=2, include_parameters=False)`, then read or set:

```
get_device_parameters_at_path(track_index=3, path=[0, 0, 4, 0, 0])
set_device_parameter_at_path(track_index=3, path=[0, 0, 4, 0, 0], param_name="Ratio", value=0.6)
```

`param_name` is a case-insensitive exact match. An unknown or ambiguous name is an error (with suggestions), never a guess. The path tools and `get_rack_devices` also take `track_type="return"` or `"master"` to reach return-track and master-track devices.

### Browser
| Tool | What it does |
|---|---|
| `get_browser_tree` | Browse available instruments, effects, samples, and plugins |
| `get_browser_items_at_path` | List items at a specific browser path (supports `plugins/VST3`, `plugins/VST`, `audio_effects`, `instruments`, `packs`, etc.) |
| `load_instrument_or_effect` | Load a native effect or VST3/VST2 plugin onto a track by URI |
| `load_drum_kit` | Load a drum rack and kit onto a track |

**Loading VST3 and VST2 plugins**

Use `get_browser_items_at_path` to find the exact URI for any plugin, then pass it to a load tool:

```
get_browser_items_at_path("plugins/VST3/Valhalla DSP")
-> returns URI: query:Plugins#VST3:Valhalla%20DSP:ValhallaSupermassive

load_instrument_or_effect(track_index=0, item_uri="query:Plugins#VST3:Valhalla%20DSP:ValhallaSupermassive")
```

VST3 is always preferred over VST2 when loading by plugin name. Both formats work with `load_instrument_or_effect`, `load_drum_kit`, and `load_effect_on_return_track`.

### Clip automation envelopes
| Tool | What it does |
|---|---|
| `get_clip_envelope` | Read automation points for a device parameter in a clip |
| `set_clip_envelope_point` | Insert an automation breakpoint into a clip envelope |
| `clear_clip_envelope` | Clear automation for a specific device parameter in a clip |

### Live API limitations

These operations are not possible via the Live Python API and must be done manually:

- **Creating arrangement clips on Live 11 or earlier** - double-click in the Arrangement View to draw a clip. On Live 12+, use `create_arrangement_midi_clip` and `create_arrangement_audio_clip`.
- **Deleting an arrangement clip** - select the clip and press Delete
- **Deleting a return track** - right-click the return track header and select Delete
- **Creating new clip automation envelopes on arrangement clips** - `set_clip_envelope_point` requires an existing envelope. Right-click the parameter in Ableton and choose Show Automation in Clip to draw the first breakpoint manually, then the tool can insert additional points.

---

## Deploying changes

If you modify any server or remote script files, run the deploy script from the project root to push all changes to the right places:

```powershell
.\deploy.ps1     # Windows
```

```bash
./deploy.sh      # macOS / Linux
```

This script:
1. Deletes `__pycache__` in the Ableton deployed folder and copies all 7 remote script files there
2. Syncs `ableton/*.py` and `server_arrangement.py` to all active Claude Code worktrees

After running, restart Ableton to pick up remote script changes. Claude Code reconnects automatically on next use.

---

## Troubleshooting

### Remote script changes not taking effect

If you have modified the remote script files and Ableton is not picking up your changes:

1. Run the deploy script (`.\deploy.ps1` on Windows, `./deploy.sh` on macOS/Linux) to copy files and clear `__pycache__`
2. Do a full Ableton restart

Ableton caches compiled bytecode in `__pycache__` and also caches modules in `sys.modules` at runtime. Toggling the control surface to None and back is not sufficient to clear either cache - only a full restart picks up changes to `.py` files.

### New MCP tools not appearing in Claude Code

Claude Code creates git worktrees when opening a project. The MCP server may be running from a worktree directory that has stale copies of the server files. Run the deploy script to sync all server files to all active worktrees, then restart Claude Code.

The `.mcp.json` uses an absolute path for the server script to help prevent this, but the worktree sync is the reliable fix if tools are missing.

### MCP server fails to start

Make sure:
- `uv` is installed and available on your PATH (or `command` in `.mcp.json` uses its absolute path)
- The `cwd` in `.mcp.json` points to the correct folder (where `pyproject.toml` lives)
- You are running Python 3.12 or newer (`uv python list` to check)

### Claude cannot connect to Ableton

Make sure:
- Ableton is open and `AbletonMCPLocal` is selected as the Control Surface
- No other application is using port 9877
- The `__pycache__` in the deployed folder is not stale (run the deploy script and restart Ableton)

---

## Credits

Built on top of [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp) by [@ahujasid](https://github.com/ahujasid).

All Ableton Live integration is built against the [Ableton Live Object Model](https://structure.uniqpath.com/ableton/live-object-model) - the Python API that Live exposes to Remote Scripts.

MCP server built with the [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk).
