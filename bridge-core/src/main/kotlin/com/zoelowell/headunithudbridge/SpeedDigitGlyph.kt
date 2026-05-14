package com.zoelowell.headunithudbridge

data class SpeedGlyphSegment(
    val startX: Float,
    val startY: Float,
    val endX: Float,
    val endY: Float
)

object SpeedDigitGlyph {
    fun isStyled(char: Char): Boolean {
        return char in '0'..'9' || char in listOf('m', 'k', 'h', '/', '.', ':')
    }

    fun advanceRatio(char: Char): Float {
        return when (char) {
            'm' -> 0.96f
            '/', '.', ':' -> 0.34f
            else -> 0.72f
        }
    }

    fun segments(digit: Char, cellWidth: Float, glyphHeight: Float): List<SpeedGlyphSegment> {
        fun segment(startX: Float, startY: Float, endX: Float, endY: Float): SpeedGlyphSegment {
            return SpeedGlyphSegment(
                startX = startX * cellWidth,
                startY = startY * glyphHeight,
                endX = endX * cellWidth,
                endY = endY * glyphHeight
            )
        }

        val top = segment(0.16f, 0.07f, 0.84f, 0.07f)
        val upperLeft = segment(0.16f, 0.08f, 0.16f, 0.46f)
        val upperRight = segment(0.84f, 0.08f, 0.84f, 0.46f)
        val middle = segment(0.19f, 0.50f, 0.81f, 0.50f)
        val lowerLeft = segment(0.16f, 0.54f, 0.16f, 0.92f)
        val lowerRight = segment(0.84f, 0.54f, 0.84f, 0.92f)
        val bottom = segment(0.16f, 0.93f, 0.84f, 0.93f)

        return when (digit) {
            '0' -> listOf(top, upperLeft, upperRight, lowerLeft, lowerRight, bottom)
            '1' -> listOf(segment(0.60f, 0.08f, 0.60f, 0.92f))
            '2' -> listOf(top, upperRight, middle, lowerLeft, bottom)
            '3' -> listOf(top, upperRight, middle, lowerRight, bottom)
            '4' -> listOf(upperLeft, upperRight, middle, lowerRight)
            '5' -> listOf(top, upperLeft, middle, lowerRight, bottom)
            '6' -> listOf(top, upperLeft, middle, lowerLeft, lowerRight, bottom)
            '7' -> listOf(
                top,
                segment(0.84f, 0.07f, 0.84f, 0.26f),
                segment(0.84f, 0.26f, 0.30f, 0.93f)
            )
            '8' -> listOf(top, upperLeft, upperRight, middle, lowerLeft, lowerRight, bottom)
            '9' -> listOf(top, upperLeft, upperRight, middle, lowerRight, bottom)
            'm' -> listOf(
                segment(0.14f, 0.93f, 0.14f, 0.44f),
                segment(0.14f, 0.44f, 0.42f, 0.44f),
                segment(0.42f, 0.44f, 0.42f, 0.93f),
                segment(0.42f, 0.44f, 0.70f, 0.44f),
                segment(0.70f, 0.44f, 0.70f, 0.93f)
            )
            'k' -> listOf(
                segment(0.18f, 0.08f, 0.18f, 0.93f),
                segment(0.80f, 0.37f, 0.22f, 0.62f),
                segment(0.33f, 0.58f, 0.84f, 0.93f)
            )
            'h' -> listOf(
                segment(0.18f, 0.08f, 0.18f, 0.93f),
                segment(0.18f, 0.48f, 0.76f, 0.48f),
                segment(0.76f, 0.48f, 0.76f, 0.93f)
            )
            '/' -> listOf(segment(0.86f, 0.08f, 0.14f, 0.93f))
            '.' -> listOf(segment(0.50f, 0.92f, 0.50f, 0.92f))
            ':' -> listOf(
                segment(0.50f, 0.36f, 0.50f, 0.36f),
                segment(0.50f, 0.74f, 0.50f, 0.74f)
            )
            else -> emptyList()
        }
    }
}