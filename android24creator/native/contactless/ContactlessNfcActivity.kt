package com.mn24.contactless

import android.nfc.NdefMessage
import android.nfc.NdefRecord
import android.nfc.NfcAdapter
import android.nfc.Tag
import android.nfc.tech.Ndef
import android.nfc.tech.NdefFormatable
import android.os.Bundle
import android.app.Activity
import java.nio.charset.Charset

/**
 * Native NFC NDEF reader/writer sample for Android/Honor devices.
 * This is for exchanging a short, non-sensitive handoff URL only.
 * It is NOT an EMV payment terminal, card emulator, or banking implementation.
 */
class ContactlessNfcActivity : Activity(), NfcAdapter.ReaderCallback {
    private var adapter: NfcAdapter? = null
    @Volatile private var pendingUrl: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        adapter = NfcAdapter.getDefaultAdapter(this)
        // Bind this Activity to the existing AppBuilder UI and show a visible
        // "Ready to tap" state only when adapter?.isEnabled == true.
    }

    override fun onResume() {
        super.onResume()
        adapter?.enableReaderMode(
            this,
            this,
            NfcAdapter.FLAG_READER_NFC_A or
                NfcAdapter.FLAG_READER_NFC_B or
                NfcAdapter.FLAG_READER_NFC_F or
                NfcAdapter.FLAG_READER_NFC_V,
            Bundle().apply { putInt(NfcAdapter.EXTRA_READER_PRESENCE_CHECK_DELAY, 250) }
        )
    }

    override fun onPause() {
        adapter?.disableReaderMode(this)
        super.onPause()
    }

    fun queueHttpsHandoff(url: String) {
        require(url.startsWith("https://")) { "Only HTTPS handoff links are allowed" }
        require(url.length <= 2048) { "Handoff URL too long" }
        pendingUrl = url
    }

    override fun onTagDiscovered(tag: Tag) {
        val url = pendingUrl ?: return
        val record = NdefRecord.createUri(url)
        val message = NdefMessage(arrayOf(record))
        val ndef = Ndef.get(tag)
        try {
            if (ndef != null) {
                ndef.connect()
                if (!ndef.isWritable || message.toByteArray().size > ndef.maxSize) return
                ndef.writeNdefMessage(message)
                ndef.close()
                pendingUrl = null
                runOnUiThread {
                    // Notify the AppBuilder UI: "NFC handoff written".
                }
                return
            }
            val formatable = NdefFormatable.get(tag) ?: return
            formatable.connect()
            formatable.format(message)
            formatable.close()
            pendingUrl = null
            runOnUiThread {
                // Notify the AppBuilder UI: "NFC tag formatted and written".
            }
        } catch (_: Exception) {
            // Surface a generic failure to the UI; never log tokens or payloads.
            try { ndef?.close() } catch (_: Exception) {}
        }
    }
}
