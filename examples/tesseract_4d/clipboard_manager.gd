extends Node
class_name MN24ClipboardManager

signal text_copied
signal text_pasted(value: String)

func copy_text(value: String) -> void:
	DisplayServer.clipboard_set(value)
	text_copied.emit()

func paste_text() -> String:
	var value := DisplayServer.clipboard_get()
	text_pasted.emit(value)
	return value

func clear_clipboard() -> void:
	DisplayServer.clipboard_set("")
