package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Test

class HudSpeedStateTest {
    @Test
    fun returnsLatestSpeedPacket() {
        val state = HudSpeedState()
        state.update(HudSpeedPacket(speedKmh = 52))

        assertEquals(
            HudSpeedPacket(speedKmh = 52),
            state.currentPacket()
        )
    }

    @Test
    fun startsWithStationarySpeed() {
        assertEquals(HudSpeedPacket(speedKmh = 0), HudSpeedState().currentPacket())
    }
}