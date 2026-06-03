package com.zoelowell.headunithudbridge

data class HudNavigationPacket(
    val distanceMeters: Int,
    val timeSeconds: Int,
    val road: String,
    val eventType: HeadunitNavEvent,
    val turnSide: TurnSide,
    val turnNumber: Int,
    val turnAngle: Int,
    val roadBitmap: HudTextBitmap? = null,
    val iconBitmap: HudTextBitmap? = null
) {
    val instruction: String
        get() = actionText()

    val activeGuidance: Boolean
        get() = eventType != HeadunitNavEvent.UNKNOWN ||
            distanceMeters >= 0 ||
            timeSeconds >= 0

    fun toJson(): String {
        return buildString {
            append('{')
            append("\"distance_meters\":").append(distanceMeters).append(',')
            append("\"time_seconds\":").append(timeSeconds).append(',')
            append("\"road\":\"").append(road.escapeJson()).append("\",")
            roadBitmap?.let { bitmap ->
                append("\"road_bitmap_width\":").append(bitmap.width).append(',')
                append("\"road_bitmap_height\":").append(bitmap.height).append(',')
                append("\"road_bitmap_hex\":\"").append(bitmap.hex.escapeJson()).append("\",")
            }
            iconBitmap?.let { bitmap ->
                append("\"icon_bitmap_width\":").append(bitmap.width).append(',')
                append("\"icon_bitmap_height\":").append(bitmap.height).append(',')
                append("\"icon_bitmap_hex\":\"").append(bitmap.hex.escapeJson()).append("\",")
            }
            append("\"event_type\":").append(eventType.wireValue).append(',')
            append("\"turn_side\":").append(turnSide.wireValue).append(',')
            append("\"turn_number\":").append(turnNumber).append(',')
            append("\"turn_angle\":").append(turnAngle).append(',')
            append("\"active\":").append(activeGuidance).append(',')
            append("\"instruction\":\"").append(instruction.escapeJson()).append("\"")
            append('}')
        }
    }

    fun toHudJson(): String {
        return buildString {
            append('{')
            append("\"distance_meters\":").append(distanceMeters).append(',')
            append("\"time_seconds\":").append(timeSeconds).append(',')
            append("\"road\":\"").append(road.escapeJson()).append("\",")
            roadBitmap?.let { bitmap ->
                append("\"road_bitmap_width\":").append(bitmap.width).append(',')
                append("\"road_bitmap_height\":").append(bitmap.height).append(',')
                append("\"road_bitmap_hex\":\"").append(bitmap.hex.escapeJson()).append("\",")
            }
            iconBitmap?.let { bitmap ->
                append("\"icon_bitmap_width\":").append(bitmap.width).append(',')
                append("\"icon_bitmap_height\":").append(bitmap.height).append(',')
                append("\"icon_bitmap_hex\":\"").append(bitmap.hex.escapeJson()).append("\",")
            }
            append("\"event_type\":").append(eventType.wireValue).append(',')
            append("\"turn_side\":").append(turnSide.wireValue).append(',')
            append("\"turn_number\":").append(turnNumber).append(',')
            append("\"turn_angle\":").append(turnAngle).append(',')
            append("\"active\":").append(activeGuidance)
            append('}')
        }
    }

    private fun actionText(): String {
        return actionTextFor(eventType, turnSide, turnNumber)
    }

    companion object {
        fun inactive(): HudNavigationPacket {
            return HudNavigationPacket(
                distanceMeters = -1,
                timeSeconds = -1,
                road = "",
                eventType = HeadunitNavEvent.UNKNOWN,
                turnSide = TurnSide.UNSPECIFIED,
                turnNumber = -1,
                turnAngle = -1
            )
        }

        fun fromHeadunitValues(
            distanceMeters: Int,
            timeSeconds: Int,
            road: String?,
            nextEventType: Int,
            turnSide: Int,
            turnNumber: Int,
            turnAngle: Int
        ): HudNavigationPacket {
            val eventType = HeadunitNavEvent.fromWireValue(nextEventType)
            val side = TurnSide.fromWireValue(turnSide)
            return HudNavigationPacket(
                distanceMeters = distanceMeters,
                timeSeconds = timeSeconds,
                road = selectDisplayRoad(
                    legacyRoad = road.orEmpty(),
                    eventType = eventType,
                    turnSide = side,
                    turnNumber = turnNumber
                ),
                eventType = eventType,
                turnSide = side,
                turnNumber = turnNumber,
                turnAngle = turnAngle
            )
        }

        private fun selectDisplayRoad(
            legacyRoad: String,
            eventType: HeadunitNavEvent,
            turnSide: TurnSide,
            turnNumber: Int
        ): String {
            return sequenceOf(legacyRoad)
                .map(String::trim)
                .firstOrNull { it.isNotBlank() && !it.isManeuverOnlyText() }
                ?: actionTextFor(eventType, turnSide, turnNumber)
        }

        private fun actionTextFor(
            eventType: HeadunitNavEvent,
            turnSide: TurnSide,
            turnNumber: Int
        ): String {
            return when (eventType) {
                HeadunitNavEvent.DEPART -> "출발"
                HeadunitNavEvent.NAME_CHANGE -> "도로명 변경"
                HeadunitNavEvent.SLIGHT_TURN -> sideAwareTurn(turnSide, "완만한 좌회전", "완만한 우회전", "완만한 회전")
                HeadunitNavEvent.TURN -> sideAwareTurn(turnSide, "좌회전", "우회전", "회전")
                HeadunitNavEvent.SHARP_TURN -> sideAwareTurn(turnSide, "급좌회전", "급우회전", "급회전")
                HeadunitNavEvent.UTURN -> sideAwareTurn(turnSide, "좌측 유턴", "우측 유턴", "유턴")
                HeadunitNavEvent.ONRAMP -> sideAwareTurn(turnSide, "좌측 도로 진입", "우측 도로 진입", "도로 진입")
                HeadunitNavEvent.OFFRAMP -> sideAwareTurn(turnSide, "좌측 진출로", "우측 진출로", "진출로")
                HeadunitNavEvent.FORK -> sideAwareTurn(turnSide, "좌측 갈림길", "우측 갈림길", "갈림길")
                HeadunitNavEvent.MERGE -> sideAwareTurn(turnSide, "좌측 합류", "우측 합류", "합류")
                HeadunitNavEvent.ROUNDABOUT_ENTER -> "회전교차로 진입"
                HeadunitNavEvent.ROUNDABOUT_EXIT -> roundaboutExitText(turnNumber)
                HeadunitNavEvent.ROUNDABOUT_ENTER_AND_EXIT -> roundaboutExitText(turnNumber)
                HeadunitNavEvent.STRAIGHT -> "직진"
                HeadunitNavEvent.FERRY_BOAT -> "페리 탑승"
                HeadunitNavEvent.FERRY_TRAIN -> "열차 페리 탑승"
                HeadunitNavEvent.DESTINATION -> "도착"
                HeadunitNavEvent.UNKNOWN -> sideAwareTurn(turnSide, "좌회전", "우회전", "경로 안내")
            }
        }

        private fun sideAwareTurn(
            turnSide: TurnSide,
            leftText: String,
            rightText: String,
            fallbackText: String
        ): String {
            return when (turnSide) {
                TurnSide.LEFT -> leftText
                TurnSide.RIGHT -> rightText
                TurnSide.UNSPECIFIED -> fallbackText
            }
        }

        private fun roundaboutExitText(turnNumber: Int): String {
            return if (turnNumber >= 0) {
                "회전교차로 ${turnNumber}번째 출구"
            } else {
                "회전교차로"
            }
        }

        private fun String.isManeuverOnlyText(): Boolean {
            val normalized = replace(" ", "")
            return normalized in maneuverOnlyTexts
        }

        private val maneuverOnlyTexts = setOf(
            "좌회전",
            "우회전",
            "회전",
            "완만한좌회전",
            "완만한우회전",
            "급좌회전",
            "급우회전",
            "직진",
            "유턴",
            "좌측유턴",
            "우측유턴",
            "갈림길",
            "좌측갈림길",
            "우측갈림길",
            "합류",
            "좌측합류",
            "우측합류",
            "도로명변경",
            "경로안내",
            "도착"
        )
    }
}

data class HudTextBitmap(
    val width: Int,
    val height: Int,
    val hex: String
) {
    init {
        require(width > 0) { "width must be positive" }
        require(height > 0) { "height must be positive" }
        require(hex.length % 2 == 0) { "hex must contain whole bytes" }
    }
}

private fun String.escapeJson(): String {
    return buildString {
        for (char in this@escapeJson) {
            when (char) {
                '\\' -> append("\\\\")
                '"' -> append("\\\"")
                '\b' -> append("\\b")
                '\u000C' -> append("\\f")
                '\n' -> append("\\n")
                '\r' -> append("\\r")
                '\t' -> append("\\t")
                else -> {
                    if (char.code < 0x20) {
                        append("\\u")
                        append(char.code.toString(16).padStart(4, '0'))
                    } else {
                        append(char)
                    }
                }
            }
        }
    }
}
