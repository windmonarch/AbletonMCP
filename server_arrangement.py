# server_arrangement.py
# Extended AbletonMCP server with Arrangement View tools.
# Run via: uv run --with mcp[cli] python server_arrangement.py
from mcp.server.fastmcp import FastMCP, Context
import socket
import json
import logging
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List, Union

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AbletonMCPServer")

@dataclass
class AbletonConnection:
    host: str
    port: int
    sock: socket.socket = None

    def connect(self) -> bool:
        if self.sock:
            return True
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Ableton at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ableton: {str(e)}")
            self.sock = None
            return False

    def disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting: {str(e)}")
            finally:
                self.sock = None

    def receive_full_response(self, sock, buffer_size=8192):
        chunks = []
        sock.settimeout(15.0)
        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        if not chunks:
                            raise Exception("Connection closed before receiving any data")
                        break
                    chunks.append(chunk)
                    try:
                        data = b''.join(chunks)
                        json.loads(data.decode('utf-8'))
                        return data
                    except json.JSONDecodeError:
                        continue
                except socket.timeout:
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error(f"Socket connection error during receive: {str(e)}")
                    raise
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise
        if chunks:
            data = b''.join(chunks)
            try:
                json.loads(data.decode('utf-8'))
                return data
            except json.JSONDecodeError:
                raise Exception("Incomplete JSON response received")
        else:
            raise Exception("No data received")

    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Ableton")
        command = {"type": command_type, "params": params or {}}
        is_modifying = command_type in [
            "create_midi_track", "create_audio_track", "set_track_name",
            "create_clip", "add_notes_to_clip", "set_clip_name",
            "set_tempo", "fire_clip", "stop_clip", "set_device_parameter",
            "start_playback", "stop_playback", "load_instrument_or_effect",
            "add_notes_to_arrangement_clip",
            "set_arrangement_clip_name",
        ]
        try:
            logger.info(f"Sending command: {command_type} with params: {params}")
            self.sock.sendall(json.dumps(command).encode('utf-8'))
            if is_modifying:
                import time; time.sleep(0.1)
            self.sock.settimeout(15.0 if is_modifying else 10.0)
            response_data = self.receive_full_response(self.sock)
            response = json.loads(response_data.decode('utf-8'))
            if response.get("status") == "error":
                raise Exception(response.get("message", "Unknown error from Ableton"))
            if is_modifying:
                import time; time.sleep(0.1)
            return response.get("result", {})
        except socket.timeout:
            self.sock = None
            raise Exception("Timeout waiting for Ableton response")
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            self.sock = None
            raise Exception(f"Connection to Ableton lost: {str(e)}")
        except json.JSONDecodeError as e:
            self.sock = None
            raise Exception(f"Invalid response from Ableton: {str(e)}")
        except Exception as e:
            self.sock = None
            raise Exception(f"Communication error with Ableton: {str(e)}")


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    try:
        logger.info("AbletonMCP server starting up")
        try:
            get_ableton_connection()
            logger.info("Connected to Ableton on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Ableton on startup: {str(e)}")
        yield {}
    finally:
        global _ableton_connection
        if _ableton_connection:
            _ableton_connection.disconnect()
            _ableton_connection = None
        logger.info("AbletonMCP server shut down")


mcp = FastMCP("AbletonMCP", lifespan=server_lifespan)
_ableton_connection = None


def get_ableton_connection():
    global _ableton_connection
    if _ableton_connection is not None:
        try:
            _ableton_connection.sock.settimeout(1.0)
            _ableton_connection.sock.sendall(b'')
            return _ableton_connection
        except Exception:
            try:
                _ableton_connection.disconnect()
            except:
                pass
            _ableton_connection = None

    for attempt in range(1, 4):
        try:
            logger.info(f"Connecting to Ableton (attempt {attempt}/3)...")
            _ableton_connection = AbletonConnection(host="localhost", port=9877)
            if _ableton_connection.connect():
                _ableton_connection.send_command("get_session_info")
                logger.info("Connection validated")
                return _ableton_connection
            else:
                _ableton_connection = None
        except Exception as e:
            logger.error(f"Attempt {attempt} failed: {str(e)}")
            if _ableton_connection:
                _ableton_connection.disconnect()
                _ableton_connection = None
        if attempt < 3:
            import time; time.sleep(1.0)

    raise Exception("Could not connect to Ableton. Make sure the Remote Script is running.")


