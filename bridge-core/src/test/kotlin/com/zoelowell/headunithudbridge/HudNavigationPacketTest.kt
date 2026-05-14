package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class HudNavigationPacketTest {
    @Test
    fun formatsRightTurnInstructionWithDistance() {
        val packet = HudNavigationPacket(
            distanceMeters = 300,
            timeSeconds = 25,
            road = "강남대로",
            eventType = HeadunitNavEvent.TURN,
            turnSide = TurnSide.RIGHT,
            turnNumber = -1,
            turnAngle = -1
        )

        assertEquals("300m 후 우회전", packet.instruction)
        assertEquals(
            "{\"distance_meters\":300,\"time_seconds\":25,\"road\":\"강남대로\",\"event_type\":4,\"turn_side\":2,\"turn_number\":-1,\"turn_angle\":-1,\"active\":true,\"instruction\":\"300m 후 우회전\"}",
            packet.toJson()
        )
    }

    @Test
    fun formatsUnknownDistanceWithoutPrefix() {
        val packet = HudNavigationPacket(
            distanceMeters = -1,
            timeSeconds = -1,
            road = "",
            eventType = HeadunitNavEvent.DESTINATION,
            turnSide = TurnSide.UNSPECIFIED,
            turnNumber = -1,
            turnAngle = -1
        )

        assertEquals("도착", packet.instruction)
    }

    @Test
    fun mapsUnknownEventToStableInstruction() {
        val packet = HudNavigationPacket(
            distanceMeters = 120,
            timeSeconds = -1,
            road = "서초대로",
            eventType = HeadunitNavEvent.UNKNOWN,
            turnSide = TurnSide.UNSPECIFIED,
            turnNumber = -1,
            turnAngle = -1
        )

        assertEquals("120m 후 경로 안내", packet.instruction)
    }

    @Test
    fun marksUnknownNoDistanceNoTimePacketAsInactiveGuidance() {
        val packet = HudNavigationPacket(
            distanceMeters = -1,
            timeSeconds = -1,
            road = "",
            eventType = HeadunitNavEvent.UNKNOWN,
            turnSide = TurnSide.UNSPECIFIED,
            turnNumber = -1,
            turnAngle = -1
        )

        assertEquals(false, packet.activeGuidance)
        assertEquals(
            "{\"distance_meters\":-1,\"time_seconds\":-1,\"road\":\"\",\"event_type\":0,\"turn_side\":3,\"turn_number\":-1,\"turn_angle\":-1,\"active\":false,\"instruction\":\"경로 안내\"}",
            packet.toJson()
        )
    }

    @Test
    fun omitsUnusedRawBroadcastFieldsFromBridgeJson() {
        val packet = HudNavigationPacket.fromHeadunitValues(
            distanceMeters = 500,
            timeSeconds = 40,
            road = "강변북로",
            nextEventType = HeadunitNavEvent.STRAIGHT.wireValue,
            turnSide = TurnSide.UNSPECIFIED.wireValue,
            turnNumber = -1,
            turnAngle = -1
        )

        val json = packet.toJson()

        assertFalse(json.contains("action_text"))
        assertFalse(json.contains("maneuver_type"))
        assertFalse(json.contains("maneuver_name"))
        assertFalse(json.contains("current_road"))
        assertFalse(json.contains("step_road"))
        assertFalse(json.contains("cue_text"))
        assertFalse(json.contains("raw_navigation_text"))
    }

    @Test
    fun fallsBackToManeuverTextWhenNoRoadNameExists() {
        val packet = HudNavigationPacket.fromHeadunitValues(
            distanceMeters = 300,
            timeSeconds = 25,
            road = "",
            nextEventType = HeadunitNavEvent.TURN.wireValue,
            turnSide = TurnSide.RIGHT.wireValue,
            turnNumber = -1,
            turnAngle = -1
        )

        assertEquals("우회전", packet.road)
    }

    @Test
    fun ignoresManeuverOnlyFieldsThenFallsBackToManeuverText() {
        val packet = HudNavigationPacket.fromHeadunitValues(
            distanceMeters = 300,
            timeSeconds = 25,
            road = "우회전",
            nextEventType = HeadunitNavEvent.TURN.wireValue,
            turnSide = TurnSide.RIGHT.wireValue,
            turnNumber = -1,
            turnAngle = -1
        )

        assertEquals("우회전", packet.road)
    }

    @Test
    fun serializesOptionalRoadTextBitmapForEsp32HangulRendering() {
        val packet = HudNavigationPacket(
            distanceMeters = 300,
            timeSeconds = 25,
            road = "강남대로",
            eventType = HeadunitNavEvent.TURN,
            turnSide = TurnSide.RIGHT,
            turnNumber = -1,
            turnAngle = -1,
            roadBitmap = HudTextBitmap(width = 16, height = 8, hex = "ff00aa55")
        )

        assertEquals(
            "{\"distance_meters\":300,\"time_seconds\":25,\"road\":\"강남대로\",\"road_bitmap_width\":16,\"road_bitmap_height\":8,\"road_bitmap_hex\":\"ff00aa55\",\"event_type\":4,\"turn_side\":2,\"turn_number\":-1,\"turn_angle\":-1,\"active\":true,\"instruction\":\"300m 후 우회전\"}",
            packet.toJson()
        )
    }

    @Test
    fun serializesOptionalManeuverIconBitmapForEsp32Rendering() {
        val packet = HudNavigationPacket(
            distanceMeters = 300,
            timeSeconds = 25,
            road = "강남대로",
            eventType = HeadunitNavEvent.TURN,
            turnSide = TurnSide.RIGHT,
            turnNumber = -1,
            turnAngle = -1,
            iconBitmap = HudTextBitmap(width = 8, height = 8, hex = "183c7effff7e3c18")
        )

        assertEquals(
            "{\"distance_meters\":300,\"time_seconds\":25,\"road\":\"강남대로\",\"icon_bitmap_width\":8,\"icon_bitmap_height\":8,\"icon_bitmap_hex\":\"183c7effff7e3c18\",\"event_type\":4,\"turn_side\":2,\"turn_number\":-1,\"turn_angle\":-1,\"active\":true,\"instruction\":\"300m 후 우회전\"}",
            packet.toJson()
        )
    }

    @Test
    fun serializesCompactHudJsonForEsp32UdpRendering() {
        val packet = HudNavigationPacket.fromHeadunitValues(
            distanceMeters = 3700,
            timeSeconds = 496,
            road = "창원터널",
            nextEventType = HeadunitNavEvent.FORK.wireValue,
            turnSide = TurnSide.LEFT.wireValue,
            turnNumber = -1,
            turnAngle = -1
        ).copy(
            roadBitmap = HudTextBitmap(width = 76, height = 16, hex = "aa".repeat(160)),
            iconBitmap = HudTextBitmap(width = 50, height = 42, hex = "55".repeat(294))
        )

        val json = packet.toHudJson()

        assertTrue(json.contains("\"road_bitmap_hex\""))
        assertTrue(json.contains("\"icon_bitmap_hex\""))
        assertFalse(json.contains("raw_navigation_text"))
        assertFalse(json.contains("action_text"))
        assertFalse(json.contains("cue_texts"))
        assertTrue(json.toByteArray(Charsets.UTF_8).size < 1400)
    }
}
