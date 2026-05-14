package com.zoelowell.headunithudbridge

class AutoDiscoveryGate {
    private var androidAutoActive = false
    private var pendingProvisioningDiscovery = false

    fun onProvisioningReady(): Boolean {
        if (androidAutoActive) {
            pendingProvisioningDiscovery = false
            return true
        }

        pendingProvisioningDiscovery = true
        return false
    }

    fun onAndroidAutoActive(): Boolean {
        androidAutoActive = true
        if (!pendingProvisioningDiscovery) {
            return false
        }

        pendingProvisioningDiscovery = false
        return true
    }
}