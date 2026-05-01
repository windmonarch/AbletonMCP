# AbletonMCPLocal/commands_browser.py
# Handlers for Ableton's browser (instruments, effects, samples).
from __future__ import absolute_import, print_function, unicode_literals
import traceback


class BrowserCommands:
    """Mixin providing browser command handlers."""

    # Standard browser category names to Live API attribute names
    _BROWSER_CATEGORIES = {
        "instruments": "instruments",
        "sounds": "sounds",
        "drums": "drums",
        "audio_effects": "audio_effects",
        "midi_effects": "midi_effects",
    }

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

    def _find_browser_item_by_uri(self, browser_or_item, uri, max_depth=10, current_depth=0):
        try:
            if hasattr(browser_or_item, "uri") and browser_or_item.uri == uri:
                return browser_or_item
            if current_depth >= max_depth:
                return None
            # Walk top-level browser categories
            if hasattr(browser_or_item, "instruments"):
                for attr in self._BROWSER_CATEGORIES.values():
                    category = getattr(browser_or_item, attr, None)
                    if category:
                        found = self._find_browser_item_by_uri(
                            category, uri, max_depth, current_depth + 1)
                        if found:
                            return found
                return None
            # Recurse into children
            if hasattr(browser_or_item, "children") and browser_or_item.children:
                for child in browser_or_item.children:
                    found = self._find_browser_item_by_uri(
                        child, uri, max_depth, current_depth + 1)
                    if found:
                        return found
        except Exception as e:
            self.log_message("Error finding browser item by URI: {0}".format(str(e)))
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
