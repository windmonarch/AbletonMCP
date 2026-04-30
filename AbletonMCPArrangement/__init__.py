# AbletonMCPArrangement/__init__.py
# Extended version of AbletonMCP with Arrangement View support.
from __future__ import absolute_import, print_function, unicode_literals

from _Framework.ControlSurface import ControlSurface
import socket
import json
import threading
import time
import traceback

try:
    import Queue as queue  # Python 2
except ImportError:
    import queue  # Python 3

DEFAULT_PORT = 9877
HOST = "localhost"

def create_instance(c_instance):
    return AbletonMCPArrangement(c_instance)

class AbletonMCPArrangement(ControlSurface):

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.log_message("AbletonMCPArrangement initializing...")
        self.server = None
        self.client_threads = []
        self.server_thread = None
        self.running = False
        self._song = self.song()
        self.start_server()
        self.log_message("AbletonMCPArrangement initialized")
        self.show_message("AbletonMCPArrangement: Listening on port " + str(DEFAULT_PORT))

    def disconnect(self):
        self.log_message("AbletonMCPArrangement disconnecting...")
        self.running = False
        if self.server:
            try:
                self.server.close()
            except:
                pass
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(1.0)
        for client_thread in self.client_threads[:]:
            if client_thread.is_alive():
                self.log_message("Client thread still alive during disconnect")
        ControlSurface.disconnect(self)
        self.log_message("AbletonMCPArrangement disconnected")

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
            self.show_message("AbletonMCPArrangement: Error starting server - " + str(e))

    def _server_thread(self):
        try:
            self.log_message("Server thread started")
            self.server.settimeout(1.0)
            while self.running:
                try:
                    client, address = self.server.accept()
                    self.log_message("Connection accepted from " + str(address))
                    self.show_message("AbletonMCPArrangement: Client connected")
                    client_thread = threading.Thread(target=self._handle_client, args=(client,))
                    client_thread.daemon = True
                    client_thread.start()
                    self.client_threads.append(client_thread)
                    self.client_threads = [t for t in self.client_threads if t.is_alive()]
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.log_message("Server accept error: " + str(e))
                    time.sleep(0.5)
            self.log_message("Server thread stopped")
        except Exception as e:
            self.log_message("Server thread error: " + str(e))

    def _handle_client(self, client):
        self.log_message("Client handler started")
        client.settimeout(None)
        buffer = ''
        try:
            while self.running:
                try:
                    data = client.recv(8192)
                    if not data:
                        self.log_message("Client disconnected")
                        break
                    try:
                        buffer += data.decode('utf-8')
                    except AttributeError:
                        buffer += data
                    try:
                        command = json.loads(buffer)
                        buffer = ''
                        self.log_message("Received command: " + str(command.get("type", "unknown")))
                        response = self._process_command(command)
                        try:
                            client.sendall(json.dumps(response).encode('utf-8'))
                        except AttributeError:
                            client.sendall(json.dumps(response))
                    except ValueError:
                        continue
                except Exception as e:
                    self.log_message("Error handling client data: " + str(e))
                    self.log_message(traceback.format_exc())
                    error_response = {"status": "error", "message": str(e)}
                    try:
                        client.sendall(json.dumps(error_response).encode('utf-8'))
                    except AttributeError:
                        client.sendall(json.dumps(error_response))
                    except:
                        break
                    if not isinstance(e, ValueError):
                        break
        except Exception as e:
            self.log_message("Error in client handler: " + str(e))
        finally:
            try:
                client.close()
            except:
                pass
            self.log_message("Client handler stopped")

    def _process_command(self, command):
        command_type = command.get("type", "")
        params = command.get("params", {})
        response = {"status": "success", "result": {}}

        try:
            # Read-only commands — safe to run directly
            if command_type == "get_session_info":
                response["result"] = self._get_session_info()
            elif command_type == "get_track_info":
                response["result"] = self._get_track_info(params.get("track_index", 0))
            elif command_type == "get_arrangement_clips":
                response["result"] = self._get_arrangement_clips(params.get("track_index", 0))
            elif command_type == "get_browser_item":
                response["result"] = self._get_browser_item(
                    params.get("uri", None), params.get("path", None))
            elif command_type == "get_browser_categories":
                response["result"] = self._get_browser_categories(params.get("category_type", "all"))
            elif command_type == "get_browser_items":
                response["result"] = self._get_browser_items(
                    params.get("path", ""), params.get("item_type", "all"))
            elif command_type == "get_browser_tree":
                response["result"] = self.get_browser_tree(params.get("category_type", "all"))
            elif command_type == "get_browser_items_at_path":
                response["result"] = self.get_browser_items_at_path(params.get("path", ""))

            # State-modifying commands — run on main thread
            elif command_type in [
                "create_midi_track", "set_track_name",
                "create_clip", "add_notes_to_clip", "set_clip_name",
                "set_tempo", "fire_clip", "stop_clip",
                "start_playback", "stop_playback", "load_browser_item",
                # Arrangement view commands
                "add_notes_to_arrangement_clip",
                "set_arrangement_clip_name",
            ]:
                response_queue = queue.Queue()

                def main_thread_task():
                    try:
                        result = None
                        if command_type == "create_midi_track":
                            result = self._create_midi_track(params.get("index", -1))
                        elif command_type == "set_track_name":
                            result = self._set_track_name(
                                params.get("track_index", 0), params.get("name", ""))
                        elif command_type == "create_clip":
                            result = self._create_clip(
                                params.get("track_index", 0),
                                params.get("clip_index", 0),
                                params.get("length", 4.0))
                        elif command_type == "add_notes_to_clip":
                            result = self._add_notes_to_clip(
                                params.get("track_index", 0),
                                params.get("clip_index", 0),
                                params.get("notes", []))
                        elif command_type == "set_clip_name":
                            result = self._set_clip_name(
                                params.get("track_index", 0),
                                params.get("clip_index", 0),
                                params.get("name", ""))
                        elif command_type == "set_tempo":
                            result = self._set_tempo(params.get("tempo", 120.0))
                        elif command_type == "fire_clip":
                            result = self._fire_clip(
                                params.get("track_index", 0), params.get("clip_index", 0))
                        elif command_type == "stop_clip":
                            result = self._stop_clip(
                                params.get("track_index", 0), params.get("clip_index", 0))
                        elif command_type == "start_playback":
                            result = self._start_playback()
                        elif command_type == "stop_playback":
                            result = self._stop_playback()
                        elif command_type == "load_browser_item":
                            result = self._load_browser_item(
                                params.get("track_index", 0), params.get("item_uri", ""))
                        # --- Arrangement view ---
                        elif command_type == "add_notes_to_arrangement_clip":
                            result = self._add_notes_to_arrangement_clip(
                                params.get("track_index", 0),
                                params.get("clip_index", 0),
                                params.get("notes", []))
                        elif command_type == "set_arrangement_clip_name":
                            result = self._set_arrangement_clip_name(
                                params.get("track_index", 0),
                                params.get("clip_index", 0),
                                params.get("name", ""))
                        response_queue.put({"status": "success", "result": result})
                    except Exception as e:
                        self.log_message("Error in main thread task: " + str(e))
                        self.log_message(traceback.format_exc())
                        response_queue.put({"status": "error", "message": str(e)})

                try:
                    self.schedule_message(0, main_thread_task)
                except AssertionError:
                    main_thread_task()

                try:
                    task_response = response_queue.get(timeout=10.0)
                    if task_response.get("status") == "error":
                        response["status"] = "error"
                        response["message"] = task_response.get("message", "Unknown error")
                    else:
                        response["result"] = task_response.get("result", {})
                except queue.Empty:
                    response["status"] = "error"
                    response["message"] = "Timeout waiting for operation to complete"
            else:
                response["status"] = "error"
                response["message"] = "Unknown command: " + command_type
        except Exception as e:
            self.log_message("Error processing command: " + str(e))
            self.log_message(traceback.format_exc())
            response["status"] = "error"
            response["message"] = str(e)

        return response

    # -------------------------------------------------------------------------
    # Session info / track info
    # -------------------------------------------------------------------------

    def _get_session_info(self):
        try:
            return {
                "tempo": self._song.tempo,
                "signature_numerator": self._song.signature_numerator,
                "signature_denominator": self._song.signature_denominator,
                "track_count": len(self._song.tracks),
                "return_track_count": len(self._song.return_tracks),
                "master_track": {
                    "name": "Master",
                    "volume": self._song.master_track.mixer_device.volume.value,
                    "panning": self._song.master_track.mixer_device.panning.value
                }
            }
        except Exception as e:
            self.log_message("Error getting session info: " + str(e))
            raise

    def _get_track_info(self, track_index):
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            track = self._song.tracks[track_index]
            clip_slots = []
            for slot_index, slot in enumerate(track.clip_slots):
                clip_info = None
                if slot.has_clip:
                    clip = slot.clip
                    clip_info = {
                        "name": clip.name,
                        "length": clip.length,
                        "is_playing": clip.is_playing,
                        "is_recording": clip.is_recording
                    }
                clip_slots.append({
                    "index": slot_index,
                    "has_clip": slot.has_clip,
                    "clip": clip_info
                })
            devices = []
            for device_index, device in enumerate(track.devices):
                devices.append({
                    "index": device_index,
                    "name": device.name,
                    "class_name": device.class_name,
                    "type": self._get_device_type(device)
                })
            return {
                "index": track_index,
                "name": track.name,
                "is_audio_track": track.has_audio_input,
                "is_midi_track": track.has_midi_input,
                "mute": track.mute,
                "solo": track.solo,
                "arm": track.arm,
                "volume": track.mixer_device.volume.value,
                "panning": track.mixer_device.panning.value,
                "clip_slots": clip_slots,
                "devices": devices
            }
        except Exception as e:
            self.log_message("Error getting track info: " + str(e))
            raise

    # -------------------------------------------------------------------------
    # Session View commands (unchanged from original)
    # -------------------------------------------------------------------------

    def _create_midi_track(self, index):
        try:
            self._song.create_midi_track(index)
            new_track_index = len(self._song.tracks) - 1 if index == -1 else index
            new_track = self._song.tracks[new_track_index]
            return {"index": new_track_index, "name": new_track.name}
        except Exception as e:
            self.log_message("Error creating MIDI track: " + str(e))
            raise

    def _set_track_name(self, track_index, name):
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            track = self._song.tracks[track_index]
            track.name = name
            return {"name": track.name}
        except Exception as e:
            self.log_message("Error setting track name: " + str(e))
            raise

    def _create_clip(self, track_index, clip_index, length):
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            track = self._song.tracks[track_index]
            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")
            clip_slot = track.clip_slots[clip_index]
            if clip_slot.has_clip:
                raise Exception("Clip slot already has a clip")
            clip_slot.create_clip(length)
            return {"name": clip_slot.clip.name, "length": clip_slot.clip.length}
        except Exception as e:
            self.log_message("Error creating clip: " + str(e))
            raise

    def _add_notes_to_clip(self, track_index, clip_index, notes):
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            track = self._song.tracks[track_index]
            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")
            clip_slot = track.clip_slots[clip_index]
            if not clip_slot.has_clip:
                raise Exception("No clip in slot")
            clip = clip_slot.clip
            live_notes = []
            for note in notes:
                live_notes.append((
                    note.get("pitch", 60),
                    note.get("start_time", 0.0),
                    note.get("duration", 0.25),
                    note.get("velocity", 100),
                    note.get("mute", False)
                ))
            clip.set_notes(tuple(live_notes))
            return {"note_count": len(notes)}
        except Exception as e:
            self.log_message("Error adding notes to clip: " + str(e))
            raise

    def _set_clip_name(self, track_index, clip_index, name):
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            track = self._song.tracks[track_index]
            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")
            clip_slot = track.clip_slots[clip_index]
            if not clip_slot.has_clip:
                raise Exception("No clip in slot")
            clip_slot.clip.name = name
            return {"name": clip_slot.clip.name}
        except Exception as e:
            self.log_message("Error setting clip name: " + str(e))
            raise

    def _set_tempo(self, tempo):
        try:
            self._song.tempo = tempo
            return {"tempo": self._song.tempo}
        except Exception as e:
            self.log_message("Error setting tempo: " + str(e))
            raise

    def _fire_clip(self, track_index, clip_index):
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            track = self._song.tracks[track_index]
            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")
            clip_slot = track.clip_slots[clip_index]
            if not clip_slot.has_clip:
                raise Exception("No clip in slot")
            clip_slot.fire()
            return {"fired": True}
        except Exception as e:
            self.log_message("Error firing clip: " + str(e))
            raise

    def _stop_clip(self, track_index, clip_index):
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            track = self._song.tracks[track_index]
            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")
            track.clip_slots[clip_index].stop()
            return {"stopped": True}
        except Exception as e:
            self.log_message("Error stopping clip: " + str(e))
            raise

    def _start_playback(self):
        try:
            self._song.start_playing()
            return {"playing": self._song.is_playing}
        except Exception as e:
            self.log_message("Error starting playback: " + str(e))
            raise

    def _stop_playback(self):
        try:
            self._song.stop_playing()
            return {"playing": self._song.is_playing}
        except Exception as e:
            self.log_message("Error stopping playback: " + str(e))
            raise

    # -------------------------------------------------------------------------
    # Arrangement View commands (new)
    # -------------------------------------------------------------------------

    def _get_arrangement_clips(self, track_index):
        """Return all clips currently placed in the Arrangement View for a track."""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            track = self._song.tracks[track_index]
            clips = []
            for i, clip in enumerate(track.arrangement_clips):
                clips.append({
                    "index": i,
                    "name": clip.name,
                    "start_time": clip.start_time,
                    "end_time": clip.end_time,
                    "length": clip.length,
                    "is_playing": clip.is_playing,
                })
            return {"clips": clips, "count": len(clips)}
        except Exception as e:
            self.log_message("Error getting arrangement clips: " + str(e))
            raise

    # NOTE: create_arrangement_clip and delete_arrangement_clip are NOT implemented.
    # The Live ControlSurface Python API exposes no method to create or delete
    # arrangement clips (track.create_clip() and clip.delete() do not exist).
    # Users must create/delete clips manually in Ableton's Arrangement View.

    def _add_notes_to_arrangement_clip(self, track_index, clip_index, notes):
        """Add MIDI notes to a clip in the Arrangement View.

        clip_index is the position of the clip in track.arrangement_clips.
        """
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            track = self._song.tracks[track_index]
            arr_clips = list(track.arrangement_clips)
            if clip_index < 0 or clip_index >= len(arr_clips):
                raise IndexError(
                    "Arrangement clip index out of range. Track has {0} arrangement clip(s).".format(
                        len(arr_clips)))
            clip = arr_clips[clip_index]
            live_notes = []
            for note in notes:
                live_notes.append((
                    note.get("pitch", 60),
                    note.get("start_time", 0.0),
                    note.get("duration", 0.25),
                    note.get("velocity", 100),
                    note.get("mute", False)
                ))
            clip.set_notes(tuple(live_notes))
            return {"note_count": len(notes)}
        except Exception as e:
            self.log_message("Error adding notes to arrangement clip: " + str(e))
            raise

    def _set_arrangement_clip_name(self, track_index, clip_index, name):
        """Rename a clip in the Arrangement View."""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            track = self._song.tracks[track_index]
            arr_clips = list(track.arrangement_clips)
            if clip_index < 0 or clip_index >= len(arr_clips):
                raise IndexError("Arrangement clip index out of range")
            arr_clips[clip_index].name = name
            return {"name": arr_clips[clip_index].name}
        except Exception as e:
            self.log_message("Error setting arrangement clip name: " + str(e))
            raise

    # -------------------------------------------------------------------------
    # Browser helpers (unchanged from original)
    # -------------------------------------------------------------------------

    def _load_browser_item(self, track_index, item_uri):
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            track = self._song.tracks[track_index]
            app = self.application()
            item = self._find_browser_item_by_uri(app.browser, item_uri)
            if not item:
                raise ValueError("Browser item with URI '{0}' not found".format(item_uri))
            self._song.view.selected_track = track
            app.browser.load_item(item)
            return {
                "loaded": True,
                "item_name": item.name,
                "track_name": track.name,
                "uri": item_uri
            }
        except Exception as e:
            self.log_message("Error loading browser item: {0}".format(str(e)))
            self.log_message(traceback.format_exc())
            raise

    def _get_browser_item(self, uri, path):
        try:
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
                        "uri": item.uri
                    }
                    return result
            if path:
                path_parts = path.split("/")
                current_item = None
                if path_parts[0].lower() == "instruments":
                    current_item = app.browser.instruments
                elif path_parts[0].lower() == "sounds":
                    current_item = app.browser.sounds
                elif path_parts[0].lower() == "drums":
                    current_item = app.browser.drums
                elif path_parts[0].lower() == "audio_effects":
                    current_item = app.browser.audio_effects
                elif path_parts[0].lower() == "midi_effects":
                    current_item = app.browser.midi_effects
                else:
                    current_item = app.browser.instruments
                    path_parts = ["instruments"] + path_parts
                for i in range(1, len(path_parts)):
                    part = path_parts[i]
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
                    "uri": current_item.uri
                }
            return result
        except Exception as e:
            self.log_message("Error getting browser item: " + str(e))
            self.log_message(traceback.format_exc())
            raise

    def _find_browser_item_by_uri(self, browser_or_item, uri, max_depth=10, current_depth=0):
        try:
            if hasattr(browser_or_item, 'uri') and browser_or_item.uri == uri:
                return browser_or_item
            if current_depth >= max_depth:
                return None
            if hasattr(browser_or_item, 'instruments'):
                categories = [
                    browser_or_item.instruments,
                    browser_or_item.sounds,
                    browser_or_item.drums,
                    browser_or_item.audio_effects,
                    browser_or_item.midi_effects
                ]
                for category in categories:
                    item = self._find_browser_item_by_uri(category, uri, max_depth, current_depth + 1)
                    if item:
                        return item
                return None
            if hasattr(browser_or_item, 'children') and browser_or_item.children:
                for child in browser_or_item.children:
                    item = self._find_browser_item_by_uri(child, uri, max_depth, current_depth + 1)
                    if item:
                        return item
            return None
        except Exception as e:
            self.log_message("Error finding browser item by URI: {0}".format(str(e)))
            return None

    def _get_browser_categories(self, category_type):
        return {}

    def _get_browser_items(self, path, item_type):
        return {}

    def _get_device_type(self, device):
        try:
            if device.can_have_drum_pads:
                return "drum_machine"
            elif device.can_have_chains:
                return "rack"
            elif "instrument" in device.class_display_name.lower():
                return "instrument"
            elif "audio_effect" in device.class_name.lower():
                return "audio_effect"
            elif "midi_effect" in device.class_name.lower():
                return "midi_effect"
            else:
                return "unknown"
        except:
            return "unknown"

    def get_browser_tree(self, category_type="all"):
        try:
            app = self.application()
            if not app:
                raise RuntimeError("Could not access Live application")
            if not hasattr(app, 'browser') or app.browser is None:
                raise RuntimeError("Browser is not available in the Live application")
            browser_attrs = [attr for attr in dir(app.browser) if not attr.startswith('_')]
            self.log_message("Available browser attributes: {0}".format(browser_attrs))
            result = {
                "type": category_type,
                "categories": [],
                "available_categories": browser_attrs
            }

            def process_item(item, depth=0):
                if not item:
                    return None
                return {
                    "name": item.name if hasattr(item, 'name') else "Unknown",
                    "is_folder": hasattr(item, 'children') and bool(item.children),
                    "is_device": hasattr(item, 'is_device') and item.is_device,
                    "is_loadable": hasattr(item, 'is_loadable') and item.is_loadable,
                    "uri": item.uri if hasattr(item, 'uri') else None,
                    "children": []
                }

            cat_map = {
                "instruments": ("Instruments", lambda: app.browser.instruments),
                "sounds": ("Sounds", lambda: app.browser.sounds),
                "drums": ("Drums", lambda: app.browser.drums),
                "audio_effects": ("Audio Effects", lambda: app.browser.audio_effects),
                "midi_effects": ("MIDI Effects", lambda: app.browser.midi_effects),
            }
            for key, (label, getter) in cat_map.items():
                if (category_type == "all" or category_type == key) and hasattr(app.browser, key):
                    try:
                        cat = process_item(getter())
                        if cat:
                            cat["name"] = label
                            result["categories"].append(cat)
                    except Exception as e:
                        self.log_message("Error processing {0}: {1}".format(key, str(e)))

            for attr in browser_attrs:
                if attr not in cat_map and (category_type == "all" or category_type == attr):
                    try:
                        item = getattr(app.browser, attr)
                        if hasattr(item, 'children') or hasattr(item, 'name'):
                            cat = process_item(item)
                            if cat:
                                cat["name"] = attr.capitalize()
                                result["categories"].append(cat)
                    except Exception as e:
                        self.log_message("Error processing {0}: {1}".format(attr, str(e)))

            self.log_message("Browser tree generated with {0} root categories".format(
                len(result['categories'])))
            return result
        except Exception as e:
            self.log_message("Error getting browser tree: {0}".format(str(e)))
            self.log_message(traceback.format_exc())
            raise

    def get_browser_items_at_path(self, path):
        try:
            app = self.application()
            if not app:
                raise RuntimeError("Could not access Live application")
            if not hasattr(app, 'browser') or app.browser is None:
                raise RuntimeError("Browser is not available in the Live application")
            browser_attrs = [attr for attr in dir(app.browser) if not attr.startswith('_')]
            path_parts = path.split("/")
            if not path_parts:
                raise ValueError("Invalid path")
            root_category = path_parts[0].lower()
            current_item = None
            standard = {
                "instruments": "instruments",
                "sounds": "sounds",
                "drums": "drums",
                "audio_effects": "audio_effects",
                "midi_effects": "midi_effects",
            }
            if root_category in standard and hasattr(app.browser, standard[root_category]):
                current_item = getattr(app.browser, standard[root_category])
            else:
                for attr in browser_attrs:
                    if attr.lower() == root_category:
                        try:
                            current_item = getattr(app.browser, attr)
                            break
                        except Exception as e:
                            self.log_message("Error accessing {0}: {1}".format(attr, str(e)))
                if current_item is None:
                    return {
                        "path": path,
                        "error": "Unknown or unavailable category: {0}".format(root_category),
                        "available_categories": browser_attrs,
                        "items": []
                    }
            for i in range(1, len(path_parts)):
                part = path_parts[i]
                if not part:
                    continue
                if not hasattr(current_item, 'children'):
                    return {
                        "path": path,
                        "error": "Item at '{0}' has no children".format('/'.join(path_parts[:i])),
                        "items": []
                    }
                found = False
                for child in current_item.children:
                    if hasattr(child, 'name') and child.name.lower() == part.lower():
                        current_item = child
                        found = True
                        break
                if not found:
                    return {
                        "path": path,
                        "error": "Path part '{0}' not found".format(part),
                        "items": []
                    }
            items = []
            if hasattr(current_item, 'children'):
                for child in current_item.children:
                    items.append({
                        "name": child.name if hasattr(child, 'name') else "Unknown",
                        "is_folder": hasattr(child, 'children') and bool(child.children),
                        "is_device": hasattr(child, 'is_device') and child.is_device,
                        "is_loadable": hasattr(child, 'is_loadable') and child.is_loadable,
                        "uri": child.uri if hasattr(child, 'uri') else None
                    })
            return {
                "path": path,
                "name": current_item.name if hasattr(current_item, 'name') else "Unknown",
                "uri": current_item.uri if hasattr(current_item, 'uri') else None,
                "is_folder": hasattr(current_item, 'children') and bool(current_item.children),
                "is_device": hasattr(current_item, 'is_device') and current_item.is_device,
                "is_loadable": hasattr(current_item, 'is_loadable') and current_item.is_loadable,
                "items": items
            }
        except Exception as e:
            self.log_message("Error getting browser items at path: {0}".format(str(e)))
            self.log_message(traceback.format_exc())
            raise
