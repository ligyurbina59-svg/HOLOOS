"""Optional Pygame system clipboard adapter.

Call initialize() after pygame.display.set_mode(). This adapter uses the OS
clipboard through pygame.scrap; availability depends on the platform/display.
No clipboard history or background polling is performed.
"""
from __future__ import annotations


class MN24Clipboard:
    @staticmethod
    def _scrap():
        try:
            import pygame.scrap
        except ImportError as exc:
            raise RuntimeError("Pygame is required for the Pygame clipboard adapter") from exc
        return pygame.scrap

    @classmethod
    def initialize(cls) -> None:
        scrap = cls._scrap()
        try:
            if not scrap.get_init():
                scrap.init()
        except Exception as exc:
            raise RuntimeError("System clipboard is unavailable in this Pygame environment") from exc

    @classmethod
    def copy_text(cls, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("clipboard value must be a string")
        scrap = cls._scrap()
        try:
            if not scrap.get_init():
                scrap.init()
            scrap.put(scrap.SCRAP_TEXT, value.encode("utf-8") + b"\\0")
        except Exception as exc:
            raise RuntimeError("Could not write to the system clipboard") from exc

    @classmethod
    def paste_text(cls) -> str:
        scrap = cls._scrap()
        try:
            if not scrap.get_init():
                scrap.init()
            data = scrap.get(scrap.SCRAP_TEXT)
        except Exception as exc:
            raise RuntimeError("Could not read the system clipboard") from exc
        if not data:
            return ""
        return data.decode("utf-8", errors="replace").rstrip("\\0")
