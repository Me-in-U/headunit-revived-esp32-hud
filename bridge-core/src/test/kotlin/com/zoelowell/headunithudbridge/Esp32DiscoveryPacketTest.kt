package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Test

class Esp32DiscoveryPacketTest {
    @Test
    fun usesUdpSourceAddressBeforePayloadIp() {
        val target = Esp32DiscoveryPacket.resolveTargetHost(
            payloadIp = "8.8.8.8",
            sourceHost = "192.168.43.82"
        )

        assertEquals("192.168.43.82", target)
    }

    @Test
    fun fallsBackToPayloadIpWhenSourceAddressIsBlank() {
        val target = Esp32DiscoveryPacket.resolveTargetHost(
            payloadIp = "192.168.43.82",
            sourceHost = ""
        )

        assertEquals("192.168.43.82", target)
    }

    @Test
    fun serializesDiscoveryProbe() {
        assertEquals(
            """{"type":"headunit_hud_discover"}""",
            Esp32DiscoveryPacket.discoveryProbeJson()
        )
    }
}