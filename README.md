# AbletonMCP

Control Ableton Live through Claude using the Model Context Protocol (MCP).


## What it does

AbletonMCP connects Claude to a live Ableton session over a local socket connection. You can ask Claude to create tracks, write MIDI, load instruments, set tempo, control playback, and more - all executed directly in your Ableton session.

## Components

| File | Role |
|---|---|
| `server_arrangement.py` | MCP server - runs on your PC, Claude connects to this |
| `AbletonMCPArrangement/__init__.py` | Ableton Remote Script - runs inside Ableton Live |

## Requirements

- Ableton Live 12.2.7 or newer
- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

### 1. Install the Remote Script

Copy the `AbletonMCPArrangement` folder into your Ableton User Library:

```
C:\Users\[Username]\Documents\Ableton\User Library\Remote Scripts\
```

Then in Ableton: **Preferences → Link, Tempo & MIDI → Control Surface** - select `AbletonMCPArrangement` and set Input/Output to `None`.

**To reload the script after making changes (no full restart needed):**
1. Delete the `__pycache__` folder inside your deployed `AbletonMCPArrangement` folder
2. In Ableton Preferences, set the Control Surface to `None`, then back to `AbletonMCPArrangement`

### 2. Run the MCP server

```powershell
uv run --with mcp[cli] server_arrangement.py
```

### 3. Connect Claude Code

Create or edit the `.mcp.json` file in your project folder and add the following. Replace the path in the last `args` entry with the full path to where you saved `server_arrangement.py` on your machine:

```json
{
  "mcpServers": {
    "AbletonMCP": {
      "command": "uv",
      "args": ["run", "--with", "mcp[cli]", "C:\\Users\\[Username]\\path\\to\\server_arrangement.py"]
    }
  }
}
```

For example, if you saved the file to `C:\Users\John\Projects\AbletonMCP\server_arrangement.py`, the last arg would be:
```
"C:\\Users\\John\\Projects\\AbletonMCP\\server_arrangement.py"
```

> **Note:** Windows paths in JSON require double backslashes `\\` as shown above.

---

## Available tools

- `get_session_info` - inspect the current session (tracks, tempo, etc.)
- `get_track_info` - details about a specific track
- `create_midi_track` - add a new MIDI track
- `set_track_name` - rename a track
- `create_clip` - create a MIDI clip on a track
- `add_notes_to_clip` - write MIDI notes into a Session View clip
- `add_notes_to_arrangement_clip` - write MIDI notes into an Arrangement View clip
- `get_arrangement_clips` - list clips on a track in Arrangement View
- `set_clip_name` / `set_arrangement_clip_name` - rename clips
- `set_tempo` - change BPM
- `load_instrument_or_effect` - load a device onto a track
- `load_drum_kit` - load a drum rack and kit
- `get_browser_tree` / `get_browser_items_at_path` - browse Ableton's device library
- `fire_clip` / `stop_clip` - trigger or stop a clip
- `start_playback` / `stop_playback` - transport control

---

## Credits

This project is built on top of [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp) by [@ahujasid](https://github.com/ahujasid). The original project provides the core MCP server architecture and Ableton Remote Script foundation. This fork extends it with Arrangement View tooling.
