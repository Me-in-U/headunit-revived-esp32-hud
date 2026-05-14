package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Test

class HudUdpPayloadSequencerTest {
    @Test
    fun addsSequenceAsFirstJsonField() {
        assertEquals(
            """{"seq":42,"distance_meters":300}""",
            HudUdpPayloadSequencer.addSequence("""{"distance_meters":300}""", 42L)
        )
    }

    @Test
    fun keepsSequenceIncreasingWhenClockDoesNotAdvance() {
        HudUdpPayloadSequencer.resetForTest()

        assertEquals("""{"seq":1000,"type":"speed","speed_kmh":55}""", HudUdpPayloadSequencer.wrap("""{"type":"speed","speed_kmh":55}""", 1000L))
        assertEquals("""{"seq":1001,"type":"speed","speed_kmh":56}""", HudUdpPayloadSequencer.wrap("""{"type":"speed","speed_kmh":56}""", 1000L))
    }
}