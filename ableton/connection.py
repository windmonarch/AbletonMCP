# ableton/connection.py
# TCP connection to the AbletonMCPLocal remote script running inside Ableton.
import socket
import json
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any

logger = logging.getLogger("AbletonMCPServer")

# Commands that modify Live state - need a short delay and longer timeout.
MODIFYING_COMMANDS: set = {
    "create_midi_track",
    "create_audio_track",
    "set_track_name",
    "create_clip",
    "add_notes_to_clip",
    "set_clip_name",
    "set_tempo",
    "fire_clip",
    "stop_clip",
    "set_device_parameter",
    "start_playback",
    "stop_playback",
    "load_instrument_or_effect",
    "add_notes_to_arrangement_clip",
    "set_arrangement_clip_name",
    # New write commands
    "jump_to_cue",
    "undo",
    "redo",
    "create_return_track",
    "delete_track",
    "duplicate_track",
    "set_track_color",
    "set_track_mute",
    "set_track_solo",
    "set_track_arm",
    "set_track_volume",
    "set_track_pan",
    "set_track_send",
    "delete_device",
    "remove_notes_from_clip",
    "set_clip_color",
    "set_clip_pitch",
    "set_clip_gain",
    "set_clip_markers",
}


@dataclass
class AbletonConnection:
    host: str
    port: int
    sock: socket.socket = field(default=None, repr=False)

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

    def _receive_full_response(self, buffer_size: int = 8192) -> bytes:
        """Read from socket until a complete JSON payload is received."""
        chunks = []
        self.sock.settimeout(15.0)
        try:
            while True:
                try:
                    chunk = self.sock.recv(buffer_size)
                    if not chunk:
                        if not chunks:
                            raise Exception("Connection closed before receiving any data")
                        break
                    chunks.append(chunk)
                    # Check if accumulated data is valid JSON - stop if so.
                    data = b"".join(chunks)
                    try:
                        json.loads(data.decode("utf-8"))
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
            data = b"".join(chunks)
            try:
                json.loads(data.decode("utf-8"))
                return data
            except json.JSONDecodeError:
                raise Exception("Incomplete JSON response received")
        raise Exception("No data received")

    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Ableton")

        command = {"type": command_type, "params": params or {}}
        modifying = command_type in MODIFYING_COMMANDS

        try:
            logger.info(f"Sending command: {command_type} with params: {params}")
            self.sock.sendall(json.dumps(command).encode("utf-8"))

            if modifying:
                time.sleep(0.1)

            self.sock.settimeout(15.0 if modifying else 10.0)
            response_data = self._receive_full_response()
            response = json.loads(response_data.decode("utf-8"))

            if response.get("status") == "error":
                raise Exception(response.get("message", "Unknown error from Ableton"))

            if modifying:
                time.sleep(0.1)

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


# ---------------------------------------------------------------------------
# Module-level singleton connection
# ---------------------------------------------------------------------------

_ableton_connection: AbletonConnection = None


def get_ableton_connection() -> AbletonConnection:
    global _ableton_connection

    # Validate existing connection with a no-op send.
    if _ableton_connection is not None:
        try:
            _ableton_connection.sock.settimeout(1.0)
            _ableton_connection.sock.sendall(b"")
            return _ableton_connection
        except Exception:
            try:
                _ableton_connection.disconnect()
            except Exception:
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
            _ableton_connection = None
        except Exception as e:
            logger.error(f"Attempt {attempt} failed: {str(e)}")
            if _ableton_connection:
                _ableton_connection.disconnect()
                _ableton_connection = None
        if attempt < 3:
            time.sleep(1.0)

    raise Exception("Could not connect to Ableton. Make sure the Remote Script is running.")


def shutdown_connection():
    global _ableton_connection
    if _ableton_connection:
        _ableton_connection.disconnect()
        _ableton_connection = None