# =============================================================================
# Existing tools (unchanged behaviour)
# =============================================================================

@mcp.tool()
def get_session_info(ctx: Context) -> str:
    """Get detailed information about the current Ableton session"""
    try:
        result = get_ableton_connection().send_command("get_session_info")
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting session info: {str(e)}"

@mcp.tool()
def get_track_info(ctx: Context, track_index: int) -> str:
    """
    Get detailed information about a specific track in Ableton.

    Parameters:
    - track_index: The index of the track to get information about
    """
    try:
        result = get_ableton_connection().send_command("get_track_info", {"track_index": track_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting track info: {str(e)}"

@mcp.tool()
def create_midi_track(ctx: Context, index: int = -1) -> str:
    """
    Create a new MIDI track in the Ableton session.

    Parameters:
    - index: The index to insert the track at (-1 = end of list)
    """
    try:
        result = get_ableton_connection().send_command("create_midi_track", {"index": index})
        return f"Created new MIDI track: {result.get('name', 'unknown')}"
    except Exception as e:
        return f"Error creating MIDI track: {str(e)}"

@mcp.tool()
def set_track_name(ctx: Context, track_index: int, name: str) -> str:
    """
    Set the name of a track.

    Parameters:
    - track_index: The index of the track to rename
    - name: The new name for the track
    """
    try:
        result = get_ableton_connection().send_command("set_track_name", {
            "track_index": track_index, "name": name})
        return f"Renamed track to: {result.get('name', name)}"
    except Exception as e:
        return f"Error setting track name: {str(e)}"

@mcp.tool()
def create_clip(ctx: Context, track_index: int, clip_index: int, length: float = 4.0) -> str:
    """
    Create a new MIDI clip in the specified track and clip slot (Session View).

    Parameters:
    - track_index: The index of the track to create the clip in
    - clip_index: The index of the clip slot to create the clip in
    - length: The length of the clip in beats (default: 4.0)
    """
    try:
        get_ableton_connection().send_command("create_clip", {
            "track_index": track_index, "clip_index": clip_index, "length": length})
        return f"Created new clip at track {track_index}, slot {clip_index} with length {length} beats"
    except Exception as e:
        return f"Error creating clip: {str(e)}"

@mcp.tool()
def add_notes_to_clip(
    ctx: Context,
    track_index: int,
    clip_index: int,
    notes: List[Dict[str, Union[int, float, bool]]]
) -> str:
    """
    Add MIDI notes to a Session View clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - notes: List of note dicts with pitch, start_time, duration, velocity, mute
    """
    try:
        get_ableton_connection().send_command("add_notes_to_clip", {
            "track_index": track_index, "clip_index": clip_index, "notes": notes})
        return f"Added {len(notes)} notes to clip at track {track_index}, slot {clip_index}"
    except Exception as e:
        return f"Error adding notes to clip: {str(e)}"

@mcp.tool()
def set_clip_name(ctx: Context, track_index: int, clip_index: int, name: str) -> str:
    """
    Set the name of a Session View clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - name: The new name for the clip
    """
    try:
        get_ableton_connection().send_command("set_clip_name", {
            "track_index": track_index, "clip_index": clip_index, "name": name})
        return f"Renamed clip at track {track_index}, slot {clip_index} to '{name}'"
    except Exception as e:
        return f"Error setting clip name: {str(e)}"

@mcp.tool()
def set_tempo(ctx: Context, tempo: float) -> str:
    """
    Set the tempo of the Ableton session.

    Parameters:
    - tempo: The new tempo in BPM
    """
    try:
        get_ableton_connection().send_command("set_tempo", {"tempo": tempo})
        return f"Set tempo to {tempo} BPM"
    except Exception as e:
        return f"Error setting tempo: {str(e)}"

@mcp.tool()
def load_instrument_or_effect(ctx: Context, track_index: int, uri: str) -> str:
    """
    Load an instrument or effect onto a track using its URI.

    Parameters:
    - track_index: The index of the track to load the instrument on
    - uri: The URI of the instrument or effect to load
    """
    try:
        result = get_ableton_connection().send_command("load_browser_item", {
            "track_index": track_index, "item_uri": uri})
        if result.get("loaded", False):
            devices = result.get("devices_after", [])
            return f"Loaded '{uri}' on track {track_index}. Devices: {', '.join(devices)}"
        return f"Failed to load '{uri}'"
    except Exception as e:
        return f"Error loading instrument: {str(e)}"

@mcp.tool()
def fire_clip(ctx: Context, track_index: int, clip_index: int) -> str:
    """
    Start playing a Session View clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    """
    try:
        get_ableton_connection().send_command("fire_clip", {
            "track_index": track_index, "clip_index": clip_index})
        return f"Started playing clip at track {track_index}, slot {clip_index}"
    except Exception as e:
        return f"Error firing clip: {str(e)}"

@mcp.tool()
def stop_clip(ctx: Context, track_index: int, clip_index: int) -> str:
    """
    Stop playing a Session View clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    """
    try:
        get_ableton_connection().send_command("stop_clip", {
            "track_index": track_index, "clip_index": clip_index})
        return f"Stopped clip at track {track_index}, slot {clip_index}"
    except Exception as e:
        return f"Error stopping clip: {str(e)}"

@mcp.tool()
def start_playback(ctx: Context) -> str:
    """Start playing the Ableton session."""
    try:
        get_ableton_connection().send_command("start_playback")
        return "Started playback"
    except Exception as e:
        return f"Error starting playback: {str(e)}"

@mcp.tool()
def stop_playback(ctx: Context) -> str:
    """Stop playing the Ableton session."""
    try:
        get_ableton_connection().send_command("stop_playback")
        return "Stopped playback"
    except Exception as e:
        return f"Error stopping playback: {str(e)}"

@mcp.tool()
def get_browser_tree(ctx: Context, category_type: str = "all") -> str:
    """
    Get a hierarchical tree of browser categories from Ableton.

    Parameters:
    - category_type: 'all', 'instruments', 'sounds', 'drums', 'audio_effects', 'midi_effects'
    """
    try:
        result = get_ableton_connection().send_command("get_browser_tree", {
            "category_type": category_type})
        if "available_categories" in result and len(result.get("categories", [])) == 0:
            available = result.get("available_categories", [])
            return (f"No categories found for '{category_type}'. "
                    f"Available: {', '.join(available)}")
        formatted = f"Browser tree for '{category_type}':\n\n"

        def format_tree(item, indent=0):
            out = ""
            if item:
                prefix = "  " * indent
                name = item.get("name", "Unknown")
                path = item.get("path", "")
                has_more = item.get("has_more", False)
                out += f"{prefix}• {name}"
                if path:
                    out += f" (path: {path})"
                if has_more:
                    out += " [...]"
                out += "\n"
                for child in item.get("children", []):
                    out += format_tree(child, indent + 1)
            return out

        for category in result.get("categories", []):
            formatted += format_tree(category)
            formatted += "\n"
        return formatted
    except Exception as e:
        return f"Error getting browser tree: {str(e)}"

@mcp.tool()
def get_browser_items_at_path(ctx: Context, path: str) -> str:
    """
    Get browser items at a specific path in Ableton's browser.

    Parameters:
    - path: Path in format "category/folder/subfolder"
    """
    try:
        result = get_ableton_connection().send_command("get_browser_items_at_path", {"path": path})
        if "error" in result and "available_categories" in result:
            return (f"Error: {result.get('error')}\n"
                    f"Available categories: {', '.join(result.get('available_categories', []))}")
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting browser items: {str(e)}"

@mcp.tool()
def load_drum_kit(ctx: Context, track_index: int, rack_uri: str, kit_path: str) -> str:
    """
    Load a drum rack and then a specific drum kit into it.

    Parameters:
    - track_index: The index of the track to load on
    - rack_uri: URI of the drum rack to load
    - kit_path: Browser path to the drum kit (e.g. 'drums/acoustic/kit1')
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("load_browser_item", {
            "track_index": track_index, "item_uri": rack_uri})
        if not result.get("loaded", False):
            return f"Failed to load drum rack '{rack_uri}'"
        kit_result = ableton.send_command("get_browser_items_at_path", {"path": kit_path})
        if "error" in kit_result:
            return f"Loaded drum rack but failed to find kit: {kit_result.get('error')}"
        loadable = [i for i in kit_result.get("items", []) if i.get("is_loadable", False)]
        if not loadable:
            return f"Loaded drum rack but no loadable kits found at '{kit_path}'"
        kit_uri = loadable[0].get("uri")
        ableton.send_command("load_browser_item", {"track_index": track_index, "item_uri": kit_uri})
        return f"Loaded drum rack and kit '{loadable[0].get('name')}' on track {track_index}"
    except Exception as e:
        return f"Error loading drum kit: {str(e)}"


# =============================================================================
# Arrangement View tools (new)
# =============================================================================

@mcp.tool()
def get_arrangement_clips(ctx: Context, track_index: int) -> str:
    """
    Get all clips currently placed in the Arrangement View for a track.

    Parameters:
    - track_index: The index of the track to inspect
    """
    try:
        result = get_ableton_connection().send_command("get_arrangement_clips", {
            "track_index": track_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting arrangement clips: {str(e)}"

# create_arrangement_clip: NOT a tool. track.create_clip() does not exist in the Live API.
# delete_arrangement_clip: NOT a tool. clip.delete() does not exist in the Live API.
# Both must be done manually by the user in Ableton's Arrangement View.

@mcp.tool()
def add_notes_to_arrangement_clip(
    ctx: Context,
    track_index: int,
    clip_index: int,
    notes: List[Dict[str, Union[int, float, bool]]]
) -> str:
    """
    Add MIDI notes to a clip in the Arrangement View.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The position of the clip in the track's arrangement clip list (0 = first clip)
    - notes: List of note dicts — each needs: pitch (MIDI 0-127), start_time (beats from clip start),
             duration (beats), velocity (0-127), mute (bool, optional)
    """
    try:
        result = get_ableton_connection().send_command("add_notes_to_arrangement_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "notes": notes,
        })
        return (f"Added {result.get('note_count', len(notes))} notes to arrangement clip "
                f"{clip_index} on track {track_index}")
    except Exception as e:
        return f"Error adding notes to arrangement clip: {str(e)}"

@mcp.tool()
def set_arrangement_clip_name(
    ctx: Context,
    track_index: int,
    clip_index: int,
    name: str
) -> str:
    """
    Rename a clip in the Arrangement View.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The position of the clip in the track's arrangement clip list (0 = first clip)
    - name: The new name for the clip
    """
    try:
        result = get_ableton_connection().send_command("set_arrangement_clip_name", {
            "track_index": track_index,
            "clip_index": clip_index,
            "name": name,
        })
        return f"Renamed arrangement clip {clip_index} on track {track_index} to '{result.get('name', name)}'"
    except Exception as e:
        return f"Error setting arrangement clip name: {str(e)}"

# delete_arrangement_clip: NOT exposed as a tool.
# The Live ControlSurface Python API has no method to delete arrangement clips
# (clip.delete() and song.delete_clip() do not exist). Users must delete manually in Ableton.


def main():
    mcp.run()

if __name__ == "__main__":
    main()
