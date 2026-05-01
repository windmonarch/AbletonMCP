# AbletonMCPLocal/__init__.py
# Ableton Remote Script entry point.
# Loaded by Ableton Live from:
#   Documents\Ableton\User Library\Remote Scripts\AbletonMCPLocal\
from __future__ import absolute_import, print_function, unicode_literals

from _Framework.ControlSurface import ControlSurface
import socket
import json
import threading
import time
import traceback
import queue

from .commands_session import SessionCommands
from .commands_arrangement import ArrangementCommands
from .commands_browser import BrowserCommands
from .commands_devices import DeviceCommands
from .commands_scenes import SceneCommands
from .commands_automation import AutomationCommands

DEFAULT_PORT = 9877
HOST = "localhost"


def create_instance(c_instance):
    return AbletonMCPLocal(c_instance)


class AbletonMCPLocal(SessionCommands, ArrangementCommands, BrowserCommands, DeviceCommands, SceneCommands, AutomationCommands, ControlSurface):

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.log_message("AbletonMCPLocal initializing...")
        self.server = None
        self.client_threads = []
        self.server_thread = None
        self.running = False
        self._song = self.song()
        self._build_dispatch_table()
        self.start_server()
        self.log_message("AbletonMCPLocal initialized")
        self.show_message("AbletonMCPLocal: Listening on port " + str(DEFAULT_PORT))

    def disconnect(self):
        self.log_message("AbletonMCPLocal disconnecting...")
        self.running = False
        if self.server:
            try:
                self.server.close()
            except Exception:
                pass
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(1.0)
        ControlSurface.disconnect(self)
        self.log_message("AbletonMCPLocal disconnected")

    # -------------------------------------------------------------------------
    # Dispatch table
    # -------------------------------------------------------------------------

    def _build_dispatch_table(self):
        """Build two dicts that map command names to handler callables.

        READ_DISPATCH  - safe to call from any thread immediately.
        WRITE_DISPATCH - must run on Ableton's main thread via schedule_message().
        """
        self.READ_DISPATCH = {
            "get_session_info":          lambda p: self._get_session_info(),
            "get_track_info":            lambda p: self._get_track_info(p.get("track_index", 0)),
            "get_arrangement_clips":     lambda p: self._get_arrangement_clips(p.get("track_index", 0)),
            "get_browser_tree":          lambda p: self.get_browser_tree(p.get("category_type", "all")),
            "get_browser_items_at_path": lambda p: self.get_browser_items_at_path(p.get("path", "")),
            "get_browser_item":          lambda p: self._get_browser_item(p.get("uri"), p.get("path")),
            "get_cue_points":            lambda p: self._get_cue_points(),
            "get_current_song_time":     lambda p: self._get_current_song_time(),
            "get_track_sends":           lambda p: self._get_track_sends(p.get("track_index", 0)),
            "get_clip_notes":            lambda p: self._get_clip_notes(p.get("track_index", 0), p.get("clip_index", 0)),
            "get_device_parameters":     lambda p: self._get_device_parameters(p.get("track_index", 0), p.get("device_index", 0)),
            "get_drum_pads":             lambda p: self._get_drum_pads(p.get("track_index", 0), p.get("device_index", 0)),
            "get_scenes":                lambda p: self._get_scenes(),
            "get_clip_envelope":         lambda p: self._get_clip_envelope(p.get("track_index", 0), p.get("clip_index", 0), p.get("device_index", 0), p.get("param_index", 0)),
        }

        self.WRITE_DISPATCH = {
            "create_midi_track":              lambda p: self._create_midi_track(p.get("index", -1)),
            "set_track_name":                 lambda p: self._set_track_name(p.get("track_index", 0), p.get("name", "")),
            "create_clip":                    lambda p: self._create_clip(p.get("track_index", 0), p.get("clip_index", 0), p.get("length", 4.0)),
            "add_notes_to_clip":              lambda p: self._add_notes_to_clip(p.get("track_index", 0), p.get("clip_index", 0), p.get("notes", [])),
            "set_clip_name":                  lambda p: self._set_clip_name(p.get("track_index", 0), p.get("clip_index", 0), p.get("name", "")),
            "set_tempo":                      lambda p: self._set_tempo(p.get("tempo", 120.0)),
            "fire_clip":                      lambda p: self._fire_clip(p.get("track_index", 0), p.get("clip_index", 0)),
            "stop_clip":                      lambda p: self._stop_clip(p.get("track_index", 0), p.get("clip_index", 0)),
            "start_playback":                 lambda p: self._start_playback(),
            "stop_playback":                  lambda p: self._stop_playback(),
            "load_browser_item":              lambda p: self._load_browser_item(p.get("track_index", 0), p.get("item_uri", "")),
            "add_notes_to_arrangement_clip":  lambda p: self._add_notes_to_arrangement_clip(p.get("track_index", 0), p.get("clip_index", 0), p.get("notes", [])),
            "set_arrangement_clip_name":      lambda p: self._set_arrangement_clip_name(p.get("track_index", 0), p.get("clip_index", 0), p.get("name", "")),
            # New commands
            "jump_to_cue":            lambda p: self._jump_to_cue(p.get("direction", "next")),
            "undo":                   lambda p: self._undo(),
            "redo":                   lambda p: self._redo(),
            "create_audio_track":     lambda p: self._create_audio_track(p.get("index", -1)),
            "create_return_track":    lambda p: self._create_return_track(),
            "delete_track":           lambda p: self._delete_track(p.get("track_index", 0)),
            "duplicate_track":        lambda p: self._duplicate_track(p.get("track_index", 0)),
            "set_track_color":        lambda p: self._set_track_color(p.get("track_index", 0), p.get("color", 0)),
            "set_track_mute":         lambda p: self._set_track_mute(p.get("track_index", 0), p.get("mute", False)),
            "set_track_solo":         lambda p: self._set_track_solo(p.get("track_index", 0), p.get("solo", False)),
            "set_track_arm":          lambda p: self._set_track_arm(p.get("track_index", 0), p.get("arm", False)),
            "set_track_volume":       lambda p: self._set_track_volume(p.get("track_index", 0), p.get("volume", 0.85)),
            "set_track_pan":          lambda p: self._set_track_pan(p.get("track_index", 0), p.get("panning", 0.0)),
            "set_track_send":         lambda p: self._set_track_send(p.get("track_index", 0), p.get("send_index", 0), p.get("value", 0.0)),
            "delete_device":          lambda p: self._delete_device(p.get("track_index", 0), p.get("device_index", 0)),
            "remove_notes_from_clip": lambda p: self._remove_notes_from_clip(p.get("track_index", 0), p.get("clip_index", 0)),
            "set_clip_color":         lambda p: self._set_clip_color(p.get("track_index", 0), p.get("clip_index", 0), p.get("color", 0)),
            "set_clip_pitch":         lambda p: self._set_clip_pitch(p.get("track_index", 0), p.get("clip_index", 0), p.get("pitch_coarse", 0), p.get("pitch_fine")),
            "set_clip_gain":          lambda p: self._set_clip_gain(p.get("track_index", 0), p.get("clip_index", 0), p.get("gain", 1.0)),
            "set_clip_markers":       lambda p: self._set_clip_markers(p.get("track_index", 0), p.get("clip_index", 0), p.get("start_marker", 0.0), p.get("end_marker", 0.0)),
            "set_device_parameter":   lambda p: self._set_device_parameter(p.get("track_index", 0), p.get("device_index", 0), p.get("param_index", 0), p.get("value", 0.0)),
            # Song level
            "set_time_signature":     lambda p: self._set_time_signature(p.get("numerator", 4), p.get("denominator", 4)),
            "jump_to_time":           lambda p: self._jump_to_time(p.get("time", 0.0)),
            # Scenes
            "create_scene":           lambda p: self._create_scene(p.get("index", -1)),
            "delete_scene":           lambda p: self._delete_scene(p.get("scene_index", 0)),
            "fire_scene":             lambda p: self._fire_scene(p.get("scene_index", 0)),
            "set_scene_name":         lambda p: self._set_scene_name(p.get("scene_index", 0), p.get("name", "")),
            "set_scene_tempo":        lambda p: self._set_scene_tempo(p.get("scene_index", 0), p.get("tempo", 120.0)),
            # Clip level
            "quantize_clip":          lambda p: self._quantize_clip(p.get("track_index", 0), p.get("clip_index", 0), p.get("grid", "1/8"), p.get("amount", 1.0)),
            "duplicate_clip_loop":    lambda p: self._duplicate_clip_loop(p.get("track_index", 0), p.get("clip_index", 0)),
            "set_clip_mute":          lambda p: self._set_clip_mute(p.get("track_index", 0), p.get("clip_index", 0), p.get("mute", False)),
            "clear_clip_envelopes":   lambda p: self._clear_clip_envelopes(p.get("track_index", 0), p.get("clip_index", 0)),
            # Cue points
            "create_cue_point":       lambda p: self._create_cue_point(p.get("time", 0.0)),
            "delete_cue_point":       lambda p: self._delete_cue_point(p.get("cue_index", 0)),
            "set_cue_point_name":     lambda p: self._set_cue_point_name(p.get("cue_index", 0), p.get("name", "")),
            # Automation
            "set_clip_envelope_point": lambda p: self._set_clip_envelope_point(p.get("track_index", 0), p.get("clip_index", 0), p.get("device_index", 0), p.get("param_index", 0), p.get("time", 0.0), p.get("value", 0.0), p.get("duration", 0.0)),
            "clear_clip_envelope":     lambda p: self._clear_clip_envelope(p.get("track_index", 0), p.get("clip_index", 0), p.get("device_index", 0), p.get("param_index", 0)),
        }

    # -------------------------------------------------------------------------
    # TCP server
    # -------------------------------------------------------------------------

    def start_server(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((HOST, DEFAULT_PORT))
            self.server.listen(5)
            self.running = True
            self.server_thread = threading.Thread(target=self._server_thread)
            self.server_thread.daemon = True
            self.server_thread.start()
            self.log_message("Server started on port " + str(DEFAULT_PORT))
        except Exception as e:
            self.log_message("Error starting server: " + str(e))
            self.show_message("AbletonMCPLocal: Error starting server - " + str(e))

    def _server_thread(self):
        self.log_message("Server thread started")
        self.server.settimeout(1.0)
        while self.running:
            try:
                client, address = self.server.accept()
                self.log_message("Connection accepted from " + str(address))
                self.show_message("AbletonMCPLocal: Client connected")
                client_thread = threading.Thread(target=self._handle_client, args=(client,))
                client_thread.daemon = True
                client_thread.start()
                # Prune dead threads while accepting new ones
                self.client_threads = [t for t in self.client_threads if t.is_alive()]
                self.client_threads.append(client_thread)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.log_message("Server accept error: " + str(e))
                time.sleep(0.5)
        self.log_message("Server thread stopped")

    def _handle_client(self, client):
        self.log_message("Client handler started")
        client.settimeout(None)
        buffer = ""
        try:
            while self.running:
                data = client.recv(8192)
                if not data:
                    self.log_message("Client disconnected")
                    break
                buffer += data.decode("utf-8")
                try:
                    command = json.loads(buffer)
                    buffer = ""
                    self.log_message("Received command: " + str(command.get("type", "unknown")))
                    response = self._process_command(command)
                    client.sendall(json.dumps(response).encode("utf-8"))
                except ValueError:
                    # Incomplete JSON - keep buffering
                    continue
                except Exception as e:
                    self.log_message("Error handling client data: " + str(e))
                    self.log_message(traceback.format_exc())
                    error_response = {"status": "error", "message": str(e)}
                    try:
                        client.sendall(json.dumps(error_response).encode("utf-8"))
                    except Exception:
                        break
                    break
        except Exception as e:
            self.log_message("Error in client handler: " + str(e))
        finally:
            try:
                client.close()
            except Exception:
                pass
            self.log_message("Client handler stopped")

    # -------------------------------------------------------------------------
    # Command dispatch
    # -------------------------------------------------------------------------

    def _process_command(self, command):
        command_type = command.get("type", "")
        params = command.get("params", {})

        # Read-only commands - run directly on this thread
        if command_type in self.READ_DISPATCH:
            try:
                result = self.READ_DISPATCH[command_type](params)
                return {"status": "success", "result": result}
            except Exception as e:
                self.log_message("Error in read command '{0}': {1}".format(command_type, str(e)))
                return {"status": "error", "message": str(e)}

        # Write commands - must run on Ableton's main thread
        if command_type in self.WRITE_DISPATCH:
            response_queue = queue.Queue()

            def main_thread_task():
                try:
                    result = self.WRITE_DISPATCH[command_type](params)
                    response_queue.put({"status": "success", "result": result})
                except Exception as e:
                    self.log_message("Error in write command '{0}': {1}".format(command_type, str(e)))
                    self.log_message(traceback.format_exc())
                    response_queue.put({"status": "error", "message": str(e)})

            try:
                self.schedule_message(0, main_thread_task)
            except AssertionError:
                main_thread_task()

            try:
                return response_queue.get(timeout=10.0)
            except queue.Empty:
                return {"status": "error", "message": "Timeout waiting for operation to complete"}

        return {"status": "error", "message": "Unknown command: " + command_type}

    # -------------------------------------------------------------------------
    # Legacy browser helper (kept for get_browser_item compatibility)
    # -------------------------------------------------------------------------

    def _get_browser_item(self, uri, path):
        app = self.application()
        if not app:
            raise RuntimeError("Could not access Live application")
        result = {"uri": uri, "path": path, "found": False}

        if uri:
            item = self._find_browser_item_by_uri(app.browser, uri)
            if item:
                result["found"] = True
                result["item"] = {
                    "name": item.name,
                    "is_folder": item.is_folder,
                    "is_device": item.is_device,
                    "is_loadable": item.is_loadable,
                    "uri": item.uri,
                }
                return result

        if path:
            path_parts = path.split("/")
            category_map = {
                "instruments": app.browser.instruments,
                "sounds": app.browser.sounds,
                "drums": app.browser.drums,
                "audio_effects": app.browser.audio_effects,
                "midi_effects": app.browser.midi_effects,
            }
            root = path_parts[0].lower()
            current_item = category_map.get(root)
            if current_item is None:
                current_item = app.browser.instruments
                path_parts = ["instruments"] + path_parts

            for part in path_parts[1:]:
                if not part:
                    continue
                found = False
                for child in current_item.children:
                    if child.name.lower() == part.lower():
                        current_item = child
                        found = True
                        break
                if not found:
                    result["error"] = "Path part '{0}' not found".format(part)
                    return result

            result["found"] = True
            result["item"] = {
                "name": current_item.name,
                "is_folder": current_item.is_folder,
                "is_device": current_item.is_device,
                "is_loadable": current_item.is_loadable,
                "uri": current_item.uri,
            }
        return result
