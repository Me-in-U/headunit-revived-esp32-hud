package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class HudBridgeStateTest {
    @Test
    fun projectionRequestClearsNavigationDisplayWhenNoGuidanceWasSeen() {
        val state = HudBridgeState()

        assertEquals(HudNavigationPacket.inactive().toHudJson(), state.onProjectionRequest())
        assertNull(state.payloadForRefresh())
        assertEquals(HeadunitObservedState.PROJECTION_ACTIVE, state.statusSnapshot().headunitState)
        assertEquals(HudOutputState.NAVIGATION_INACTIVE, state.statusSnapshot().hudOutputState)
    }

    @Test
    fun navigationPacketIsReplayedWhenEsp32TargetRefreshesLater() {
        val state = HudBridgeState()
        val packet = activePacket(distanceMeters = 42)

        assertEquals(packet.toHudJson(), state.onNavigationPacket(packet))
        assertEquals(packet.toHudJson(), state.payloadForRefresh())
        assertEquals(HeadunitObservedState.NAVIGATION_ACTIVE, state.statusSnapshot().headunitState)
        assertEquals(HudOutputState.NAVIGATION_GUIDANCE, state.statusSnapshot().hudOutputState)
    }

    @Test
    fun inactiveNavigationPacketClearsReplayWithoutWaitingState() {
        val state = HudBridgeState()
        state.onProjectionRequest()
        state.onNavigationPacket(activePacket())

        assertEquals(HudNavigationPacket.inactive().toHudJson(), state.onNavigationPacket(HudNavigationPacket.inactive()))
        assertNull(state.payloadForRefresh())
        assertEquals(HeadunitObservedState.PROJECTION_ACTIVE, state.statusSnapshot().headunitState)
        assertEquals(HudOutputState.NAVIGATION_INACTIVE, state.statusSnapshot().hudOutputState)
    }

    @Test
    fun refreshBeforeHeadunitActivityDoesNothing() {
        val state = HudBridgeState()

        assertNull(state.payloadForRefresh())
        assertEquals(HeadunitObservedState.WAITING_FOR_BROADCAST, state.statusSnapshot().headunitState)
        assertEquals(HudOutputState.NONE, state.statusSnapshot().hudOutputState)
    }

    private fun activePacket(distanceMeters: Int = 120): HudNavigationPacket {
        return HudNavigationPacket(
            distanceMeters = distanceMeters,
            timeSeconds = 30,
            road = "서초대로",
            eventType = HeadunitNavEvent.TURN,
            turnSide = TurnSide.RIGHT,
            turnNumber = -1,
            turnAngle = -1
        )
    }
}