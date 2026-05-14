package com.zoelowell.headunithudbridge

data class HudUdpTarget(
    val host: String,
    val port: Int
)

object HudUdpTargetPlan {
    const val BROADCAST_HOST = "255.255.255.255"

    fun forTarget(host: String?, port: Int): List<HudUdpTarget> {
        val targets = mutableListOf<HudUdpTarget>()
        val savedHost = host?.trim()?.takeIf { it.isNotEmpty() }

        targets += HudUdpTarget(savedHost ?: BROADCAST_HOST, port)

        return targets.distinct()
    }
}