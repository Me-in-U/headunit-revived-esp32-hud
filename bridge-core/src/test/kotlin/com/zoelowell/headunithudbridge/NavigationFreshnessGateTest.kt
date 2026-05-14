package com.zoelowell.headunithudbridge

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class NavigationFreshnessGateTest {
    @Test
    fun rejectsOlderRegressionAfterFreshChangedValue() {
        val gate = NavigationFreshnessGate()

        assertTrue(gate.shouldAccept(sample(distanceMeters = 1400, distanceAgeMs = 2)))
        assertFalse(gate.shouldAccept(sample(distanceMeters = 1500, distanceAgeMs = 1501)))
        assertTrue(gate.shouldAccept(sample(distanceMeters = 1300, distanceAgeMs = 4)))
    }

    @Test
    fun acceptsSameValueEvenWhenAgeIncreases() {
        val gate = NavigationFreshnessGate()

        assertTrue(gate.shouldAccept(sample(distanceMeters = 1400, distanceAgeMs = 2)))
        assertTrue(gate.shouldAccept(sample(distanceMeters = 1400, distanceAgeMs = 1500)))
        assertFalse(gate.shouldAccept(sample(distanceMeters = 1500, distanceAgeMs = 1501)))
    }

    @Test
    fun acceptsUnknownAgeBecauseFreshnessCannotBeProven() {
        val gate = NavigationFreshnessGate()

        assertTrue(gate.shouldAccept(sample(distanceMeters = 1400, distanceAgeMs = 2)))
        assertTrue(gate.shouldAccept(sample(distanceMeters = 1500, distanceAgeMs = -1)))
    }

    @Test
    fun rejectsOlderNavigationValue() {
        val gate = NavigationFreshnessGate()

        assertTrue(gate.shouldAccept(sample(distanceMeters = 1400, distanceAgeMs = 2)))
        assertFalse(gate.shouldAccept(sample(distanceMeters = 1500, distanceAgeMs = 1501)))
    }

    @Test
    fun rejectsChangedValueFromStaleNavigationSnapshot() {
        val gate = NavigationFreshnessGate()

        assertTrue(gate.shouldAccept(sample(distanceMeters = 364, distanceAgeMs = 2)))
        assertTrue(gate.shouldAccept(sample(distanceMeters = 365, distanceAgeMs = 1200)))
        assertTrue(gate.shouldAccept(sample(distanceMeters = 366, distanceAgeMs = 1500)))
        assertFalse(gate.shouldAccept(sample(distanceMeters = 4000, distanceAgeMs = 1501)))
        assertTrue(gate.shouldAccept(sample(distanceMeters = 309, distanceAgeMs = 93)))
    }

    @Test
    fun resetAllowsNextRouteToStartFresh() {
        val gate = NavigationFreshnessGate()

        assertTrue(gate.shouldAccept(sample(distanceMeters = 1400, distanceAgeMs = 2)))
        gate.reset()
        assertTrue(gate.shouldAccept(sample(distanceMeters = 1500, distanceAgeMs = 1200)))
    }

    private fun sample(
        distanceMeters: Int,
        distanceAgeMs: Long,
        timeSeconds: Int = 62
    ): NavigationFreshnessSample {
        return NavigationFreshnessSample(
            distanceMeters = distanceMeters,
            timeSeconds = timeSeconds,
            eventType = HeadunitNavEvent.NAME_CHANGE.wireValue,
            turnSide = TurnSide.UNSPECIFIED.wireValue,
            road = "터널 진입",
            distanceAgeMs = distanceAgeMs,
            turnAgeMs = -1L,
            clusterAgeMs = -1L
        )
    }
}
