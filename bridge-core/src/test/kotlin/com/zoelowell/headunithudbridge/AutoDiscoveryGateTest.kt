package com.zoelowell.headunithudbridge

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AutoDiscoveryGateTest {
    @Test
    fun defersProvisioningDiscoveryUntilAndroidAutoIsActive() {
        val gate = AutoDiscoveryGate()

        assertFalse(gate.onProvisioningReady())
        assertTrue(gate.onAndroidAutoActive())
    }

    @Test
    fun startsProvisioningDiscoveryImmediatelyWhenAndroidAutoIsAlreadyActive() {
        val gate = AutoDiscoveryGate()

        assertFalse(gate.onAndroidAutoActive())
        assertTrue(gate.onProvisioningReady())
    }

    @Test
    fun ignoresDuplicateAndroidAutoSignalsAfterPendingDiscoveryStarts() {
        val gate = AutoDiscoveryGate()

        assertFalse(gate.onProvisioningReady())
        assertTrue(gate.onAndroidAutoActive())
        assertFalse(gate.onAndroidAutoActive())
    }
}