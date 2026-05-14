package com.zoelowell.headunithudbridge

data class PermissionActionVisibility(
    val showRuntimePermissionButton: Boolean,
    val showBatteryOptimizationButton: Boolean
) {
    val showActionsRow: Boolean
        get() = showRuntimePermissionButton || showBatteryOptimizationButton

    companion object {
        fun from(missingRuntimePermissionCount: Int, batteryOptimizationIgnored: Boolean): PermissionActionVisibility {
            return PermissionActionVisibility(
                showRuntimePermissionButton = missingRuntimePermissionCount > 0,
                showBatteryOptimizationButton = !batteryOptimizationIgnored
            )
        }
    }
}
