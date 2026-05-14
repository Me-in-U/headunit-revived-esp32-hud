package com.zoelowell.headunithudbridge

data class NavigationFreshnessSample(
    val distanceMeters: Int,
    val timeSeconds: Int,
    val eventType: Int,
    val turnSide: Int,
    val road: String,
    val distanceAgeMs: Long,
    val turnAgeMs: Long,
    val clusterAgeMs: Long
) {
    val displaySignature: String
        get() = listOf(
            distanceMeters,
            timeSeconds,
            eventType,
            turnSide,
            road
        ).joinToString("|")

    val freshnessAgeMs: Long
        get() = minKnownAge(distanceAgeMs, turnAgeMs, clusterAgeMs)

    companion object {
        const val UNKNOWN_AGE = Long.MAX_VALUE

        private fun minKnownAge(vararg ages: Long): Long {
            return ages
                .filter { it >= 0L && it != UNKNOWN_AGE }
                .minOrNull()
                ?: UNKNOWN_AGE
        }
    }
}

class NavigationFreshnessGate(
    private val staleRegressionMarginMs: Long = DEFAULT_STALE_REGRESSION_MARGIN_MS,
    private val staleChangedValueAgeMs: Long = DEFAULT_STALE_CHANGED_VALUE_AGE_MS
) {
    private var lastAccepted: NavigationFreshnessSample? = null

    fun shouldAccept(sample: NavigationFreshnessSample): Boolean {
        val previous = lastAccepted
        if (previous == null) {
            lastAccepted = sample
            return true
        }

        if (sample.displaySignature == previous.displaySignature) {
            if (sample.isFresherThan(previous)) {
                lastAccepted = sample
            }
            return true
        }

        if (sample.isChangedValueFromStaleSnapshot(previous, staleChangedValueAgeMs)) {
            return false
        }

        if (sample.isClearlyOlderThan(previous, staleRegressionMarginMs)) {
            return false
        }

        lastAccepted = sample
        return true
    }

    fun reset() {
        lastAccepted = null
    }

    private fun NavigationFreshnessSample.isFresherThan(other: NavigationFreshnessSample): Boolean {
        return freshnessAgeMs != NavigationFreshnessSample.UNKNOWN_AGE &&
            (other.freshnessAgeMs == NavigationFreshnessSample.UNKNOWN_AGE || freshnessAgeMs < other.freshnessAgeMs)
    }

    private fun NavigationFreshnessSample.isClearlyOlderThan(
        other: NavigationFreshnessSample,
        marginMs: Long
    ): Boolean {
        if (freshnessAgeMs == NavigationFreshnessSample.UNKNOWN_AGE ||
            other.freshnessAgeMs == NavigationFreshnessSample.UNKNOWN_AGE
        ) {
            return false
        }
        return freshnessAgeMs > other.freshnessAgeMs + marginMs
    }

    private fun NavigationFreshnessSample.isChangedValueFromStaleSnapshot(
        other: NavigationFreshnessSample,
        maxAgeMs: Long
    ): Boolean {
        return displaySignature != other.displaySignature &&
            freshnessAgeMs.isKnownAndOlderThan(maxAgeMs)
    }

    private fun Long.isKnownAndOlderThan(maxAgeMs: Long): Boolean {
        return this != NavigationFreshnessSample.UNKNOWN_AGE && this > maxAgeMs
    }

    companion object {
        const val DEFAULT_STALE_REGRESSION_MARGIN_MS = 1500L
        const val DEFAULT_STALE_CHANGED_VALUE_AGE_MS = 1500L
    }
}
