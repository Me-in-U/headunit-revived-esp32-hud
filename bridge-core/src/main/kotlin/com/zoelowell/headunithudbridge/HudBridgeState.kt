package com.zoelowell.headunithudbridge

class HudBridgeState {
    private var projectionActive = false
    private var lastActiveNavigationPayload: String? = null
    private var lastHudOutputState = HudOutputState.NONE

    fun onProjectionRequest(): String {
        projectionActive = true
        lastHudOutputState = if (lastActiveNavigationPayload != null) {
            HudOutputState.NAVIGATION_GUIDANCE
        } else {
            HudOutputState.NAVIGATION_INACTIVE
        }
        return lastActiveNavigationPayload ?: HudNavigationPacket.inactive().toHudJson()
    }

    fun onNavigationPacket(packet: HudNavigationPacket): String {
        projectionActive = true
        lastActiveNavigationPayload = if (packet.activeGuidance) {
            packet.toHudJson()
        } else {
            null
        }
        lastHudOutputState = if (packet.activeGuidance) {
            HudOutputState.NAVIGATION_GUIDANCE
        } else {
            HudOutputState.NAVIGATION_INACTIVE
        }
        return packet.toHudJson()
    }

    fun payloadForRefresh(): String? {
        return lastActiveNavigationPayload
    }

    fun statusSnapshot(): HudBridgeStatusSnapshot {
        val headunitState = when {
            lastActiveNavigationPayload != null -> HeadunitObservedState.NAVIGATION_ACTIVE
            projectionActive -> HeadunitObservedState.PROJECTION_ACTIVE
            else -> HeadunitObservedState.WAITING_FOR_BROADCAST
        }
        return HudBridgeStatusSnapshot(
            headunitState = headunitState,
            hudOutputState = lastHudOutputState
        )
    }
}

enum class HeadunitObservedState {
    WAITING_FOR_BROADCAST,
    PROJECTION_ACTIVE,
    NAVIGATION_ACTIVE
}

enum class HudOutputState {
    NONE,
    NAVIGATION_GUIDANCE,
    NAVIGATION_INACTIVE
}

data class HudBridgeStatusSnapshot(
    val headunitState: HeadunitObservedState,
    val hudOutputState: HudOutputState
)