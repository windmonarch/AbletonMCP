# AbletonMCP

Control Ableton Live through Claude using the Model Context Protocol (MCP).

## What it does

AbletonMCP connects Claude to a live Ableton session over a local socket connection. You can ask Claude to create tracks, write MIDI, load instruments, set tempo, control playback, manage scenes, automate parameters, and more - all executed directly in your open Ableton session in real time.

---

## Requirements

- Windows only - macOS and Linux are not supported
- Ableton Live 12.2.7 or newer
- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) package manager
- [Claude Code](https://claude.ai/code) - requires MCP protocol support, which is only available in Claude Code. Does not work with Claude.ai or any other Claude interface.

---

## Project structure

```
AbletonMCP\
├── server_arrangement.py        - MCP server entry point
├── deploy.ps1                   - Deploy script (copies files to Ableton + Claude Code worktrees)
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
```

The MCP server (`server_arrangement.py` + `ableton/`) runs on your PC and Claude connects to it. The Remote Script (`AbletonMCPLocal/`) runs inside Ableton Live and receives commands over a local socket on port 9877.

---

## Setup

### Step 1 - Clone the repo

Clone this repo to your PC. This gives you both folders:

- `ableton/` - the MCP server package, stays where you cloned it and runs on your PC
- `AbletonMCPLocal/` - the Ableton Remote Script, needs to be copied into Ableton in Step 2

```powershell
git clone https://github.com/windmonarch/AbletonMCP
```

### Step 2 - Install the Remote Script

Run the deploy script from the repo folder:

```powershell
.\deploy.ps1
```

This automatically copies all 7 remote script files to your Ableton User Library at:

```
C:\Users\[Username]\Documents\Ableton\User Library\Remote Scripts\AbletonMCPLocal\
```

> **Important:** Ableton scans `Documents\Ableton\User Library\Remote Scripts`. Do NOT deploy to the AppData path - Ableton does not scan it.

If you prefer to copy manually, paste the entire `AbletonMCPLocal` folder (all 7 files) into the path above.

Then in Ableton: **Preferences -> Link, Tempo & MIDI -> Control Surface** - select `AbletonMCPLocal` and set Input and Output to `None`.

### Step 3 - Configure Claude Code

Create a `.mcp.json` file inside the cloned repo folder. Use the full absolute path to `server_arrangement.py` in both `args` and `cwd`, replacing the example path with wherever you cloned the repo:

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

> **Note:** Windows paths in JSON require double backslashes `\\`. Use an absolute path for the script in `args` - this prevents Claude Code from accidentally running a stale copy from a git worktree.

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
| `get_arrangement_clips` | List all clips on a track in the Arrangement View |
| `add_notes_to_arrangement_clip` | Write MIDI notes into an Arrangement View clip |
| `set_arrangement_clip_name` | Rename an Arrangement View clip |
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
| `load_effect_on_return_track` | Load a plugin or effect onto a return track by URI |

Return tracks use a separate index (0 = first return track, e.g. A-Reverb). They are accessed via `song.return_tracks[]`, not `song.tracks[]`.

### Devices
| Tool | What it does |
|---|---|
| `get_device_parameters` | List all parameters for a device on a track |
| `set_device_parameter` | Set a device parameter value by parameter index |
| `delete_device` | Remove a device from a track by index |
| `get_drum_pads` | List all pads in a Drum Rack with their note and name |
| `get_rack_devices` | List all devices nested inside a rack's chains (Audio Effect Rack, Instrument Rack, etc.) |

### Browser
| Tool | What it does |
|---|---|
| `get_browser_tree` | Browse available instruments, effects, and samples |
| `get_browser_items_at_path` | List items at a specific browser path |
| `load_instrument_or_effect` | Load a device onto a track by URI |
| `load_drum_kit` | Load a drum rack and kit onto a track |

### Clip automation envelopes
| Tool | What it does |
|---|---|
| `get_clip_envelope` | Read automation points for a device parameter in a clip |
| `set_clip_envelope_point` | Insert an automation breakpoint into a clip envelope |
| `clear_clip_envelope` | Clear automation for a specific device parameter in a clip |

### Live API limitations

These operations are not possible via the Live Python API and must be done manually:

- **Creating an arrangement clip** - double-click in the Arrangement View to draw a clip
- **Deleting an arrangement clip** - select the clip and press Delete
- **Deleting a return track** - right-click the return track header and select Delete
- **Creating new clip automation envelopes on arrangement clips** - `set_clip_envelope_point` requires an existing envelope. Right-click the parameter in Ableton and choose Show Automation in Clip to draw the first breakpoint manually, then the tool can insert additional points.

---

## Deploying changes

If you modify any server or remote script files, run `deploy.ps1` from the project root to push all changes to the right places:

```powershell
.\deploy.ps1
```

This script:
1. Deletes `__pycache__` in the Ableton deployed folder and copies all 7 remote script files there
2. Syncs `ableton/*.py` and `server_arrangement.py` to all active Claude Code worktrees

After running, restart Ableton to pick up remote script changes. Claude Code reconnects automatically on next use.

---

## Troubleshooting

### Remote script changes not taking effect

If you have modified the remote script files and Ableton is not picking up your changes:

1. Run `.\deploy.ps1` to copy files and clear `__pycache__`
2. Do a full Ableton restart

Ableton caches compiled bytecode in `__pycache__` and also caches modules in `sys.modules` at runtime. Toggling the control surface to None and back is not sufficient to clear either cache - only a full restart picks up changes to `.py` files.

### New MCP tools not appearing in Claude Code

Claude Code creates git worktrees when opening a project. The MCP server may be running from a worktree directory that has stale copies of the server files. Run `.\deploy.ps1` to sync all server files to all active worktrees, then restart Claude Code.

The `.mcp.json` uses an absolute path for the server script to help prevent this, but the worktree sync is the reliable fix if tools are missing.

### MCP server fails to start

Make sure:
- `uv` is installed and available on your PATH
- The `cwd` in `.mcp.json` points to the correct folder (where `pyproject.toml` lives)
- You are running Python 3.12 or newer (`uv python list` to check)

### Claude cannot connect to Ableton

Make sure:
- Ableton is open and `AbletonMCPLocal` is selected as the Control Surface
- No other application is using port 9877
- The `__pycache__` in the deployed folder is not stale (run `.\deploy.ps1` and restart Ableton)

---

## Credits

Built on top of [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp) by [@ahujasid](https://github.com/ahujasid).

All Ableton Live integration is built against the [Ableton Live Object Model](https://structure.uniqpath.com/ableton/live-object-model) - the Python API that Live exposes to Remote Scripts.

MCP server built with the [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk).
