package com.zoelowell.headunithudbridge

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

object HudManeuverIconBitmapRenderer {
    const val WIDTH = 50
    const val HEIGHT = 42
    private const val ALPHA_THRESHOLD = 72
    private const val STROKE_WIDTH = 11f
    private const val ARROW_LENGTH = 19f
    private const val ARROW_HALF_WIDTH = 16f

    private val hexChars = "0123456789abcdef".toCharArray()

    fun render(eventType: HeadunitNavEvent, turnSide: TurnSide): HudTextBitmap {
        val bitmap = Bitmap.createBitmap(WIDTH, HEIGHT, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            style = Paint.Style.FILL
        }
        val strokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            style = Paint.Style.STROKE
            strokeWidth = STROKE_WIDTH
            strokeCap = Paint.Cap.ROUND
            strokeJoin = Paint.Join.ROUND
        }

        when {
            eventType == HeadunitNavEvent.DESTINATION -> drawDestination(canvas, fillPaint)
            eventType == HeadunitNavEvent.UTURN -> drawUTurn(canvas, strokePaint, fillPaint)
            eventType == HeadunitNavEvent.ROUNDABOUT_ENTER ||
                eventType == HeadunitNavEvent.ROUNDABOUT_EXIT ||
                eventType == HeadunitNavEvent.ROUNDABOUT_ENTER_AND_EXIT -> drawRoundabout(canvas, strokePaint, fillPaint)
            eventType == HeadunitNavEvent.FORK || eventType == HeadunitNavEvent.OFFRAMP -> {
                if (turnSide == TurnSide.LEFT || turnSide == TurnSide.RIGHT) {
                    drawSideAware(canvas, turnSide) { drawForkRight(canvas, strokePaint, fillPaint) }
                } else {
                    drawStraight(canvas, strokePaint, fillPaint)
                }
            }
            eventType == HeadunitNavEvent.ONRAMP || eventType == HeadunitNavEvent.MERGE -> {
                drawSideAware(canvas, turnSide) { drawMergeRight(canvas, strokePaint, fillPaint) }
            }
            eventType == HeadunitNavEvent.STRAIGHT && turnSide == TurnSide.LEFT -> {
                drawSideAware(canvas, TurnSide.LEFT) { drawKeepRight(canvas, strokePaint, fillPaint) }
            }
            eventType == HeadunitNavEvent.STRAIGHT && turnSide == TurnSide.RIGHT -> {
                drawKeepRight(canvas, strokePaint, fillPaint)
            }
            eventType == HeadunitNavEvent.SLIGHT_TURN && turnSide == TurnSide.LEFT -> {
                drawSideAware(canvas, TurnSide.LEFT) { drawSlightRight(canvas, strokePaint, fillPaint) }
            }
            eventType == HeadunitNavEvent.SLIGHT_TURN && turnSide == TurnSide.RIGHT -> {
                drawSlightRight(canvas, strokePaint, fillPaint)
            }
            eventType == HeadunitNavEvent.SHARP_TURN && turnSide == TurnSide.LEFT -> {
                drawSideAware(canvas, TurnSide.LEFT) { drawTurnRight(canvas, strokePaint, fillPaint, cornerY = 11f) }
            }
            eventType == HeadunitNavEvent.SHARP_TURN && turnSide == TurnSide.RIGHT -> {
                drawTurnRight(canvas, strokePaint, fillPaint, cornerY = 11f)
            }
            turnSide == TurnSide.LEFT -> {
                drawSideAware(canvas, TurnSide.LEFT) { drawTurnRight(canvas, strokePaint, fillPaint, cornerY = 18f) }
            }
            turnSide == TurnSide.RIGHT -> drawTurnRight(canvas, strokePaint, fillPaint, cornerY = 18f)
            else -> drawStraight(canvas, strokePaint, fillPaint)
        }

