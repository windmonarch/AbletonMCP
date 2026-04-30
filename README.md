# AbletonMCP

Control Ableton Live through Claude using the Model Context Protocol (MCP).

## What it does

AbletonMCP connects Claude to a live Ableton session over a local socket connection. You can ask Claude to create tracks, write MIDI, load instruments, set tempo, control playback, and more - all executed directly in your open Ableton session in real time.

This fork extends the original [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp) with full **Arrangement View** support.

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
├── ableton\
│   ├── connection.py            - TCP connection to Ableton
│   ├── tools_session.py         - Session View + global MCP tools
│   ├── tools_arrangement.py     - Arrangement View MCP tools
│   ├── tools_browser.py         - Browser MCP tools
│   └── tools_devices.py         - Device and drum pad MCP tools
└── AbletonMCPArrangement\
    ├── __init__.py              - Ableton Remote Script entry point
    ├── commands_session.py      - Session View command handlers
    ├── commands_arrangement.py  - Arrangement View command handlers
    ├── commands_browser.py      - Browser command handlers
    └── commands_devices.py      - Device and drum pad command handlers
```

The MCP server (`server_arrangement.py` + `ableton/`) runs on your PC and Claude connects to it. The Remote Script (`AbletonMCPArrangement/`) runs inside Ableton Live and receives commands over a local socket on port 9877.

---

## Setup

### Step 1 - Clone the repo

Clone this repo to your PC. This gives you both folders:

- `ableton/` - the MCP server package, stays where you cloned it and runs on your PC
- `AbletonMCPArrangement/` - the Ableton Remote Script, needs to be copied into Ableton in Step 2

```powershell
git clone https://github.com/windmonarch/AbletonMCP
```

### Step 2 - Install the Remote Script

Copy the entire `AbletonMCPArrangement` folder (all 5 files) into your Ableton User Library:

```
C:\Users\[Username]\Documents\Ableton\User Library\Remote Scripts\AbletonMCPArrangement\
```

The folder must contain all five files:
- `__init__.py`
- `commands_session.py`
- `commands_arrangement.py`
- `commands_browser.py`
- `commands_devices.py`

> **Important:** Ableton scans `Documents\Ableton\User Library\Remote Scripts`. Do NOT deploy to the AppData path - Ableton does not scan it.

Then in Ableton: **Preferences -> Link, Tempo & MIDI -> Control Surface** - select `AbletonMCPArrangement` and set Input and Output to `None`.

### Step 3 - Configure Claude Code

Create a `.mcp.json` file inside the cloned repo folder. Replace the path in `cwd` with the actual path to where you cloned the repo on your machine:

```json
{
  "mcpServers": {
    "AbletonMCP": {
      "command": "uv",
      "args": ["run", "--with", "mcp[cli]", "server_arrangement.py"],
      "cwd": "C:\\Users\\[Username]\\path\\to\\AbletonMCP"
    }
  }
}
```

For example, if you cloned to `C:\Users\John\Projects\AbletonMCP`:

```json
{
  "mcpServers": {
    "AbletonMCP": {
      "command": "uv",
      "args": ["run", "--with", "mcp[cli]", "server_arrangement.py"],
      "cwd": "C:\\Users\\John\\Projects\\AbletonMCP"
    }
  }
}
```

> **Note:** Windows paths in JSON require double backslashes `\\`. The `cwd` field is required - without it `uv` may not find the correct project files.

### Step 4 - Start Claude Code

Launch Claude Code from your project folder. It will automatically start the MCP server using the `.mcp.json` config. You should see the Ableton tools available in your Claude session.

Make sure Ableton is open with the `AbletonMCPArrangement` control surface active before starting Claude Code.

---

## Available tools

### Session info
| Tool | What it does |
|---|---|
| `get_session_info` | Tempo, time signature, track count, master track info |
| `get_current_song_time` | Current playhead position in beats |
| `get_cue_points` | List all cue points with their names and positions |
| `jump_to_cue` | Jump to the next or previous cue point |

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

### Session View clips
| Tool | What it does |
|---|---|
| `create_clip` | Create an empty MIDI clip in a Session View slot |
| `add_notes_to_clip` | Write MIDI notes into a Session View clip |
| `set_clip_name` | Rename a Session View clip |
| `fire_clip` | Launch a Session View clip |
| `stop_clip` | Stop a playing Session View clip |

### Devices
| Tool | What it does |
|---|---|
| `get_device_parameters` | List all parameters for a device on a track |
| `set_device_parameter` | Set a device parameter value by parameter index |
| `delete_device` | Remove a device from a track by index |
| `get_drum_pads` | List all pads in a Drum Rack with their note and name |

### Browser
| Tool | What it does |
|---|---|
| `get_browser_tree` | Browse available instruments, effects, and samples |
| `get_browser_items_at_path` | List items at a specific browser path |
| `load_instrument_or_effect` | Load a device onto a track by URI |
| `load_drum_kit` | Load a drum rack and kit onto a track |

### Live API limitations

These operations are not possible via the Live Python API and must be done manually:

- **Creating an arrangement clip** - double-click in the Arrangement View to draw a clip
- **Deleting an arrangement clip** - select the clip and press Delete
- **Deleting a return track** - right-click the return track header and select Delete

---

## Troubleshooting

### Remote script changes not taking effect

If you have modified the remote script files and Ableton is not picking up your changes:

1. Delete the `__pycache__` folder inside the deployed `AbletonMCPArrangement` folder
2. Copy the updated files from the repo to the deployed folder
3. In Ableton Preferences, set the Control Surface to `None`, then back to `AbletonMCPArrangement`

Ableton caches compiled bytecode - if you skip step 1, your changes will be ignored.

### MCP server fails to start

Make sure:
- `uv` is installed and available on your PATH
- The `cwd` in `.mcp.json` points to the correct folder (where `pyproject.toml` lives)
- You are running Python 3.12 or newer (`uv python list` to check)

### Claude cannot connect to Ableton

Make sure:
- Ableton is open and `AbletonMCPArrangement` is selected as the Control Surface
- No other application is using port 9877
- The `__pycache__` in the deployed folder is not stale (delete it and reload the surface if unsure)

---

## Credits

Built on top of [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp) by [@ahujasid](https://github.com/ahujasid). The original project provides the core MCP server architecture and Ableton Remote Script foundation. This fork extends it with Arrangement View tooling and a refactored multi-file structure.
