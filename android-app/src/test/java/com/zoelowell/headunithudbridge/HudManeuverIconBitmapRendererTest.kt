package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class HudManeuverIconBitmapRendererTest {
    @Test
    fun rendersManeuverIconAsExpectedOledBitmapSize() {
        val bitmap = HudManeuverIconBitmapRenderer.render(HeadunitNavEvent.TURN, TurnSide.RIGHT)

        assertEquals(50, bitmap.width)
        assertEquals(42, bitmap.height)
        assertEquals(((50 + 7) / 8) * 42 * 2, bitmap.hex.length)
        assertTrue(bitmap.hex.any { it != '0' })
    }

    @Test
    fun mirrorsTurnIconsBySide() {
        val right = HudManeuverIconBitmapRenderer.render(HeadunitNavEvent.TURN, TurnSide.RIGHT)
        val left = HudManeuverIconBitmapRenderer.render(HeadunitNavEvent.TURN, TurnSide.LEFT)

        assertNotEquals(right.hex, left.hex)
    }

    @Test
    fun keepsUTurnArrowHeadInsideBitmapBounds() {
        val bitmap = HudManeuverIconBitmapRenderer.render(HeadunitNavEvent.UTURN, TurnSide.UNSPECIFIED)

        assertEquals(false, bitmap.hasLitPixelInColumn(0))
        assertTrue(bitmap.maxLitPixelsPerRow() < 39)
    }

    @Test
    fun rendersUTurnArrowHeadAsFilledTriangle() {
        val bitmap = HudManeuverIconBitmapRenderer.render(HeadunitNavEvent.UTURN, TurnSide.UNSPECIFIED)

        assertEquals(true, bitmap.isLit(12, 32))
        assertEquals(true, bitmap.isLit(5, 30))
        assertEquals(true, bitmap.isLit(21, 30))
    }

    private fun HudTextBitmap.hasLitPixelInColumn(column: Int): Boolean {
        val bytesPerRow = (width + 7) / 8
        for (row in 0 until height) {
            val byteIndex = row * bytesPerRow + column / 8
            val hexIndex = byteIndex * 2
            val value = bitmapByte(hex[hexIndex], hex[hexIndex + 1])
            if ((value and (1 shl (7 - column % 8))) != 0) {
                return true
            }
        }
        return false
    }

    private fun HudTextBitmap.isLit(column: Int, row: Int): Boolean {
        val bytesPerRow = (width + 7) / 8
        val byteIndex = row * bytesPerRow + column / 8
        val hexIndex = byteIndex * 2
        val value = bitmapByte(hex[hexIndex], hex[hexIndex + 1])
        return (value and (1 shl (7 - column % 8))) != 0
    }

    private fun HudTextBitmap.maxLitPixelsPerRow(): Int {
        val bytesPerRow = (width + 7) / 8
        return (0 until height).maxOf { row ->
            (0 until width).count { column ->
                val byteIndex = row * bytesPerRow + column / 8
                val hexIndex = byteIndex * 2
                val value = bitmapByte(hex[hexIndex], hex[hexIndex + 1])
                (value and (1 shl (7 - column % 8))) != 0
            }
        }
    }

    private fun bitmapByte(high: Char, low: Char): Int {
        return high.digitToInt(16) shl 4 or low.digitToInt(16)
    }
}