package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Test

class RetryBackoffTest {
    @Test
    fun doublesDelayUntilMaximum() {
        val backoff = RetryBackoff(initialDelayMillis = 5_000L, maxDelayMillis = 30_000L)

        assertEquals(5_000L, backoff.nextDelayMillis())
        assertEquals(10_000L, backoff.nextDelayMillis())
        assertEquals(20_000L, backoff.nextDelayMillis())
        assertEquals(30_000L, backoff.nextDelayMillis())
        assertEquals(30_000L, backoff.nextDelayMillis())
    }

    @Test
    fun resetReturnsToInitialDelay() {
        val backoff = RetryBackoff(initialDelayMillis = 5_000L, maxDelayMillis = 30_000L)

        backoff.nextDelayMillis()
        backoff.nextDelayMillis()
        backoff.reset()

        assertEquals(5_000L, backoff.nextDelayMillis())
    }
}