package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class BleStatusPacketTest {
    @Test
    fun parsesLegacyVerboseStatus() {
        val status = BleStatusPacket.parse(
            """{"state":"connected","ip":"10.233.116.145","message":"Wi-Fi connected"}"""
        )

        assertEquals(BleProvisioningContract.STATE_CONNECTED, status?.state)
        assertEquals("10.233.116.145", status?.ipAddress)
        assertEquals("Wi-Fi connected", status?.message)
    }

    @Test
    fun parsesCompactConnectedStatus() {
        val status = BleStatusPacket.parse("""{"s":"c","i":"10.233.116.145"}""")

        assertEquals(BleProvisioningContract.STATE_CONNECTED, status?.state)
        assertEquals("10.233.116.145", status?.ipAddress)
        assertEquals(BleProvisioningContract.STATE_CONNECTED, status?.message)
    }

    @Test
    fun rejectsTruncatedJson() {
        assertNull(BleStatusPacket.parse("""{"state":"connected""""))
    }
}