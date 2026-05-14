package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class SpeedDigitGlyphTest {
    @Test
    fun definesSegmentsForAllSpeedDigits() {
        ('0'..'9').forEach { digit ->
            assertTrue(
                "digit $digit should have drawable segments",
                SpeedDigitGlyph.segments(digit, cellWidth = 24f, glyphHeight = 32f).isNotEmpty()
            )
        }
    }

    @Test
    fun sevenUsesFlatTopShortRightStemAndDiagonal() {
        val segments = SpeedDigitGlyph.segments('7', cellWidth = 24f, glyphHeight = 32f)

        assertEquals(3, segments.size)
        assertTrue(segments[0].endX > segments[0].startX)
        assertEquals(segments[0].startY, segments[0].endY, 0.001f)
        assertEquals(segments[1].startX, segments[1].endX, 0.001f)
        assertTrue(segments[1].endY > segments[1].startY)
        assertEquals(segments[1].endX, segments[2].startX, 0.001f)
        assertEquals(segments[1].endY, segments[2].startY, 0.001f)
        assertTrue(segments[2].endX < segments[2].startX)
        assertTrue(segments[2].endY > segments[2].startY)
    }

    @Test
    fun definesStrokeGlyphsForDistanceAndSpeedUnits() {
        listOf('m', 'k', 'h', '/', '.', ':').forEach { char ->
            assertTrue(
                "unit char $char should have drawable segments",
                SpeedDigitGlyph.segments(char, cellWidth = 24f, glyphHeight = 32f).isNotEmpty()
            )
        }
    }

    @Test
    fun givesWideGlyphAdvanceToLowercaseM() {
        assertTrue(SpeedDigitGlyph.advanceRatio('m') > SpeedDigitGlyph.advanceRatio('k'))
    }

    @Test
    fun unitMAndHUseAxisAlignedStrokesForSmallOledReadability() {
        listOf('m', 'h').forEach { char ->
            SpeedDigitGlyph.segments(char, cellWidth = 24f, glyphHeight = 32f).forEach { segment ->
                val isVertical = segment.startX == segment.endX
                val isHorizontal = segment.startY == segment.endY
                assertTrue("$char segment should be vertical or horizontal", isVertical || isHorizontal)
            }
        }
    }

    @Test
    fun unitMUsesEvenlySpacedVerticalStems() {
        val verticals = SpeedDigitGlyph.segments('m', cellWidth = 24f, glyphHeight = 32f)
            .filter { it.startX == it.endX }
            .map { it.startX }

        assertEquals(3, verticals.size)
        assertEquals(verticals[1] - verticals[0], verticals[2] - verticals[1], 0.001f)
    }

    @Test
    fun unitHRightStemDoesNotProtrudeAboveCrossbar() {
        val segments = SpeedDigitGlyph.segments('h', cellWidth = 24f, glyphHeight = 32f)
        val crossbar = segments[1]
        val rightStem = segments[2]

        assertEquals(crossbar.startY, rightStem.startY, 0.001f)
    }
}