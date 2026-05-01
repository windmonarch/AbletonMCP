# ableton/tools_scenes.py
# MCP tools for Scene management.
import json
from mcp.server.fastmcp import FastMCP, Context
from .connection import get_ableton_connection


def register(mcp: FastMCP):
    """Register all Scene tools onto the FastMCP instance."""

    @mcp.tool()
    def get_scenes(ctx: Context) -> str:
        """Get all scenes in the Ableton session with their names and tempos."""
        try:
            result = get_ableton_connection().send_command("get_scenes")
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error getting scenes: {str(e)}"

    @mcp.tool()
    def create_scene(ctx: Context, index: int = -1) -> str:
        """
        Create a new scene in the Ableton session.

        Parameters:
        - index: Position to insert the scene (-1 = end of list)
        """
        try:
            result = get_ableton_connection().send_command("create_scene", {"index": index})
            return f"Created scene '{result['name']}' at index {result['index']}"
        except Exception as e:
            return f"Error creating scene: {str(e)}"

    @mcp.tool()
    def delete_scene(ctx: Context, scene_index: int) -> str:
        """
        Delete a scene from the Ableton session.

        Parameters:
        - scene_index: The index of the scene to delete
        """
        try:
            get_ableton_connection().send_command("delete_scene", {"scene_index": scene_index})
            return f"Deleted scene at index {scene_index}"
        except Exception as e:
            return f"Error deleting scene: {str(e)}"

    @mcp.tool()
    def fire_scene(ctx: Context, scene_index: int) -> str:
        """
        Launch all clips in a scene.

        Parameters:
        - scene_index: The index of the scene to fire
        """
        try:
            get_ableton_connection().send_command("fire_scene", {"scene_index": scene_index})
            return f"Fired scene at index {scene_index}"
        except Exception as e:
            return f"Error firing scene: {str(e)}"

    @mcp.tool()
    def set_scene_name(ctx: Context, scene_index: int, name: str) -> str:
        """
        Rename a scene.

        Parameters:
        - scene_index: The index of the scene to rename
        - name: The new name for the scene
        """
        try:
            result = get_ableton_connection().send_command("set_scene_name", {
                "scene_index": scene_index, "name": name})
            return f"Scene renamed to '{result['name']}'"
        except Exception as e:
            return f"Error setting scene name: {str(e)}"

    @mcp.tool()
    def set_scene_tempo(ctx: Context, scene_index: int, tempo: float) -> str:
        """
        Set the tempo for a scene. When this scene is launched, Ableton will switch to this tempo.
        Set to 0.0 to remove the scene tempo.

        Parameters:
        - scene_index: The index of the scene
        - tempo: The tempo in BPM (e.g. 120.0), or 0.0 to clear
        """
        try:
            result = get_ableton_connection().send_command("set_scene_tempo", {
                "scene_index": scene_index, "tempo": tempo})
            return f"Scene tempo set to {result['tempo']} BPM"
        except Exception as e:
            return f"Error setting scene tempo: {str(e)}"