        return HudTextBitmap(
            width = WIDTH,
            height = HEIGHT,
            hex = bitmap.toPackedMonoHex(ALPHA_THRESHOLD)
        )
    }

    private fun drawSideAware(canvas: Canvas, side: TurnSide, drawRight: () -> Unit) {
        if (side != TurnSide.LEFT) {
            drawRight()
            return
        }

        canvas.save()
        canvas.scale(-1f, 1f, WIDTH / 2f, HEIGHT / 2f)
        drawRight()
        canvas.restore()
    }

    private fun drawTurnRight(canvas: Canvas, strokePaint: Paint, fillPaint: Paint, cornerY: Float) {
        val path = Path().apply {
            moveTo(12f, 39f)
            lineTo(12f, cornerY + 8f)
            quadTo(12f, cornerY, 21f, cornerY)
            lineTo(32f, cornerY)
        }
        canvas.drawPath(path, strokePaint)
        drawArrowHead(canvas, fillPaint, tipX = 48f, tipY = cornerY, angleRadians = 0.0)
    }

    private fun drawSlightRight(canvas: Canvas, strokePaint: Paint, fillPaint: Paint) {
        val path = Path().apply {
            moveTo(24f, 39f)
            cubicTo(24f, 30f, 29f, 22f, 34f, 17f)
        }
        canvas.drawPath(path, strokePaint)
        drawArrowHead(canvas, fillPaint, tipX = 47f, tipY = 4f, angleRadians = -0.72)
    }

    private fun drawKeepRight(canvas: Canvas, strokePaint: Paint, fillPaint: Paint) {
        val path = Path().apply {
            moveTo(25f, 39f)
            cubicTo(25f, 30f, 30f, 22f, 35f, 16f)
        }
        canvas.drawPath(path, strokePaint)
        drawArrowHead(canvas, fillPaint, tipX = 47f, tipY = 4f, angleRadians = -0.68)
    }

    private fun drawForkRight(canvas: Canvas, strokePaint: Paint, fillPaint: Paint) {
        val path = Path().apply {
            moveTo(12f, 39f)
            lineTo(12f, 31f)
            cubicTo(12f, 23f, 22f, 16f, 32f, 13f)
        }
        canvas.drawPath(path, strokePaint)
        drawArrowHead(canvas, fillPaint, tipX = 47f, tipY = 4f, angleRadians = -0.52)
    }

    private fun drawMergeRight(canvas: Canvas, strokePaint: Paint, fillPaint: Paint) {
        val main = Path().apply {
            moveTo(25f, 39f)
            lineTo(25f, 20f)
        }
        canvas.drawPath(main, strokePaint)
        val branch = Path().apply {
            moveTo(44f, 39f)
            cubicTo(38f, 34f, 31f, 28f, 25f, 23f)
        }
        canvas.drawPath(branch, strokePaint)
        drawArrowHead(canvas, fillPaint, tipX = 25f, tipY = 2f, angleRadians = -PI / 2.0)
    }

    private fun drawStraight(canvas: Canvas, strokePaint: Paint, fillPaint: Paint) {
        val path = Path().apply {
            moveTo(25f, 39f)
            lineTo(25f, 20f)
        }
        canvas.drawPath(path, strokePaint)
        drawArrowHead(canvas, fillPaint, tipX = 25f, tipY = 2f, angleRadians = -PI / 2.0)
    }

    private fun drawUTurn(canvas: Canvas, strokePaint: Paint, fillPaint: Paint) {
        val previousStrokeWidth = strokePaint.strokeWidth
        strokePaint.strokeWidth = 8f
        val path = Path().apply {
            moveTo(36f, 39f)
            lineTo(36f, 17f)
            quadTo(36f, 8f, 27f, 8f)
            lineTo(21f, 8f)
            quadTo(12f, 8f, 12f, 17f)
            lineTo(12f, 27f)
        }
        canvas.drawPath(path, strokePaint)
        strokePaint.strokeWidth = previousStrokeWidth
        drawArrowHead(canvas, fillPaint, tipX = 13f, tipY = 39f, angleRadians = PI / 2.0, length = 10f, halfWidth = 10f)
    }

    private fun drawDestination(canvas: Canvas, fillPaint: Paint) {
        canvas.drawCircle(25f, 15f, 14f, fillPaint)
        val cutout = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.TRANSPARENT
            xfermode = android.graphics.PorterDuffXfermode(android.graphics.PorterDuff.Mode.CLEAR)
        }
        canvas.drawCircle(25f, 15f, 7f, cutout)
        canvas.drawCircle(25f, 15f, 4f, fillPaint)
        canvas.drawRect(20f, 26f, 31f, 40f, fillPaint)
    }

    private fun drawRoundabout(canvas: Canvas, strokePaint: Paint, fillPaint: Paint) {
        val previousWidth = strokePaint.strokeWidth
        strokePaint.strokeWidth = 8f
        canvas.drawArc(RectF(12f, 5f, 38f, 31f), 55f, 310f, false, strokePaint)
        strokePaint.strokeWidth = previousWidth
        canvas.drawRect(20f, 28f, 31f, 40f, fillPaint)
        drawArrowHead(canvas, fillPaint, tipX = 42f, tipY = 16f, angleRadians = 0.0, length = 16f, halfWidth = 12f)
    }

    private fun drawArrowHead(
        canvas: Canvas,
        fillPaint: Paint,
        tipX: Float,
        tipY: Float,
        angleRadians: Double,
        length: Float = ARROW_LENGTH,
        halfWidth: Float = ARROW_HALF_WIDTH
    ) {
        val dirX = cos(angleRadians).toFloat()
        val dirY = sin(angleRadians).toFloat()
        val baseCenterX = tipX - dirX * length
        val baseCenterY = tipY - dirY * length
        val perpX = -dirY
        val perpY = dirX
        val path = Path().apply {
            moveTo(tipX, tipY)
            lineTo(baseCenterX + perpX * halfWidth, baseCenterY + perpY * halfWidth)
            lineTo(baseCenterX - perpX * halfWidth, baseCenterY - perpY * halfWidth)
            close()
        }
        canvas.drawPath(path, fillPaint)
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