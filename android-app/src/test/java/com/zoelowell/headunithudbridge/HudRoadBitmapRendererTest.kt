package com.zoelowell.headunithudbridge

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class HudRoadBitmapRendererTest {
    @Test
    fun usesOneBitOledRenderingPolicy() {
        assertEquals(false, HudRoadBitmapRenderer.policy.antiAlias)
        assertEquals(false, HudRoadBitmapRenderer.policy.bold)
        assertEquals(14f, HudRoadBitmapRenderer.policy.maxTextSize)
        assertEquals(9f, HudRoadBitmapRenderer.policy.minTextSize)
        assertEquals(128, HudRoadBitmapRenderer.policy.pixelAlphaThreshold)
    }

    @Test
    fun rendersHangulRoadTextAsCompactOneBitGlyphs() {
        val bitmap = requireNotNull(HudRoadBitmapRenderer.render("명덕"))

        assertEquals(76, bitmap.width)
        assertEquals(16, bitmap.height)
        assertEquals(expectedOledHex("명덕"), bitmap.hex)
    }

    private fun expectedOledHex(text: String): String {
        val cleanText = text.trim()
        val paint = Paint().apply {
            color = Color.WHITE
            textAlign = Paint.Align.CENTER
            typeface = Typeface.create("sans-serif", Typeface.NORMAL)
            isAntiAlias = false
            isDither = false
            isFilterBitmap = false
            isSubpixelText = false
            hinting = Paint.HINTING_ON
        }
        var textSize = 14f
        paint.textSize = textSize
        while (textSize > 9f && paint.measureText(cleanText) > 76) {
            textSize -= 1f
            paint.textSize = textSize
        }

        val bitmap = Bitmap.createBitmap(76, 16, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val baseline = ((16 / 2f) - ((paint.descent() + paint.ascent()) / 2f)).toInt().toFloat()
        canvas.drawText(cleanText, 76 / 2f, baseline, paint)

        return bitmap.toPackedMonoHex()
    }

    private fun Bitmap.toPackedMonoHex(): String {
        val hexChars = "0123456789abcdef".toCharArray()
        val bytesPerRow = (width + 7) / 8
        return buildString(bytesPerRow * height * 2) {
            for (y in 0 until height) {
                for (byteX in 0 until bytesPerRow) {
                    var value = 0
                    for (bit in 0 until 8) {
                        val x = byteX * 8 + bit
                        if (x < width && Color.alpha(getPixel(x, y)) >= 128) {
                            value = value or (1 shl (7 - bit))
                        }
                    }
                    append(hexChars[value ushr 4])
                    append(hexChars[value and 0x0F])
                }
            }
        }
    }
}