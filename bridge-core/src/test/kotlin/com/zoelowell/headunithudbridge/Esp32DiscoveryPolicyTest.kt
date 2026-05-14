package com.zoelowell.headunithudbridge

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class Esp32DiscoveryPolicyTest {
    @Test
    fun skipsAutomaticDiscoveryWhenTargetIsAlreadyKnown() {
        assertFalse(Esp32DiscoveryPolicy.shouldStartAfterHudSend(hasKnownTarget = true))
    }

    @Test
    fun startsAutomaticDiscoveryWhenTargetIsUnknown() {
        assertTrue(Esp32DiscoveryPolicy.shouldStartAfterHudSend(hasKnownTarget = false))
    }

    @Test
    fun retriesOnlyWhenHeadunitIsOnlineAndEspIsNotConnected() {
        assertFalse(
            Esp32DiscoveryPolicy.shouldRetry(
                headunitState = HeadunitObservedState.WAITING_FOR_BROADCAST,
                espConnectionState = EspConnectionObservedState.DISCONNECTED
            )
        )
        assertFalse(
            Esp32DiscoveryPolicy.shouldRetry(
                headunitState = HeadunitObservedState.NAVIGATION_ACTIVE,
                espConnectionState = EspConnectionObservedState.CONNECTED
            )
        )
        assertTrue(
            Esp32DiscoveryPolicy.shouldRetry(
                headunitState = HeadunitObservedState.PROJECTION_ACTIVE,
                espConnectionState = EspConnectionObservedState.DISCONNECTED
            )
        )
    }
}