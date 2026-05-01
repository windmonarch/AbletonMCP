# AbletonMCPArrangement/commands_scenes.py
# Handlers for Scene commands.
from __future__ import absolute_import, print_function, unicode_literals


class SceneCommands:
    """Mixin providing Scene command handlers."""

    def _get_scenes(self):
        scenes = []
        for i, scene in enumerate(self._song.scenes):
            scenes.append({
                "index": i,
                "name": scene.name,
                "tempo": scene.tempo,
                "is_triggered": scene.is_triggered,
            })
        return {"scenes": scenes, "count": len(scenes)}

    def _create_scene(self, index=-1):
        self._song.create_scene(index)
        new_index = len(self._song.scenes) - 1 if index == -1 else index
        scene = self._song.scenes[new_index]
        return {"index": new_index, "name": scene.name}

    def _delete_scene(self, scene_index):
        if scene_index < 0 or scene_index >= len(self._song.scenes):
            raise IndexError("Scene index out of range")
        self._song.delete_scene(scene_index)
        return {"deleted": True}

    def _fire_scene(self, scene_index):
        if scene_index < 0 or scene_index >= len(self._song.scenes):
            raise IndexError("Scene index out of range")
        self._song.scenes[scene_index].fire()
        return {"fired": True, "scene_index": scene_index}

    def _set_scene_name(self, scene_index, name):
        if scene_index < 0 or scene_index >= len(self._song.scenes):
            raise IndexError("Scene index out of range")
        self._song.scenes[scene_index].name = name
        return {"name": self._song.scenes[scene_index].name}

    def _set_scene_tempo(self, scene_index, tempo):
        if scene_index < 0 or scene_index >= len(self._song.scenes):
            raise IndexError("Scene index out of range")
        scene = self._song.scenes[scene_index]
        scene.tempo = float(tempo)
        return {"tempo": scene.tempo}
