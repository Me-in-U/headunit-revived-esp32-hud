package com.zoelowell.headunithudbridge

data class SpeedFaceBounds(
    val speedLeft: Float,
    val speedTop: Float,
    val speedWidth: Float,
    val speedHeight: Float,
    val unitLeft: Float,
    val unitTop: Float,
    val unitWidth: Float,
    val unitHeight: Float
) {
    val speedRight: Float
        get() = speedLeft + speedWidth
    val speedBottom: Float
        get() = speedTop + speedHeight
    val unitRight: Float
        get() = unitLeft + unitWidth
    val unitBottom: Float
        get() = unitTop + unitHeight
}

object SpeedFaceLayout {
    const val SPEED_DIGIT_WIDTH_RATIO = 0.72f
    const val SPEED_DIGIT_GAP_RATIO = 0.14f
    const val UNIT_GAP_RATIO = 0.08f
    private const val UNIT_GLYPH_GAP_RATIO = 0.06f
    private const val UNIT_AFTER_DIGIT_GAP_RATIO = 0.12f

    fun calculate(
        speedText: String,
        unitText: String,
        unitVisible: Boolean,
        containerWidth: Float,
        containerHeight: Float,
        speedGlyphHeight: Float,
        unitGlyphHeight: Float
    ): SpeedFaceBounds {
        val speedWidth = speedTextWidth(speedText, speedGlyphHeight)
        val speedTop = ((containerHeight - speedGlyphHeight) / 2f).coerceAtLeast(0f)

        if (!unitVisible || unitText.isBlank()) {
            return SpeedFaceBounds(
                speedLeft = ((containerWidth - speedWidth) / 2f).coerceAtLeast(0f),
                speedTop = speedTop,
                speedWidth = speedWidth,
                speedHeight = speedGlyphHeight,
                unitLeft = 0f,
                unitTop = 0f,
                unitWidth = 0f,
                unitHeight = 0f
            )
        }

        val unitWidth = styledTextWidth(unitText, unitGlyphHeight)
        val unitGap = speedGlyphHeight * UNIT_GAP_RATIO
        val totalWidth = speedWidth + unitGap + unitWidth
        val startLeft = ((containerWidth - totalWidth) / 2f).coerceAtLeast(0f)
        val unitTop = speedTop + speedGlyphHeight - unitGlyphHeight

        return SpeedFaceBounds(
            speedLeft = startLeft,
            speedTop = speedTop,
            speedWidth = speedWidth,
            speedHeight = speedGlyphHeight,
            unitLeft = startLeft + speedWidth + unitGap,
            unitTop = unitTop,
            unitWidth = unitWidth,
            unitHeight = unitGlyphHeight
        )
    }

    fun speedTextWidth(text: String, glyphHeight: Float): Float {
        if (text.isEmpty()) {
            return 0f
        }
        val glyphWidth = glyphHeight * SPEED_DIGIT_WIDTH_RATIO
        val gap = glyphHeight * SPEED_DIGIT_GAP_RATIO
        return text.length * glyphWidth + (text.length - 1) * gap
    }

    fun styledTextWidth(text: String, glyphHeight: Float): Float {
        var width = 0f
        text.forEachIndexed { index, char ->
            width += glyphHeight * SpeedDigitGlyph.advanceRatio(char)
            if (index < text.lastIndex) {
                width += styledGlyphGap(char, text[index + 1], glyphHeight)
            }
        }
        return width
    }

    private fun styledGlyphGap(current: Char, next: Char, glyphHeight: Float): Float {
        val unitGap = if (current in '0'..'9' && next in listOf('m', 'k', 'h')) {
            glyphHeight * UNIT_AFTER_DIGIT_GAP_RATIO
        } else {
            0f
        }
        val compactGap = current == '.' || next == '.' || current == ':' || next == ':'
        return if (compactGap) unitGap else glyphHeight * UNIT_GLYPH_GAP_RATIO + unitGap
    }
}