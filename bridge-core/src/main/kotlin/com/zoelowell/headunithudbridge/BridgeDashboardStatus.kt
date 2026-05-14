package com.zoelowell.headunithudbridge

data class BridgeDashboardStatus(
    val headunitState: HeadunitObservedState,
    val hudOutputState: HudOutputState,
    val espConnectionState: EspConnectionObservedState,
    val lastEvent: String,
    val lastEventTimeMillis: Long,
    val nextEspDiscoveryRetryAtMillis: Long,
    val speedKmh: Int = 0
) {
    val headunitOnline: Boolean
        get() = headunitState != HeadunitObservedState.WAITING_FOR_BROADCAST

    fun retrySecondsRemaining(nowMillis: Long): Long? {
        if (espConnectionState != EspConnectionObservedState.RETRY_WAITING) {
            return null
        }
        if (nextEspDiscoveryRetryAtMillis <= 0L) {
            return null
        }

        val remainingMillis = (nextEspDiscoveryRetryAtMillis - nowMillis).coerceAtLeast(0L)
        return (remainingMillis + 999L) / 1_000L
    }
}

enum class EspConnectionObservedState {
    DISCONNECTED,
    DISCOVERING,
    RETRY_WAITING,
    CONNECTED
}