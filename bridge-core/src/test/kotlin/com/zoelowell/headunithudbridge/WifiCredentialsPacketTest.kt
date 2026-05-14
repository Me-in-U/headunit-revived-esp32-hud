package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Test

class WifiCredentialsPacketTest {
    @Test
    fun serializesCredentialsForBleProvisioning() {
        val packet = WifiCredentialsPacket(
            ssid = "PhoneHotspot",
            password = "hotspot-password",
            udpPort = 4210
        )

        assertEquals(
            """{"ssid":"PhoneHotspot","password":"hotspot-password","udp_port":4210}""",
            packet.toJson()
        )
    }

    @Test
    fun escapesJsonStringValues() {
        val packet = WifiCredentialsPacket(
            ssid = "Phone \"HUD\"",
            password = "line\\break",
            udpPort = 4210
        )

        assertEquals(
            """{"ssid":"Phone \"HUD\"","password":"line\\break","udp_port":4210}""",
            packet.toJson()
        )
    }
}