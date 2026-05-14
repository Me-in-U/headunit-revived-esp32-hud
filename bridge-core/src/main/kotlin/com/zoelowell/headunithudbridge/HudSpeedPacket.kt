package com.zoelowell.headunithudbridge

import kotlin.math.roundToInt

data class HudSpeedPacket(
    val speedKmh: Int
) {
    fun toJson(): String {
        return """{"type":"$TYPE_SPEED","speed_kmh":$speedKmh}"""
    }

    companion object {
        const val TYPE_SPEED = "speed"

        fun fromMetersPerSecond(speedMetersPerSecond: Float): HudSpeedPacket {
            return HudSpeedPacket((speedMetersPerSecond * 3.6f).roundToInt().coerceAtLeast(0))
        }

        fun unknown(): HudSpeedPacket {
            return HudSpeedPacket(speedKmh = 0)
        }
    }
}