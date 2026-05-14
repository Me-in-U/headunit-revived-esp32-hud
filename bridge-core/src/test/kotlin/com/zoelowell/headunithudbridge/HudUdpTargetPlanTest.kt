package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Test

class HudUdpTargetPlanTest {
    @Test
    fun usesBroadcastWhenNoEsp32TargetIsKnown() {
        assertEquals(
            listOf(HudUdpTarget("255.255.255.255", 4210)),
            HudUdpTargetPlan.forTarget(host = null, port = 4210)
        )
    }

    @Test
    fun sendsOnlyToSavedEsp32WhenTargetIsKnown() {
        assertEquals(
            listOf(HudUdpTarget("10.233.116.145", 4210)),
            HudUdpTargetPlan.forTarget(host = "10.233.116.145", port = 4210)
        )
    }

    @Test
    fun doesNotDuplicateBroadcastTarget() {
        assertEquals(
            listOf(HudUdpTarget("255.255.255.255", 4210)),
            HudUdpTargetPlan.forTarget(host = "255.255.255.255", port = 4210)
        )
    }
}