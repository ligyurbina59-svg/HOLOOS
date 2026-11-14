import sys
import types
import unittest
from unittest.mock import patch

from integrations.clipboard.clipboard import MN24Clipboard


class FakeScrap(types.ModuleType):
    SCRAP_TEXT = "text"
    def __init__(self):
        super().__init__("pygame.scrap")
        self.initialized = False
        self.payload = None
    def get_init(self):
        return self.initialized
    def init(self):
        self.initialized = True
    def put(self, kind, payload):
        self.payload = payload
    def get(self, kind):
        return self.payload


class ClipboardTests(unittest.TestCase):
    def setUp(self):
        self.scrap = FakeScrap()
        pygame = types.ModuleType("pygame")
        pygame.__path__ = []
        pygame.scrap = self.scrap
        self.modules = patch.dict(sys.modules, {"pygame": pygame, "pygame.scrap": self.scrap})
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def test_initialize(self):
        MN24Clipboard.initialize()
        self.assertTrue(self.scrap.initialized)

    def test_copy_and_paste_utf8(self):
        MN24Clipboard.copy_text("Hola, mundo 🌎")
        self.assertEqual(self.scrap.payload, "Hola, mundo 🌎".encode("utf-8") + b"\\0")
        self.assertEqual(MN24Clipboard.paste_text(), "Hola, mundo 🌎")

    def test_empty_clipboard(self):
        self.assertEqual(MN24Clipboard.paste_text(), "")

    def test_reject_non_string(self):
        with self.assertRaises(TypeError):
            MN24Clipboard.copy_text(123)


if __name__ == "__main__":
    unittest.main()
