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

    @Test
    fun treatsLegacyHeadunitHudDiscoveryAsEsp32Target() {
        assertEquals(
            HudTargetKind.ESP32,
            Esp32DiscoveryPacket.targetKindFromHello(name = "Headunit HUD", deviceKind = "")
        )
    }

    @Test
    fun treatsPiHudDiscoveryAsPiTargetByDeviceKindOrName() {
        assertEquals(
            HudTargetKind.PI_HUD,
            Esp32DiscoveryPacket.targetKindFromHello(name = "Headunit HUD", deviceKind = "pi_hud")
        )
        assertEquals(
            HudTargetKind.PI_HUD,
            Esp32DiscoveryPacket.targetKindFromHello(name = "Headunit Pi HUD", deviceKind = "")
        )
    }

    @Test
    fun sendsEsp32SettingsOnlyToEsp32Targets() {
        assertEquals(true, HudTargetKind.ESP32.receivesEsp32Settings)
        assertEquals(false, HudTargetKind.PI_HUD.receivesEsp32Settings)
    }
}
