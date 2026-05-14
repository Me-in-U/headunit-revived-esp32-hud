package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Test

class BridgeUpdateIntervalsTest {
    @Test
    fun speedReplayUsesHalfSecondInterval() {
        assertEquals(500L, BridgeUpdateIntervals.SPEED_REPLAY_MILLIS)
    }
}