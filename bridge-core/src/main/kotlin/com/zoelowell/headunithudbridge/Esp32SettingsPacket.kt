package com.zoelowell.headunithudbridge

data class Esp32SettingsPacket(
    val debugOverlay: Boolean,
    val speedUnitVisible: Boolean,
    val speedFontSize: Int = DEFAULT_SPEED_FONT_SIZE,
    val hudLanguage: String = DEFAULT_LANGUAGE
) {
    fun toJson(): String {
        val cleanSpeedFontSize = speedFontSize.coerceIn(MIN_SPEED_FONT_SIZE, MAX_SPEED_FONT_SIZE)
        val cleanLanguage = cleanLanguage(hudLanguage)
        return """{"type":"settings","debug_overlay":$debugOverlay,"speed_unit_visible":$speedUnitVisible,"speed_font_size":$cleanSpeedFontSize,"language":"$cleanLanguage"}"""
    }

    companion object {
        const val TYPE_SETTINGS = "settings"
        const val FIELD_TYPE = "type"
        const val FIELD_DEBUG_OVERLAY = "debug_overlay"
        const val FIELD_SPEED_UNIT_VISIBLE = "speed_unit_visible"
        const val FIELD_SPEED_FONT_SIZE = "speed_font_size"
        const val FIELD_LANGUAGE = "language"
        const val LANGUAGE_KOREAN = "ko"
        const val LANGUAGE_ENGLISH = "en"
        const val DEFAULT_LANGUAGE = LANGUAGE_KOREAN
        const val DEFAULT_SPEED_FONT_SIZE = 4
        const val MIN_SPEED_FONT_SIZE = 2
        const val MAX_SPEED_FONT_SIZE = 6

        fun cleanLanguage(value: String): String {
            return when (value) {
                LANGUAGE_KOREAN, LANGUAGE_ENGLISH -> value
                else -> DEFAULT_LANGUAGE
            }
        }
    }
}
