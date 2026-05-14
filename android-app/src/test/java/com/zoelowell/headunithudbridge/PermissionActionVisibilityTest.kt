package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Test

class PermissionActionVisibilityTest {
    @Test
    fun hidesAllActionsWhenPermissionsAndBackgroundAreAllowed() {
        val visibility = PermissionActionVisibility.from(
            missingRuntimePermissionCount = 0,
            batteryOptimizationIgnored = true
        )

        assertEquals(false, visibility.showRuntimePermissionButton)
        assertEquals(false, visibility.showBatteryOptimizationButton)
        assertEquals(false, visibility.showActionsRow)
    }

    @Test
    fun showsOnlyRuntimePermissionButtonWhenRuntimePermissionsAreMissing() {
        assertEquals(
            PermissionActionVisibility(
                showRuntimePermissionButton = true,
                showBatteryOptimizationButton = false
            ),
            PermissionActionVisibility.from(
                missingRuntimePermissionCount = 2,
                batteryOptimizationIgnored = true
            )
        )
    }

    @Test
    fun showsOnlyBatteryButtonWhenBackgroundRestrictionCanApply() {
        assertEquals(
            PermissionActionVisibility(
                showRuntimePermissionButton = false,
                showBatteryOptimizationButton = true
            ),
            PermissionActionVisibility.from(
                missingRuntimePermissionCount = 0,
                batteryOptimizationIgnored = false
            )
        )
    }
}
