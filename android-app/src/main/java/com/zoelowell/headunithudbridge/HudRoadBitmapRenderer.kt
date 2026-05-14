package com.zoelowell.headunithudbridge

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface

object HudRoadBitmapRenderer {
    val policy = HudRoadBitmapRenderingPolicy(
        width = 76,
        height = 16,
        maxTextSize = 14f,
        minTextSize = 9f,
        pixelAlphaThreshold = 128,
        antiAlias = false,
        bold = false
    )
    private val hexChars = "0123456789abcdef".toCharArray()

    fun render(text: String): HudTextBitmap? {
        val cleanText = text.trim()
        if (cleanText.isBlank()) {
            return null
        }

        val paint = Paint().apply {
            color = Color.WHITE
            textAlign = Paint.Align.CENTER
            typeface = Typeface.create(
                "sans-serif",
                if (policy.bold) Typeface.BOLD else Typeface.NORMAL
            )
            isAntiAlias = policy.antiAlias
            isDither = false
            isFilterBitmap = false
            isSubpixelText = false
            hinting = Paint.HINTING_ON
        }
        fitPaintToText(cleanText, paint)
        val displayText = ellipsizeToWidth(cleanText, paint)

        val bitmap = Bitmap.createBitmap(policy.width, policy.height, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val baseline = ((policy.height / 2f) - ((paint.descent() + paint.ascent()) / 2f))
            .toInt()
            .toFloat()
        canvas.drawText(displayText, policy.width / 2f, baseline, paint)

        return HudTextBitmap(
            width = policy.width,
            height = policy.height,
            hex = bitmap.toPackedMonoHex(policy.pixelAlphaThreshold)
        )
    }

    private fun fitPaintToText(text: String, paint: Paint) {
        var textSize = policy.maxTextSize
        paint.textSize = textSize
        while (textSize > policy.minTextSize && paint.measureText(text) > policy.width) {
            textSize -= 1f
            paint.textSize = textSize
        }
    }

    private fun ellipsizeToWidth(text: String, paint: Paint): String {
        if (paint.measureText(text) <= policy.width) {
            return text
        }

        var candidate = text
        while (candidate.length > 1) {
            candidate = candidate.dropLast(1)
            val ellipsized = "$candidate…"
            if (paint.measureText(ellipsized) <= policy.width) {
                return ellipsized
            }
        }
        return candidate
    }

    private fun Bitmap.toPackedMonoHex(alphaThreshold: Int): String {
        val bytesPerRow = (width + 7) / 8
        return buildString(bytesPerRow * height * 2) {
            for (y in 0 until height) {
                for (byteX in 0 until bytesPerRow) {
                    var value = 0
                    for (bit in 0 until 8) {
                        val x = byteX * 8 + bit
                        if (x < width && Color.alpha(getPixel(x, y)) >= alphaThreshold) {
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

data class HudRoadBitmapRenderingPolicy(
    val width: Int,
    val height: Int,
    val maxTextSize: Float,
    val minTextSize: Float,
    val pixelAlphaThreshold: Int,
    val antiAlias: Boolean,
    val bold: Boolean
)