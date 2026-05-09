# AbletonMCPLocal/commands_browser.py
# Handlers for Ableton's browser (instruments, effects, samples, VST3/VST2 plugins).
from __future__ import absolute_import, print_function, unicode_literals
import traceback

try:
    from urllib.parse import unquote  # Python 3
except ImportError:
    from urllib import unquote        # Python 2


class BrowserCommands:
    """Mixin providing browser command handlers."""

    # Native Ableton browser category attribute names (used for recursive fallback).
    _BROWSER_CATEGORIES = {
        "instruments": "instruments",
        "sounds": "sounds",
        "drums": "drums",
        "audio_effects": "audio_effects",
        "midi_effects": "midi_effects",
    }

    # Maps the prefix after "query:" to the browser attribute name.
    # Used by _navigate_uri_directly for O(depth) lookup instead of full tree search.
    _URI_CATEGORY_MAP = {
        "AudioFx":    "audio_effects",
        "Instruments":"instruments",
        "MidiEffects":"midi_effects",
        "Sounds":     "sounds",
        "Drums":      "drums",
        "Plugins":    "plugins",
        "LivePacks":  "packs",
        "M4L":        "max_for_live",
    }

    # Plugin format search order for name-based lookup: VST3 preferred, then VST2/VST.
    _PLUGIN_FORMAT_PRIORITY = ["vst3", "vst"]

    # ---------------------------------------------------------------------------
    # Public / internal loading helpers
    # ---------------------------------------------------------------------------

    def _load_browser_item(self, track_index, item_uri):
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
            "uri": item_uri,
        }

    # ---------------------------------------------------------------------------
    # URI resolution - fast path first, recursive fallback second
    # ---------------------------------------------------------------------------

    def _find_browser_item_by_uri(self, browser_or_item, uri, max_depth=10, current_depth=0):
        """Locate a browser item by its URI.

        Strategy (fast to slow):
        1. Direct navigation - parse the URI and walk the tree in O(depth) by
           matching each decoded path segment against children by name.
           Works for all standard Live URIs: AudioFx, Plugins (VST3/VST), LivePacks, M4L ...
        2. Recursive search - full tree walk, kept as a safety net for any URI
           format not covered by direct navigation. Restricted to native categories
           only (no plugins) to avoid timeouts on large plugin libraries.
        """
        # Fast path: decode and navigate directly using the URI structure.
        item = self._navigate_uri_directly(browser_or_item, uri)
        if item is not None:
            return item

        # Slow path: recursive search across native categories only.
        try:
            if hasattr(browser_or_item, "uri") and browser_or_item.uri == uri:
                return browser_or_item
            if current_depth >= max_depth:
                return None
            if hasattr(browser_or_item, "instruments"):
                for attr in self._BROWSER_CATEGORIES.values():
                    category = getattr(browser_or_item, attr, None)
                    if category:
                        found = self._find_browser_item_by_uri(
                            category, uri, max_depth, current_depth + 1)
                        if found:
                            return found
                return None
            if hasattr(browser_or_item, "children") and browser_or_item.children:
                for child in browser_or_item.children:
                    found = self._find_browser_item_by_uri(
                        child, uri, max_depth, current_depth + 1)
                    if found:
                        return found
        except Exception as e:
            self.log_message("Error in recursive URI search: {0}".format(str(e)))
        return None

    def _navigate_uri_directly(self, browser, uri):
        """Parse a 'query:' URI and navigate directly to the item.

        URI format:  query:<CategoryKey>#<part1>:<part2>:...<partN>
        Each part is URL-encoded (spaces as %20, etc.).

        Examples:
          query:AudioFx#EQ%20Eight          -> audio_effects -> EQ Eight
          query:Plugins#VST3:Valhalla%20DSP:ValhallaSupermassive
                                             -> plugins -> VST3 -> Valhalla DSP -> ValhallaSupermassive
          query:Plugins#VST:Custom:BritPre   -> plugins -> VST -> Custom -> BritPre
          query:LivePacks#www.ableton.com/0:Devices:Audio%20Effects:EQ%20Eight
                                             -> packs -> ... -> EQ Eight
        """
        try:
            if not isinstance(uri, str) or not uri.startswith("query:"):
                return None

            rest = uri[6:]  # strip "query:"
            if "#" not in rest:
                return None

            category_key, path_str = rest.split("#", 1)
            attr = self._URI_CATEGORY_MAP.get(category_key)
            if not attr:
                return None

            current = getattr(browser, attr, None)
            if current is None:
                return None

            if not path_str:
                return current  # caller asked for the root category

            # Split path on ":" and decode each segment.
            for raw_part in path_str.split(":"):
                decoded = unquote(raw_part)
                if not decoded:
                    continue
                if not hasattr(current, "children") or not current.children:
                    return None
                matched = None
                for child in current.children:
                    if hasattr(child, "name") and child.name == decoded:
                        matched = child
                        break
                if matched is None:
                    return None
                current = matched

            return current

        except Exception as e:
            self.log_message("Error in _navigate_uri_directly: {0}".format(str(e)))
            return None

    # ---------------------------------------------------------------------------
    # Name-based plugin lookup (VST3 preferred over VST2)
    # ---------------------------------------------------------------------------

    def _find_plugin_by_name(self, browser, name):
        """Find a loadable plugin by display name, preferring VST3 over VST2/VST.

        Walks browser.plugins sub-folders sorted by format priority
        (VST3 first, then VST, then anything else) and returns the first
        loadable item whose name matches exactly (case-insensitive).
        """
        try:
            plugins_cat = getattr(browser, "plugins", None)
            if not plugins_cat or not hasattr(plugins_cat, "children"):
                return None

            name_lower = name.strip().lower()

            # Rank each top-level plugin format folder.
            ranked = []
            for folder in plugins_cat.children:
                folder_name = (getattr(folder, "name", "") or "").lower()
                rank = next(
                    (i for i, prefix in enumerate(self._PLUGIN_FORMAT_PRIORITY)
                     if prefix in folder_name),
                    len(self._PLUGIN_FORMAT_PRIORITY),
                )
                ranked.append((rank, folder))
            ranked.sort(key=lambda t: t[0])

            for _, folder in ranked:
                found = self._search_children_by_name(folder, name_lower)
                if found:
                    return found
        except Exception as e:
            self.log_message("Error in _find_plugin_by_name: {0}".format(str(e)))
        return None

    def _search_children_by_name(self, item, name_lower, max_depth=6, current_depth=0):
        """Recursively search an item's children for a loadable item
        whose name matches name_lower (case-insensitive exact match).
        """
        if current_depth >= max_depth:
            return None
        if not hasattr(item, "children"):
            return None
        for child in item.children:
            child_name = (getattr(child, "name", "") or "").lower()
            if child_name == name_lower and getattr(child, "is_loadable", False):
                return child
            found = self._search_children_by_name(
                child, name_lower, max_depth, current_depth + 1)
            if found:
                return found
        return None

    def get_browser_tree(self, category_type="all"):
        app = self.application()
        if not app:
            raise RuntimeError("Could not access Live application")
        if not hasattr(app, "browser") or app.browser is None:
            raise RuntimeError("Browser is not available in the Live application")

        browser_attrs = [a for a in dir(app.browser) if not a.startswith("_")]
        result = {
            "type": category_type,
            "categories": [],
            "available_categories": browser_attrs,
        }

        def make_node(item):
            if not item:
                return None
            return {
                "name": item.name if hasattr(item, "name") else "Unknown",
                "is_folder": hasattr(item, "children") and bool(item.children),
                "is_device": hasattr(item, "is_device") and item.is_device,
                "is_loadable": hasattr(item, "is_loadable") and item.is_loadable,
                "uri": item.uri if hasattr(item, "uri") else None,
                "children": [],
            }

        cat_labels = {
            "instruments": "Instruments",
            "sounds": "Sounds",
            "drums": "Drums",
            "audio_effects": "Audio Effects",
            "midi_effects": "MIDI Effects",
        }

        for key, label in cat_labels.items():
            if (category_type == "all" or category_type == key) and hasattr(app.browser, key):
                try:
                    node = make_node(getattr(app.browser, key))
                    if node:
                        node["name"] = label
                        result["categories"].append(node)
                except Exception as e:
                    self.log_message("Error processing {0}: {1}".format(key, str(e)))

        # Append any additional browser attributes not in the standard list
        for attr in browser_attrs:
            if attr not in cat_labels and (category_type == "all" or category_type == attr):
                try:
                    item = getattr(app.browser, attr)
                    if hasattr(item, "children") or hasattr(item, "name"):
                        node = make_node(item)
                        if node:
                            node["name"] = attr.capitalize()
                            result["categories"].append(node)
                except Exception as e:
                    self.log_message("Error processing {0}: {1}".format(attr, str(e)))

        self.log_message("Browser tree generated with {0} root categories".format(
            len(result["categories"])))
        return result

    def get_browser_items_at_path(self, path):
        app = self.application()
        if not app:
            raise RuntimeError("Could not access Live application")
        if not hasattr(app, "browser") or app.browser is None:
            raise RuntimeError("Browser is not available in the Live application")

        browser_attrs = [a for a in dir(app.browser) if not a.startswith("_")]
        path_parts = [p for p in path.split("/") if p]
        if not path_parts:
            raise ValueError("Invalid path")

        root_category = path_parts[0].lower()
        current_item = None

        # Match root to a browser attribute
        std_key = self._BROWSER_CATEGORIES.get(root_category)
        if std_key and hasattr(app.browser, std_key):
            current_item = getattr(app.browser, std_key)
        else:
            for attr in browser_attrs:
                if attr.lower() == root_category:
                    try:
                        current_item = getattr(app.browser, attr)
                    except Exception:
                        pass
                    break

        if current_item is None:
            return {
                "path": path,
                "error": "Unknown or unavailable category: {0}".format(root_category),
                "available_categories": browser_attrs,
                "items": [],
            }

        # Traverse remaining path parts
        for i, part in enumerate(path_parts[1:], start=1):
            if not hasattr(current_item, "children"):
                return {
                    "path": path,
                    "error": "Item at '{0}' has no children".format("/".join(path_parts[:i])),
                    "items": [],
                }
            found = False
            for child in current_item.children:
                if hasattr(child, "name") and child.name.lower() == part.lower():
                    current_item = child
                    found = True
                    break
            if not found:
                return {
                    "path": path,
                    "error": "Path part '{0}' not found".format(part),
                    "items": [],
                }

        items = []
        if hasattr(current_item, "children"):
            items = [
                {
                    "name": child.name if hasattr(child, "name") else "Unknown",
                    "is_folder": hasattr(child, "children") and bool(child.children),
                    "is_device": hasattr(child, "is_device") and child.is_device,
                    "is_loadable": hasattr(child, "is_loadable") and child.is_loadable,
                    "uri": child.uri if hasattr(child, "uri") else None,
                }
                for child in current_item.children
            ]

        return {
            "path": path,
            "name": current_item.name if hasattr(current_item, "name") else "Unknown",
            "uri": current_item.uri if hasattr(current_item, "uri") else None,
            "is_folder": hasattr(current_item, "children") and bool(current_item.children),
            "is_device": hasattr(current_item, "is_device") and current_item.is_device,
            "is_loadable": hasattr(current_item, "is_loadable") and current_item.is_loadable,
            "items": items,
        }
