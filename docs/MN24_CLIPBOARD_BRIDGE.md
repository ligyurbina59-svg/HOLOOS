# MN24 Clipboard Bridge

Cross-runtime copy/paste adapters for Android24Creator / HOLOOS.

## Components

- **Godot 4:** `examples/tesseract_4d/clipboard_manager.gd`; the demo project registers it as an autoload named `MN24Clipboard`.
- **Python/Pygame:** `integrations/clipboard/clipboard.py`; initialize after `pygame.display.set_mode()`. Pygame scrap depends on the platform and active display backend; it may not be available in Termux/Android.
- **Web:** `android24creator/clipboard.js`; exposes `MN24Clipboard.copyText(text)` and `MN24Clipboard.pasteText()`.
- **Browser test UI:** `android24creator/clipboard.html`; expects the backend to serve `android24creator/clipboard.js` at `/app/clipboard.js` and the page at `/app/clipboard`. If these paths are not mapped by the current FastAPI app, use the files directly or add explicit static routes before exposing the page.

## Usage

Godot:

```gdscript
MN24Clipboard.copy_text("Texto para copiar")
var pasted := MN24Clipboard.paste_text()
```

Pygame (after display initialization):

```python
from integrations.clipboard import MN24Clipboard
MN24Clipboard.initialize()
MN24Clipboard.copy_text("Texto para copiar")
text = MN24Clipboard.paste_text()
```

Web (call from a click/tap handler):

```javascript
await MN24Clipboard.copyText("Texto para copiar");
const text = await MN24Clipboard.pasteText();
```

## Security and platform constraints

- No clipboard history, background polling, telemetry, or server-side persistence.
- Read/write only after an explicit user action. Browser reads may require permission and a secure context (HTTPS or localhost).
- Clipboard contents can contain passwords, tokens, personal data, or other secrets. Do not log or transmit them automatically.
- Godot uses the OS clipboard API. Actual support depends on the export platform and permissions.
- Pygame scrap is not a reliable Android/Termux clipboard bridge. For native Android integration, implement a dedicated Android plugin using Android ClipboardManager; do not claim Pygame scrap support on Android without device verification.

## Tests

```bash
python -m unittest tests.test_clipboard -v
```

The tests mock `pygame.scrap`; they validate adapter behavior but do not verify OS clipboard integration on a device.
