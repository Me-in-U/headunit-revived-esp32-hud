package com.zoelowell.headunithudbridge

class RetryBackoff(
    private val initialDelayMillis: Long,
    private val maxDelayMillis: Long
) {
    private var nextDelayMillis = initialDelayMillis

    fun nextDelayMillis(): Long {
        val delay = nextDelayMillis
        nextDelayMillis = (nextDelayMillis * 2).coerceAtMost(maxDelayMillis)
        return delay
    }

    fun reset() {
        nextDelayMillis = initialDelayMillis
    }
}