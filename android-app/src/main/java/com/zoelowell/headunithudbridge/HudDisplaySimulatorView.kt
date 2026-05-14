package com.zoelowell.headunithudbridge

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.graphics.Typeface
import android.text.TextPaint
import android.view.View

class HudDisplaySimulatorView(context: Context) : View(context) {
    private var bridgeStatus = BridgeDashboardStatus(
        headunitState = HeadunitObservedState.WAITING_FOR_BROADCAST,
        hudOutputState = HudOutputState.NONE,
        espConnectionState = EspConnectionObservedState.DISCONNECTED,
        lastEvent = "",
        lastEventTimeMillis = 0L,
        nextEspDiscoveryRetryAtMillis = 0L
    )
    private var navigationPacket: HudNavigationPacket? = null
    private var debugOverlayVisible = false
    private var speedUnitVisible = true
    private var speedFontSize = Esp32SettingsPacket.DEFAULT_SPEED_FONT_SIZE
    private var hudLanguage = Esp32SettingsPacket.DEFAULT_LANGUAGE

    private val displayPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.BLACK
        style = Paint.Style.FILL
    }
    private val borderPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.rgb(36, 45, 58)
        style = Paint.Style.STROKE
        strokeWidth = 2f
    }
    private val oledPaint = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD)
        textAlign = Paint.Align.LEFT
    }
    private val monoPaint = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        typeface = Typeface.create(Typeface.MONOSPACE, Typeface.NORMAL)
        textAlign = Paint.Align.LEFT
    }
    private val linePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.SQUARE
        strokeJoin = Paint.Join.MITER
        strokeWidth = 4f
    }
    private val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        style = Paint.Style.FILL
    }
    private val tempRect = RectF()
    private val tempTriangle = Path()

    fun updateStatus(status: BridgeDashboardStatus) {
        bridgeStatus = status
        invalidate()
    }

    fun updateNavigation(packet: HudNavigationPacket?) {
        navigationPacket = packet
        invalidate()
    }

    fun updateSettings(
        debugOverlay: Boolean,
        speedUnit: Boolean,
        speedFontSize: Int,
        hudLanguage: String = Esp32SettingsPacket.DEFAULT_LANGUAGE
    ) {
        debugOverlayVisible = debugOverlay
        speedUnitVisible = speedUnit
        this.speedFontSize = speedFontSize.coerceIn(
            Esp32SettingsPacket.MIN_SPEED_FONT_SIZE,
            Esp32SettingsPacket.MAX_SPEED_FONT_SIZE
        )
        this.hudLanguage = Esp32SettingsPacket.cleanLanguage(hudLanguage)
        invalidate()
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val width = MeasureSpec.getSize(widthMeasureSpec).coerceAtLeast(1)
        val horizontalPadding = paddingLeft + paddingRight
        val contentWidth = (width - horizontalPadding).coerceAtLeast(1)
        val gap = dp(8)
        val displayWidth = (contentWidth - gap) / 2f
        val displayHeight = displayWidth * OLED_HEIGHT / OLED_WIDTH
        val desiredHeight = (displayHeight + paddingTop + paddingBottom).toInt()
        setMeasuredDimension(width, resolveSize(desiredHeight, heightMeasureSpec))
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val gap = dp(8).toFloat()
        val availableWidth = width - paddingLeft - paddingRight - gap
        val screenWidth = availableWidth / 2f
        val screenHeight = screenWidth * OLED_HEIGHT / OLED_WIDTH
        val top = paddingTop.toFloat()
        var left = paddingLeft.toFloat()

        drawScreen(canvas, left, top, screenWidth, screenHeight) {
            drawSpeedScreen(canvas, left, top, screenWidth, screenHeight)
        }
        left += screenWidth + gap
        drawScreen(canvas, left, top, screenWidth, screenHeight) {
            drawNavigationScreen(canvas, left, top, screenWidth, screenHeight)
        }
    }

    private fun drawScreen(
        canvas: Canvas,
        left: Float,
        top: Float,
        width: Float,
        height: Float,
        content: () -> Unit
    ) {
        tempRect.set(left, top, left + width, top + height)
        canvas.drawRoundRect(tempRect, dp(4).toFloat(), dp(4).toFloat(), displayPaint)
        canvas.drawRoundRect(tempRect, dp(4).toFloat(), dp(4).toFloat(), borderPaint)
        content()
    }

    private fun drawSpeedScreen(canvas: Canvas, left: Float, top: Float, width: Float, height: Float) {
        if (bridgeStatus.espConnectionState != EspConnectionObservedState.CONNECTED) {
            drawCenteredText(canvas, localizedHudLabel("브릿지", "Bridge"), left, top, width, y = 36f, textSize = 15f)
            return
        }

        val scale = width / OLED_WIDTH
        val speedText = bridgeStatus.speedKmh.coerceAtLeast(0).coerceAtMost(999).toString()
        val textSize = speedFontSizeFor(speedText)
        val unitTextSize = 7f
        val layout = SpeedFaceLayout.calculate(
            speedText = speedText,
            unitText = "km/h",
            unitVisible = speedUnitVisible,
            containerWidth = OLED_WIDTH,
            containerHeight = OLED_HEIGHT,
            speedGlyphHeight = textSize,
            unitGlyphHeight = unitTextSize
        )
        drawSpeedText(canvas, speedText, left, top, scale, layout)
        if (speedUnitVisible) {
            drawStyledText(
                canvas = canvas,
                text = "km/h",
                x = left + layout.unitLeft * scale,
                baselineY = top + (layout.unitTop + unitTextSize * STYLED_DIGIT_BASELINE_RATIO) * scale,
                textSize = unitTextSize,
                paint = monoPaint,
                scale = scale
            )
        }
    }

    private fun drawNavigationScreen(canvas: Canvas, left: Float, top: Float, width: Float, height: Float) {
        if (bridgeStatus.espConnectionState != EspConnectionObservedState.CONNECTED) {
            drawCenteredText(canvas, localizedProgressHudLabel("대기중", "waiting"), left, top, width, y = 36f, textSize = 15f)
            return
        }

        val packet = navigationPacket
        if (bridgeStatus.hudOutputState != HudOutputState.NAVIGATION_GUIDANCE || packet == null) {
            drawTwoLineStatus(canvas, left, top, width, localizedHudLabel("헤드유닛", "Headunit"), localizedProgressHudLabel("대기중", "waiting"))
            return
        }

        if (debugOverlayVisible) drawHeader(canvas, left, top, width, "NAV")
        val scale = width / OLED_WIDTH
        val iconLeft = left + 3f * scale
        val iconTop = top + if (debugOverlayVisible) 15f * scale else 12f * scale
        val iconBitmap = packet.iconBitmap
            ?: HudManeuverIconBitmapRenderer.render(packet.eventType, packet.turnSide)
        if (!drawPackedMonoHexBitmap(canvas, iconBitmap, iconLeft, iconTop, scale)) {
            drawManeuverIcon(canvas, packet.eventType, packet.turnSide, iconLeft, iconTop, scale)
        }
        val textLeft = left + 50f * scale
        val textWidth = width - 50f * scale
        drawCenteredStyledText(canvas, formatDistance(packet.distanceMeters), textLeft, top, textWidth, y = if (packet.distanceMeters >= 10000) 33f else 31f, textSize = if (packet.distanceMeters >= 10000) 15f else 22f)
        drawRoadText(canvas, packet, textLeft, top + if (debugOverlayVisible) 42f * scale else 43f * scale, textWidth, scale)
    }

    private fun drawTwoLineStatus(
        canvas: Canvas,
        left: Float,
        top: Float,
        width: Float,
        title: String,
        detail: String
    ) {
        drawCenteredText(canvas, title, left, top, width, y = 26f, textSize = 13f)
        drawCenteredText(canvas, detail, left, top, width, y = 45f, textSize = 13f)
    }

    private fun localizedHudLabel(korean: String, english: String): String {
        return if (hudLanguage == Esp32SettingsPacket.LANGUAGE_ENGLISH) english else korean
    }

    private fun localizedProgressHudLabel(korean: String, english: String): String {
        return if (hudLanguage == Esp32SettingsPacket.LANGUAGE_ENGLISH) {
            english + ProgressTextAnimator.dotsFor()
        } else {
            ProgressTextAnimator.animate(korean)
        }
    }

    private fun drawHeader(canvas: Canvas, left: Float, top: Float, width: Float, label: String) {
        val scale = width / OLED_WIDTH
        tempRect.set(left, top, left + width, top + 11f * scale)
        canvas.drawRect(tempRect, fillPaint)

        monoPaint.color = Color.BLACK
        drawText(canvas, label, left + 3f * scale, top + 9f * scale, 7f, monoPaint, scale)
        val right = if (bridgeStatus.espConnectionState == EspConnectionObservedState.CONNECTED) "UDP" else "HUD"
        monoPaint.textAlign = Paint.Align.RIGHT
        drawText(canvas, right, left + width - 3f * scale, top + 9f * scale, 7f, monoPaint, scale)
        monoPaint.textAlign = Paint.Align.LEFT
        monoPaint.color = Color.WHITE
    }

    private fun drawRoadText(
        canvas: Canvas,
        packet: HudNavigationPacket,
        left: Float,
        top: Float,
        width: Float,
        scale: Float
    ) {
        packet.roadBitmap?.let { bitmap ->
            val bitmapLeft = left + ((width - bitmap.width * scale) / 2f).coerceAtLeast(0f)
            if (drawPackedMonoHexBitmap(canvas, bitmap, bitmapLeft, top, scale)) {
                return
            }
        }

        val text = packet.road
        if (text.isBlank()) {
            return
        }
        var size = 11f
        oledPaint.textAlign = Paint.Align.CENTER
        while (size > 7f) {
            oledPaint.textSize = size * scale
            if (oledPaint.measureText(text) <= width) break
            size -= 1f
        }
        canvas.drawText(text, left + width / 2f, top + size * scale, oledPaint)
        oledPaint.textAlign = Paint.Align.LEFT
    }

    private fun drawPackedMonoHexBitmap(
        canvas: Canvas,
        bitmap: HudTextBitmap,
        left: Float,
        top: Float,
        scale: Float
    ): Boolean {
        val bytesPerRow = (bitmap.width + 7) / 8
        val expectedHexLength = bytesPerRow * bitmap.height * 2
        if (bitmap.hex.length < expectedHexLength) {
            return false
        }

        var hexIndex = 0
        for (row in 0 until bitmap.height) {
            for (byteX in 0 until bytesPerRow) {
                val high = hexNibble(bitmap.hex[hexIndex++])
                val low = hexNibble(bitmap.hex[hexIndex++])
                if (high < 0 || low < 0) {
                    return false
                }
                val value = (high shl 4) or low
                for (bit in 0 until 8) {
                    val pixelX = byteX * 8 + bit
                    if (pixelX < bitmap.width && (value and (1 shl (7 - bit))) != 0) {
                        canvas.drawRect(
                            left + pixelX * scale,
                            top + row * scale,
                            left + (pixelX + 1) * scale,
                            top + (row + 1) * scale,
                            fillPaint
                        )
                    }
                }
            }
        }
        return true
    }

    private fun hexNibble(char: Char): Int {
        return when (char) {
            in '0'..'9' -> char - '0'
            in 'a'..'f' -> char - 'a' + 10
            in 'A'..'F' -> char - 'A' + 10
            else -> -1
        }
    }

    private fun drawManeuverIcon(
        canvas: Canvas,
        eventType: HeadunitNavEvent,
        turnSide: TurnSide,
        x: Float,
        y: Float,
        scale: Float
    ) {
        linePaint.strokeWidth = 5f * scale
        when {
            eventType == HeadunitNavEvent.DESTINATION -> drawDestinationIcon(canvas, x, y, scale)
            eventType == HeadunitNavEvent.UTURN -> drawUTurnIcon(canvas, x, y, scale)
            eventType == HeadunitNavEvent.ROUNDABOUT_ENTER ||
                eventType == HeadunitNavEvent.ROUNDABOUT_EXIT ||
                eventType == HeadunitNavEvent.ROUNDABOUT_ENTER_AND_EXIT -> drawRoundaboutIcon(canvas, x, y, scale)
            eventType == HeadunitNavEvent.FORK -> drawForkIcon(canvas, x, y, scale, turnSide)
            eventType == HeadunitNavEvent.ONRAMP -> drawOnRampIcon(canvas, x, y, scale, turnSide)
            eventType == HeadunitNavEvent.OFFRAMP -> drawOffRampIcon(canvas, x, y, scale, turnSide)
            eventType == HeadunitNavEvent.MERGE -> drawMergeIcon(canvas, x, y, scale, turnSide)
            eventType == HeadunitNavEvent.STRAIGHT && turnSide == TurnSide.LEFT -> drawKeepIcon(canvas, x, y, scale, TurnSide.LEFT)
            eventType == HeadunitNavEvent.STRAIGHT && turnSide == TurnSide.RIGHT -> drawKeepIcon(canvas, x, y, scale, TurnSide.RIGHT)
            eventType == HeadunitNavEvent.SLIGHT_TURN && turnSide == TurnSide.LEFT -> drawSlightTurnIcon(canvas, x, y, scale, TurnSide.LEFT)
            eventType == HeadunitNavEvent.SLIGHT_TURN && turnSide == TurnSide.RIGHT -> drawSlightTurnIcon(canvas, x, y, scale, TurnSide.RIGHT)
            eventType == HeadunitNavEvent.SHARP_TURN && turnSide == TurnSide.LEFT -> drawSharpTurnIcon(canvas, x, y, scale, TurnSide.LEFT)
            eventType == HeadunitNavEvent.SHARP_TURN && turnSide == TurnSide.RIGHT -> drawSharpTurnIcon(canvas, x, y, scale, TurnSide.RIGHT)
            turnSide == TurnSide.LEFT -> drawTurnIcon(canvas, x, y, scale, TurnSide.LEFT)
            turnSide == TurnSide.RIGHT -> drawTurnIcon(canvas, x, y, scale, TurnSide.RIGHT)
            else -> drawStraightIcon(canvas, x, y, scale)
        }
        linePaint.strokeWidth = 4f
    }

    private fun drawTurnIcon(canvas: Canvas, x: Float, y: Float, scale: Float, side: TurnSide) {
        val right = side == TurnSide.RIGHT
        val stemX = x + if (right) 14f * scale else 36f * scale
        val cornerY = y + 18f * scale
        val endX = x + if (right) 45f * scale else 5f * scale
        drawVerticalStem(canvas, stemX, cornerY, y + 37f * scale, scale)
        drawHorizontalStem(
            canvas,
            if (right) stemX else x + 17f * scale,
            cornerY,
            if (right) x + 33f * scale else stemX,
            scale
        )
        canvas.drawCircle(stemX, cornerY, 5.5f * scale, fillPaint)
        drawHorizontalArrowHead(canvas, endX, cornerY, scale, side)
    }

    private fun drawForkIcon(canvas: Canvas, x: Float, y: Float, scale: Float, side: TurnSide) {
        if (side == TurnSide.LEFT || side == TurnSide.RIGHT) {
            drawCurvedBranchArrowIcon(canvas, x, y, scale, side)
        } else {
            drawStraightIcon(canvas, x, y, scale)
        }
    }

    private fun drawMergeIcon(canvas: Canvas, x: Float, y: Float, scale: Float, side: TurnSide) {
        if (side == TurnSide.LEFT || side == TurnSide.RIGHT) {
            val right = side == TurnSide.RIGHT
            val startX = x + if (right) 43f * scale else 7f * scale
            drawWideLine(canvas, startX, y + 37f * scale, x + 25f * scale, y + 23f * scale, 11f * scale)
            drawVerticalStem(canvas, x + 25f * scale, y + 17f * scale, y + 37f * scale, scale)
            canvas.drawCircle(x + 25f * scale, y + 23f * scale, 5.5f * scale, fillPaint)
            drawUpArrowHead(canvas, x + 25f * scale, y + 2f * scale, scale)
        } else {
            drawStraightIcon(canvas, x, y, scale)
        }
    }

    private fun drawStraightIcon(canvas: Canvas, x: Float, y: Float, scale: Float) {
        val centerX = x + 25f * scale
        drawVerticalStem(canvas, centerX, y + 17f * scale, y + 37f * scale, scale)
        drawUpArrowHead(canvas, centerX, y + 2f * scale, scale)
    }

    private fun drawUTurnIcon(canvas: Canvas, x: Float, y: Float, scale: Float) {
        drawVerticalStem(canvas, x + 36f * scale, y + 13f * scale, y + 37f * scale, scale)
        drawHorizontalStem(canvas, x + 16f * scale, y + 13f * scale, x + 36f * scale, scale)
        drawVerticalStem(canvas, x + 16f * scale, y + 13f * scale, y + 26f * scale, scale)
        canvas.drawCircle(x + 36f * scale, y + 13f * scale, 5.5f * scale, fillPaint)
        canvas.drawCircle(x + 16f * scale, y + 13f * scale, 5.5f * scale, fillPaint)
        drawTriangle(
            canvas,
            x + 16f * scale,
            y + 39f * scale,
            x + 4f * scale,
            y + 28f * scale,
            x + 28f * scale,
            y + 28f * scale
        )
    }

    private fun drawSlightTurnIcon(canvas: Canvas, x: Float, y: Float, scale: Float, side: TurnSide) {
        val right = side == TurnSide.RIGHT
        val bendX = x + if (right) 30f * scale else 20f * scale
        val headBaseX = x + if (right) 35f * scale else 15f * scale
        drawVerticalStem(canvas, x + 25f * scale, y + 28f * scale, y + 37f * scale, scale)
        drawWideLine(canvas, x + 25f * scale, y + 28f * scale, bendX, y + 20f * scale, 11f * scale)
        drawWideLine(canvas, bendX, y + 20f * scale, headBaseX, y + 14f * scale, 11f * scale)
        canvas.drawCircle(x + 25f * scale, y + 28f * scale, 5.5f * scale, fillPaint)
        canvas.drawCircle(bendX, y + 20f * scale, 5.5f * scale, fillPaint)
        drawDiagonalArrowHead(canvas, x + if (right) 45f * scale else 5f * scale, y + 5f * scale, scale, side)
    }

    private fun drawSharpTurnIcon(canvas: Canvas, x: Float, y: Float, scale: Float, side: TurnSide) {
        val right = side == TurnSide.RIGHT
        val stemX = x + if (right) 14f * scale else 36f * scale
        val endX = x + if (right) 45f * scale else 5f * scale
        val cornerY = y + 11f * scale
        drawVerticalStem(canvas, stemX, cornerY, y + 37f * scale, scale)
        drawHorizontalStem(
            canvas,
            if (right) stemX else x + 17f * scale,
            cornerY,
            if (right) x + 33f * scale else stemX,
            scale
        )
        canvas.drawCircle(stemX, cornerY, 5.5f * scale, fillPaint)
        drawHorizontalArrowHead(canvas, endX, cornerY, scale, side)
    }

    private fun drawKeepIcon(canvas: Canvas, x: Float, y: Float, scale: Float, side: TurnSide) {
        val right = side == TurnSide.RIGHT
        val bendX = x + if (right) 31f * scale else 19f * scale
        val headBaseX = x + if (right) 35f * scale else 15f * scale
        drawVerticalStem(canvas, x + 25f * scale, y + 28f * scale, y + 37f * scale, scale)
        drawWideLine(canvas, x + 25f * scale, y + 28f * scale, bendX, y + 20f * scale, 11f * scale)
        drawWideLine(canvas, bendX, y + 20f * scale, headBaseX, y + 14f * scale, 11f * scale)
        canvas.drawCircle(x + 25f * scale, y + 28f * scale, 5.5f * scale, fillPaint)
        canvas.drawCircle(bendX, y + 20f * scale, 5.5f * scale, fillPaint)
        drawDiagonalArrowHead(canvas, x + if (right) 45f * scale else 5f * scale, y + 5f * scale, scale, side)
    }

    private fun drawOnRampIcon(canvas: Canvas, x: Float, y: Float, scale: Float, side: TurnSide) {
        if (side == TurnSide.LEFT || side == TurnSide.RIGHT) {
            val right = side == TurnSide.RIGHT
            val startX = x + if (right) 43f * scale else 7f * scale
            drawWideLine(canvas, startX, y + 37f * scale, x + 25f * scale, y + 23f * scale, 11f * scale)
            drawVerticalStem(canvas, x + 25f * scale, y + 17f * scale, y + 37f * scale, scale)
            canvas.drawCircle(x + 25f * scale, y + 23f * scale, 5.5f * scale, fillPaint)
            drawUpArrowHead(canvas, x + 25f * scale, y + 2f * scale, scale)
        } else {
            drawStraightIcon(canvas, x, y, scale)
        }
    }

    private fun drawOffRampIcon(canvas: Canvas, x: Float, y: Float, scale: Float, side: TurnSide) {
        if (side == TurnSide.LEFT || side == TurnSide.RIGHT) {
            drawCurvedBranchArrowIcon(canvas, x, y, scale, side)
        } else {
            drawStraightIcon(canvas, x, y, scale)
        }
    }

    private fun drawCurvedBranchArrowIcon(canvas: Canvas, x: Float, y: Float, scale: Float, side: TurnSide) {
        val right = side == TurnSide.RIGHT
        val stemX = x + if (right) 14f * scale else 36f * scale
        val bendX = x + if (right) 22f * scale else 28f * scale
        val headBaseX = x + if (right) 32f * scale else 18f * scale

        drawVerticalStem(canvas, stemX, y + 28f * scale, y + 37f * scale, scale)
        drawWideLine(canvas, stemX, y + 28f * scale, bendX, y + 19f * scale, 11f * scale)
        drawWideLine(canvas, bendX, y + 19f * scale, headBaseX, y + 14f * scale, 11f * scale)
        canvas.drawCircle(stemX, y + 28f * scale, 5.5f * scale, fillPaint)
        canvas.drawCircle(bendX, y + 19f * scale, 5.5f * scale, fillPaint)
        drawDiagonalArrowHead(canvas, x + if (right) 45f * scale else 5f * scale, y + 5f * scale, scale, side)
    }

    private fun drawDestinationIcon(canvas: Canvas, x: Float, y: Float, scale: Float) {
        drawVerticalStem(canvas, x + 25f * scale, y + 28f * scale, y + 37f * scale, scale)
        canvas.drawCircle(x + 25f * scale, y + 16f * scale, 14f * scale, fillPaint)
        displayPaint.style = Paint.Style.FILL
        canvas.drawCircle(x + 25f * scale, y + 16f * scale, 8f * scale, displayPaint)
        canvas.drawCircle(x + 25f * scale, y + 16f * scale, 4f * scale, fillPaint)
    }

    private fun drawRoundaboutIcon(canvas: Canvas, x: Float, y: Float, scale: Float) {
        drawVerticalStem(canvas, x + 25f * scale, y + 29f * scale, y + 37f * scale, scale)
        canvas.drawCircle(x + 25f * scale, y + 18f * scale, 15f * scale, fillPaint)
        canvas.drawCircle(x + 25f * scale, y + 18f * scale, 9f * scale, displayPaint)
        fillPaint.style = Paint.Style.STROKE
        fillPaint.strokeWidth = 2f * scale
        canvas.drawCircle(x + 25f * scale, y + 18f * scale, 11.5f * scale, fillPaint)
        fillPaint.style = Paint.Style.FILL
        drawHorizontalArrowHead(canvas, x + 45f * scale, y + 16f * scale, scale, TurnSide.RIGHT)
    }

    private fun drawVerticalStem(canvas: Canvas, centerX: Float, top: Float, bottom: Float, scale: Float) {
        val half = 5f * scale
        canvas.drawRect(centerX - half, top, centerX + half + scale, bottom + scale, fillPaint)
    }

    private fun drawHorizontalStem(canvas: Canvas, startX: Float, centerY: Float, endX: Float, scale: Float) {
        val left = startX.coerceAtMost(endX)
        val right = startX.coerceAtLeast(endX)
        val half = 5f * scale
        canvas.drawRect(left, centerY - half, right + scale, centerY + half + scale, fillPaint)
    }

    private fun drawWideLine(canvas: Canvas, startX: Float, startY: Float, endX: Float, endY: Float, strokeWidth: Float) {
        val previousStrokeWidth = linePaint.strokeWidth
        val previousCap = linePaint.strokeCap
        linePaint.strokeWidth = strokeWidth
        linePaint.strokeCap = Paint.Cap.ROUND
        canvas.drawLine(startX, startY, endX, endY, linePaint)
        linePaint.strokeWidth = previousStrokeWidth
        linePaint.strokeCap = previousCap
    }

    private fun drawUpArrowHead(canvas: Canvas, x: Float, y: Float, scale: Float) {
        drawTriangle(canvas, x, y, x - 15f * scale, y + 18f * scale, x + 15f * scale, y + 18f * scale)
    }

    private fun drawDownArrowHead(canvas: Canvas, x: Float, y: Float, scale: Float) {
        drawTriangle(canvas, x, y, x - 15f * scale, y - 18f * scale, x + 15f * scale, y - 18f * scale)
    }

    private fun drawHorizontalArrowHead(canvas: Canvas, x: Float, y: Float, scale: Float, side: TurnSide) {
        if (side == TurnSide.RIGHT) {
            drawTriangle(canvas, x, y, x - 17f * scale, y - 16f * scale, x - 17f * scale, y + 16f * scale)
        } else {
            drawTriangle(canvas, x, y, x + 17f * scale, y - 16f * scale, x + 17f * scale, y + 16f * scale)
        }
    }

    private fun drawDiagonalArrowHead(canvas: Canvas, x: Float, y: Float, scale: Float, side: TurnSide) {
        if (side == TurnSide.RIGHT) {
            drawTriangle(canvas, x, y, x - 18f * scale, y + 3f * scale, x - 7f * scale, y + 19f * scale)
        } else {
            drawTriangle(canvas, x, y, x + 18f * scale, y + 3f * scale, x + 7f * scale, y + 19f * scale)
        }
    }

    private fun drawTriangle(
        canvas: Canvas,
        x1: Float,
        y1: Float,
        x2: Float,
        y2: Float,
        x3: Float,
        y3: Float
    ) {
        tempTriangle.reset()
        tempTriangle.moveTo(x1, y1)
        tempTriangle.lineTo(x2, y2)
        tempTriangle.lineTo(x3, y3)
        tempTriangle.close()
        canvas.drawPath(tempTriangle, fillPaint)
    }

    private fun drawCenteredText(
        canvas: Canvas,
        text: String,
        left: Float,
        top: Float,
        width: Float,
        y: Float,
        textSize: Float
    ) {
        oledPaint.textAlign = Paint.Align.CENTER
        val scale = width / OLED_WIDTH
        drawText(canvas, text, left + width / 2f, top + y * scale, textSize, oledPaint, scale)
        oledPaint.textAlign = Paint.Align.LEFT
    }

    private fun drawCenteredTextAt(
        canvas: Canvas,
        text: String,
        centerX: Float,
        baselineY: Float,
        textSize: Float,
        scale: Float
    ) {
        oledPaint.textAlign = Paint.Align.CENTER
        drawText(canvas, text, centerX, baselineY, textSize, oledPaint, scale)
        oledPaint.textAlign = Paint.Align.LEFT
    }

    private fun drawCenteredStyledText(
        canvas: Canvas,
        text: String,
        left: Float,
        top: Float,
        width: Float,
        y: Float,
        textSize: Float
    ) {
        val scale = width / OLED_WIDTH
        val textWidth = styledTextWidth(text, textSize, oledPaint, scale)
        val x = left + (width - textWidth) / 2f
        drawStyledText(canvas, text, x.coerceAtLeast(left), top + y * scale, textSize, oledPaint, scale)
    }

    private fun drawCenteredStyledTextAt(
        canvas: Canvas,
        text: String,
        centerX: Float,
        baselineY: Float,
        textSize: Float,
        scale: Float
    ) {
        val textWidth = styledTextWidth(text, textSize, oledPaint, scale)
        drawStyledText(canvas, text, centerX - textWidth / 2f, baselineY, textSize, oledPaint, scale)
    }

    private fun drawCenteredValueWithUnit(
        canvas: Canvas,
        value: String,
        unit: String,
        left: Float,
        top: Float,
        width: Float,
        y: Float,
        valueTextSize: Float,
        unitTextSize: Float,
        unitYOffset: Float
    ) {
        val scale = width / OLED_WIDTH
        val gap = 5f * scale
        oledPaint.textAlign = Paint.Align.LEFT
        val valueWidth = styledTextWidth(value, valueTextSize, oledPaint, scale)
        oledPaint.textSize = unitTextSize * scale
        val unitWidth = if (value == "--") 0f else oledPaint.measureText(unit)
        val totalWidth = valueWidth + if (unitWidth > 0f) gap + unitWidth else 0f
        val startX = left + (width - totalWidth) / 2f

        drawStyledText(canvas, value, startX, top + y * scale, valueTextSize, oledPaint, scale)
        if (unitWidth > 0f) {
            drawText(
                canvas,
                unit,
                startX + valueWidth + gap,
                top + (y + unitYOffset) * scale,
                unitTextSize,
                oledPaint,
                scale
            )
        }
    }

    private fun drawText(
        canvas: Canvas,
        text: String,
        x: Float,
        y: Float,
        textSize: Float,
        paint: TextPaint,
        scale: Float
    ) {
        paint.textSize = textSize * scale
        canvas.drawText(text, x, y, paint)
    }

    private fun styledTextWidth(text: String, textSize: Float, paint: TextPaint, scale: Float): Float {
        paint.textSize = textSize * scale
        val glyphHeight = textSize * scale
        var width = 0f
        text.forEachIndexed { index, char ->
            width += if (SpeedDigitGlyph.isStyled(char)) {
                glyphHeight * SpeedDigitGlyph.advanceRatio(char)
            } else {
                paint.measureText(char.toString())
            }
            if (index < text.lastIndex) {
                width += styledGlyphGap(text[index], text[index + 1], glyphHeight)
            }
        }
        return width
    }

    private fun drawStyledText(
        canvas: Canvas,
        text: String,
        x: Float,
        baselineY: Float,
        textSize: Float,
        paint: TextPaint,
        scale: Float
    ) {
        val previousTextAlign = paint.textAlign
        paint.textAlign = Paint.Align.LEFT
        paint.textSize = textSize * scale
        val scaledGlyphHeight = textSize * scale
        val glyphTop = baselineY - scaledGlyphHeight * STYLED_DIGIT_BASELINE_RATIO
        var cursorX = x

        val previousStrokeWidth = linePaint.strokeWidth
        val previousStrokeCap = linePaint.strokeCap
        val previousStrokeJoin = linePaint.strokeJoin
        linePaint.strokeWidth = (scaledGlyphHeight * SPEED_DIGIT_STROKE_RATIO).coerceAtLeast(1f * scale)
        linePaint.strokeCap = Paint.Cap.ROUND
        linePaint.strokeJoin = Paint.Join.ROUND

        text.forEachIndexed { index, char ->
            if (SpeedDigitGlyph.isStyled(char)) {
                val glyphWidth = scaledGlyphHeight * SpeedDigitGlyph.advanceRatio(char)
                SpeedDigitGlyph.segments(char, glyphWidth, scaledGlyphHeight).forEach { segment ->
                    canvas.drawLine(
                        cursorX + segment.startX,
                        glyphTop + segment.startY,
                        cursorX + segment.endX,
                        glyphTop + segment.endY,
                        linePaint
                    )
                }
                cursorX += glyphWidth
            } else {
                val glyph = char.toString()
                canvas.drawText(glyph, cursorX, baselineY, paint)
                cursorX += paint.measureText(glyph)
            }
            if (index < text.lastIndex) {
                cursorX += styledGlyphGap(text[index], text[index + 1], scaledGlyphHeight)
            }
        }

        linePaint.strokeWidth = previousStrokeWidth
        linePaint.strokeCap = previousStrokeCap
        linePaint.strokeJoin = previousStrokeJoin
        paint.textAlign = previousTextAlign
    }

    private fun styledGlyphGap(current: Char, next: Char, glyphHeight: Float): Float {
        val baseGap = glyphHeight * STYLED_GLYPH_GAP_RATIO
        val unitGap = if (current in '0'..'9' && next in listOf('m', 'k', 'h')) {
            glyphHeight * STYLED_UNIT_GAP_RATIO
        } else {
            0f
        }
        val compactGap = current == '.' || next == '.' || current == ':' || next == ':'
        return if (compactGap) unitGap else baseGap + unitGap
    }

    private fun drawRightAlignedText(
        canvas: Canvas,
        text: String,
        x: Float,
        y: Float,
        textSize: Float,
        paint: TextPaint,
        scale: Float
    ) {
        paint.textAlign = Paint.Align.RIGHT
        drawText(canvas, text, x, y, textSize, paint, scale)
        paint.textAlign = Paint.Align.LEFT
    }

    private fun drawSpeedText(
        canvas: Canvas,
        text: String,
        left: Float,
        top: Float,
        scale: Float,
        layout: SpeedFaceBounds
    ) {
        val scaledGlyphHeight = layout.speedHeight * scale
        val digitWidth = scaledGlyphHeight * SpeedFaceLayout.SPEED_DIGIT_WIDTH_RATIO
        val gap = scaledGlyphHeight * SpeedFaceLayout.SPEED_DIGIT_GAP_RATIO
        var cursorX = left + layout.speedLeft * scale
        val glyphTop = top + layout.speedTop * scale
        val previousStrokeWidth = linePaint.strokeWidth
        val previousStrokeCap = linePaint.strokeCap
        val previousStrokeJoin = linePaint.strokeJoin
        linePaint.strokeWidth = (scaledGlyphHeight * SPEED_DIGIT_STROKE_RATIO).coerceAtLeast(1.4f * scale)
        linePaint.strokeCap = Paint.Cap.ROUND
        linePaint.strokeJoin = Paint.Join.ROUND

        text.forEach { digit ->
            SpeedDigitGlyph.segments(digit, digitWidth, scaledGlyphHeight).forEach { segment ->
                canvas.drawLine(
                    cursorX + segment.startX,
                    glyphTop + segment.startY,
                    cursorX + segment.endX,
                    glyphTop + segment.endY,
                    linePaint
                )
            }
            cursorX += digitWidth + gap
        }

        linePaint.strokeWidth = previousStrokeWidth
        linePaint.strokeCap = previousStrokeCap
        linePaint.strokeJoin = previousStrokeJoin
    }

    private fun speedFontSizeFor(speedText: String): Float {
        val requested = speedFontSize.coerceIn(
            Esp32SettingsPacket.MIN_SPEED_FONT_SIZE,
            Esp32SettingsPacket.MAX_SPEED_FONT_SIZE
        )
        val fitted = if (speedText.length >= 3) requested.coerceAtMost(4) else requested
        return fitted * 8f
    }

    private fun textBaselineCenterOffset(paint: TextPaint, textSize: Float, scale: Float): Float {
        paint.textSize = textSize * scale
        return -(paint.descent() + paint.ascent()) / (2f * scale)
    }

    private fun formatDistance(distanceMeters: Int): String {
        if (distanceMeters < 0) return "--"
        if (distanceMeters < 1000) return "${distanceMeters}m"
        if (distanceMeters < 10000) return String.format("%.1fkm", distanceMeters / 1000.0)
        return "${distanceMeters / 1000}km"
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
    companion object {
        private const val OLED_WIDTH = 128f
        private const val OLED_HEIGHT = 64f
        private const val SPEED_DIGIT_STROKE_RATIO = 0.105f
        private const val STYLED_DIGIT_BASELINE_RATIO = 0.82f
        private const val STYLED_GLYPH_GAP_RATIO = 0.06f
        private const val STYLED_UNIT_GAP_RATIO = 0.12f
    }
}
