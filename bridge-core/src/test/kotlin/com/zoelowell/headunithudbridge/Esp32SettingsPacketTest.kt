package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Test

class Esp32SettingsPacketTest {
    @Test
    fun serializesDebugOverlaySetting() {
        assertEquals(
            """{"type":"settings","debug_overlay":false,"speed_unit_visible":false,"speed_font_size":4,"language":"ko"}""",
            Esp32SettingsPacket(debugOverlay = false, speedUnitVisible = false, speedFontSize = 4).toJson()
        )
    }

    @Test
    fun clampsSpeedFontSizeToSupportedOledTextSizes() {
        assertEquals(
            """{"type":"settings","debug_overlay":true,"speed_unit_visible":true,"speed_font_size":2,"language":"ko"}""",
            Esp32SettingsPacket(debugOverlay = true, speedUnitVisible = true, speedFontSize = 0).toJson()
        )
        assertEquals(
            """{"type":"settings","debug_overlay":true,"speed_unit_visible":true,"speed_font_size":6,"language":"ko"}""",
            Esp32SettingsPacket(debugOverlay = true, speedUnitVisible = true, speedFontSize = 9).toJson()
        )
    }

    @Test
    fun serializesEnglishHudLanguage() {
        assertEquals(
            """{"type":"settings","debug_overlay":true,"speed_unit_visible":true,"speed_font_size":4,"language":"en"}""",
            Esp32SettingsPacket(
                debugOverlay = true,
                speedUnitVisible = true,
                speedFontSize = 4,
                hudLanguage = Esp32SettingsPacket.LANGUAGE_ENGLISH
            ).toJson()
        )
    }

    @Test
    fun fallsBackToKoreanForUnsupportedHudLanguage() {
        assertEquals(
            """{"type":"settings","debug_overlay":true,"speed_unit_visible":true,"speed_font_size":4,"language":"ko"}""",
            Esp32SettingsPacket(
                debugOverlay = true,
                speedUnitVisible = true,
                speedFontSize = 4,
                hudLanguage = "jp"
            ).toJson()
        )
    }
}
