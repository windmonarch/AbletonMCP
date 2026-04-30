# AbletonMCP

Control Ableton Live through Claude using the Model Context Protocol (MCP).

## What it does

AbletonMCP connects Claude to a live Ableton session over a local socket connection. You can ask Claude to create tracks, write MIDI, load instruments, set tempo, control playback, and more — all executed directly in your Ableton session.

## Components

| File | Role |
|---|---|
| `server_arrangement.py` | MCP server — runs on your PC, Claude connects to this |
| `AbletonMCPArrangement/__init__.py` | Ableton Remote Script — runs inside Ableton Live |

## Available tools

- `get_session_info` — inspect the current session (tracks, tempo, etc.)
- `get_track_info` — details about a specific track
- `create_midi_track` — add a new MIDI track
- `set_track_name` — rename a track
- `create_clip` — create a MIDI clip on a track
- `add_notes_to_clip` — write MIDI notes into a Session View clip
- `add_notes_to_arrangement_clip` — write MIDI notes into an Arrangement View clip
- `get_arrangement_clips` — list clips on a track in Arrangement View
- `set_clip_name` / `set_arrangement_clip_name` — rename clips
- `set_tempo` — change BPM
- `load_instrument_or_effect` — load a device onto a track
- `load_drum_kit` — load a drum rack and kit
- `get_browser_tree` / `get_browser_items_at_path` — browse Ableton's device library
- `fire_clip` / `stop_clip` — trigger or stop a clip
- `start_playback` / `stop_playback` — transport control

## Setup

### 1. Install the Remote Script

Copy the `AbletonMCPArrangement` folder into Ableton's MIDI Remote Scripts directory:

```
C:\ProgramData\Ableton\Live 12\Resources\MIDI Remote Scripts\
```

Then in Ableton: **Preferences → MIDI → Control Surface** — select `AbletonMCPArrangement`.

### 2. Run the MCP server

Requires [uv](https://docs.astral.sh/uv/):

```powershell
uv run --with mcp[cli] server_arrangement.py
```

### 3. Connect Claude Code

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "AbletonMCP": {
      "command": "uv",
      "args": ["run", "--with", "mcp[cli]", "path\\to\\server_arrangement.py"]
    }
  }
}
```

## Requirements

- Ableton Live 11 or 12
- Python (via `uv`)
- Claude Code with MCP support
