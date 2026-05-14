package com.zoelowell.headunithudbridge

object Esp32DiscoveryPolicy {
    fun shouldStartAfterHudSend(hasKnownTarget: Boolean): Boolean {
        return !hasKnownTarget
    }

    fun shouldRetry(
        headunitState: HeadunitObservedState,
        espConnectionState: EspConnectionObservedState
    ): Boolean {
        return headunitState != HeadunitObservedState.WAITING_FOR_BROADCAST &&
            espConnectionState != EspConnectionObservedState.CONNECTED
    }
}