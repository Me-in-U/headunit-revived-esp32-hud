package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class BridgeDashboardStatusTest {
    @Test
    fun headunitIsOnlineAfterProjectionOrNavigationBroadcast() {
        assertFalse(status(HeadunitObservedState.WAITING_FOR_BROADCAST).headunitOnline)
        assertTrue(status(HeadunitObservedState.PROJECTION_ACTIVE).headunitOnline)
        assertTrue(status(HeadunitObservedState.NAVIGATION_ACTIVE).headunitOnline)
    }

    @Test
    fun retryCountdownRoundsUpAndClampsExpiredRetry() {
        val waiting = status(
            headunitState = HeadunitObservedState.PROJECTION_ACTIVE,
            espConnectionState = EspConnectionObservedState.RETRY_WAITING,
            nextEspDiscoveryRetryAtMillis = 15_001L
        )

        assertEquals(6L, waiting.retrySecondsRemaining(nowMillis = 10_000L))
        assertEquals(0L, waiting.retrySecondsRemaining(nowMillis = 16_000L))
    }

    @Test
    fun retryCountdownIsOnlyShownForRetryWaitingState() {
        val discovering = status(
            headunitState = HeadunitObservedState.PROJECTION_ACTIVE,
            espConnectionState = EspConnectionObservedState.DISCOVERING,
            nextEspDiscoveryRetryAtMillis = 15_000L
        )

        assertNull(discovering.retrySecondsRemaining(nowMillis = 10_000L))
    }

    private fun status(
        headunitState: HeadunitObservedState,
        espConnectionState: EspConnectionObservedState = EspConnectionObservedState.DISCONNECTED,
        nextEspDiscoveryRetryAtMillis: Long = 0L
    ): BridgeDashboardStatus {
        return BridgeDashboardStatus(
            headunitState = headunitState,
            hudOutputState = HudOutputState.NONE,
            espConnectionState = espConnectionState,
            lastEvent = "",
            lastEventTimeMillis = 0L,
            nextEspDiscoveryRetryAtMillis = nextEspDiscoveryRetryAtMillis
        )
    }
}