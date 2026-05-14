package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class SpeedFaceLayoutTest {
    @Test
    fun placesUnitNextToSpeedLowerRightNotScreenLowerRight() {
        val layout = SpeedFaceLayout.calculate(
            speedText = "55",
            unitText = "km/h",
            unitVisible = true,
            containerWidth = 128f,
            containerHeight = 64f,
            speedGlyphHeight = 48f,
            unitGlyphHeight = 8f
        )

        assertEquals(layout.speedRight + SpeedFaceLayout.UNIT_GAP_RATIO * 48f, layout.unitLeft, 0.001f)
        assertEquals(layout.speedBottom - 8f, layout.unitTop, 0.001f)
        assertTrue(layout.unitRight < 128f)
        assertTrue(layout.unitRight < 126f)
    }

    @Test
    fun centersSpeedAloneWhenUnitIsHidden() {
        val layout = SpeedFaceLayout.calculate(
            speedText = "55",
            unitText = "km/h",
            unitVisible = false,
            containerWidth = 128f,
            containerHeight = 64f,
            speedGlyphHeight = 48f,
            unitGlyphHeight = 8f
        )

        assertEquals((128f - layout.speedWidth) / 2f, layout.speedLeft, 0.001f)
        assertEquals(0f, layout.unitWidth, 0.001f)
    }
}