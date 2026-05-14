package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Test

class HudSpeedPacketTest {
    @Test
    fun serializesRoundedGpsSpeedInKilometersPerHour() {
        assertEquals(
            """{"type":"speed","speed_kmh":42}""",
            HudSpeedPacket.fromMetersPerSecond(11.7f).toJson()
        )
    }

    @Test
    fun serializesZeroSpeedWhenLocationHasNoSpeed() {
        assertEquals(
            """{"type":"speed","speed_kmh":0}""",
            HudSpeedPacket.unknown().toJson()
        )
    }
}