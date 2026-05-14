package com.zoelowell.headunithudbridge

object Esp32DiscoveryPacket {
    const val DISCOVERY_PORT = 4211
    const val TYPE_DISCOVER = "headunit_hud_discover"
    const val TYPE_HELLO = "headunit_hud_hello"
    const val FIELD_TYPE = "type"
    const val FIELD_IP = "ip"
    const val FIELD_UDP_PORT = "udp_port"
    const val FIELD_NAME = "name"

    fun discoveryProbeJson(): String = """{"$FIELD_TYPE":"$TYPE_DISCOVER"}"""

    fun resolveTargetHost(payloadIp: String, sourceHost: String): String {
        return sourceHost.takeIf { it.isNotBlank() } ?: payloadIp
    }
}