package com.zoelowell.headunithudbridge

object HudUdpPayloadSequencer {
    private var lastSequence = 0L

    @Synchronized
    fun wrap(payload: String, nowMillis: Long): String {
        val sequence = if (nowMillis > lastSequence) nowMillis else lastSequence + 1L
        lastSequence = sequence
        return addSequence(payload, sequence)
    }

    internal fun addSequence(payload: String, sequence: Long): String {
        val trimmed = payload.trimStart()
        require(trimmed.startsWith("{")) { "HUD UDP payload must be a JSON object" }

        val prefixLength = payload.length - trimmed.length
        val prefix = payload.substring(0, prefixLength)
        return if (trimmed == "{}") {
            """${prefix}{"seq":$sequence}"""
        } else {
            """${prefix}{"seq":$sequence,${trimmed.drop(1)}"""
        }
    }

    @Synchronized
    internal fun resetForTest() {
        lastSequence = 0L
    }
}