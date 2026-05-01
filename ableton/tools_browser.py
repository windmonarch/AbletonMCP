# ableton/tools_browser.py
# MCP tools for Ableton's browser (instruments, effects, samples).
import json
from mcp.server.fastmcp import FastMCP, Context
from .connection import get_ableton_connection


def register(mcp: FastMCP):
    """Register all browser tools onto the FastMCP instance."""

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

            def format_tree(item, indent=0):
                if not item:
                    return ""
                prefix = "  " * indent
                name = item.get("name", "Unknown")
                path = item.get("path", "")
                suffix = " [...]" if item.get("has_more") else ""
                path_str = f" (path: {path})" if path else ""
                lines = [f"{prefix}- {name}{path_str}{suffix}"]
                for child in item.get("children", []):
                    lines.append(format_tree(child, indent + 1))
                return "\n".join(lines)

            sections = [f"Browser tree for '{category_type}':\n"]
            for category in result.get("categories", []):
                sections.append(format_tree(category))
            return "\n".join(sections)
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
    def load_drum_kit(ctx: Context, track_index: int, rack_uri: str, kit_path: str) -> str:
        """
        Load a drum rack and then a specific drum kit into it.

        Parameters:
        - track_index: The index of the track to load on
        - rack_uri: URI of the drum rack to load
        - kit_path: Browser path to the folder containing drum kits (e.g. 'drums' to load the first kit in the Drums category)
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

            # Filter for loadable preset files only (exclude devices like Drum Rack itself)
            loadable = [
                i for i in kit_result.get("items", [])
                if i.get("is_loadable", False) and not i.get("is_device", False)
            ]
            if not loadable:
                return f"Loaded drum rack but no loadable kits found at '{kit_path}'"

            kit_uri = loadable[0].get("uri")
            ableton.send_command("load_browser_item", {"track_index": track_index, "item_uri": kit_uri})
            return f"Loaded drum rack and kit '{loadable[0].get('name')}' on track {track_index}"
        except Exception as e:
            return f"Error loading drum kit: {str(e)}"
