/* MN24 Clipboard Bridge — browser adapter.
 * Clipboard reads/writes must be called from a user gesture. Browser support
 * generally requires HTTPS or localhost and may prompt for permission.
 */
(function (root) {
  "use strict";
  const api = {
    async copyText(value) {
      if (typeof value !== "string") throw new TypeError("value must be a string");
      if (!navigator.clipboard || !navigator.clipboard.writeText) {
        throw new Error("Clipboard write is not supported in this browser/context");
      }
      await navigator.clipboard.writeText(value);
      return true;
    },
    async pasteText() {
      if (!navigator.clipboard || !navigator.clipboard.readText) {
        throw new Error("Clipboard read is not supported in this browser/context");
      }
      return await navigator.clipboard.readText();
    }
  };
  root.MN24Clipboard = Object.freeze(api);
})(globalThis);
