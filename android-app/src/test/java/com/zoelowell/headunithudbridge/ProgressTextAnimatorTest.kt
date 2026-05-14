package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Test

class ProgressTextAnimatorTest {
    @Test
    fun padsProgressDotsEveryHalfSecond() {
        assertEquals("Wi-Fi 검색중   ", ProgressTextAnimator.animate("Wi-Fi 검색중", 0L))
        assertEquals("Wi-Fi 검색중.  ", ProgressTextAnimator.animate("Wi-Fi 검색중", 500L))
        assertEquals("Wi-Fi 검색중.. ", ProgressTextAnimator.animate("Wi-Fi 검색중", 1_000L))
        assertEquals("Wi-Fi 검색중...", ProgressTextAnimator.animate("Wi-Fi 검색중", 1_500L))
        assertEquals("Wi-Fi 검색중   ", ProgressTextAnimator.animate("Wi-Fi 검색중", 2_000L))
    }

    @Test
    fun stripsExistingDotsBeforeAnimatingNextFrame() {
        assertEquals("진행중.. ", ProgressTextAnimator.animate("진행중.", 1_000L))
        assertEquals("연결중.  · Wi-Fi 검색중.  ", ProgressTextAnimator.animate("연결중... · Wi-Fi 검색중.", 500L))
    }

    @Test
    fun leavesCompletedTextUnchanged() {
        assertEquals("Wi-Fi 검색됨", ProgressTextAnimator.animate("Wi-Fi 검색됨", 500L))
        assertEquals("ESP32 연결됨", ProgressTextAnimator.animate("ESP32 연결됨", 500L))
    }
}
