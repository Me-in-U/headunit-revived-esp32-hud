package com.zoelowell.headunithudbridge

import android.content.Intent
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class HeadunitNavigationIntentExtensionsTest {
    @Test
    fun mapsHeadunitNavigationBroadcastToHudPacket() {
        val intent = Intent(HeadunitRevivedBroadcast.ACTION_NAVIGATION_UPDATE)
            .putExtra(HeadunitRevivedBroadcast.EXTRA_DISTANCE_METERS, 250)
            .putExtra(HeadunitRevivedBroadcast.EXTRA_TIME_SECONDS, 35)
            .putExtra(HeadunitRevivedBroadcast.EXTRA_ROAD, "강남대로")
            .putExtra(HeadunitRevivedBroadcast.EXTRA_NEXT_EVENT_TYPE, HeadunitNavEvent.TURN.wireValue)
            .putExtra(HeadunitRevivedBroadcast.EXTRA_TURN_SIDE, TurnSide.RIGHT.wireValue)
            .putExtra(HeadunitRevivedBroadcast.EXTRA_TURN_NUMBER, -1)
            .putExtra(HeadunitRevivedBroadcast.EXTRA_TURN_ANGLE, 90)

        val packet = intent.toHudNavigationPacket()

        assertEquals(250, packet.distanceMeters)
        assertEquals(35, packet.timeSeconds)
        assertEquals("강남대로", packet.road)
        assertEquals(HeadunitNavEvent.TURN, packet.eventType)
        assertEquals(TurnSide.RIGHT, packet.turnSide)
        assertEquals(-1, packet.turnNumber)
        assertEquals(90, packet.turnAngle)
    }

    @Test
    fun attachesRenderedHudBitmapsToNavigationPacket() {
        val packet = HudNavigationPacket.fromHeadunitValues(
            distanceMeters = 250,
            timeSeconds = 35,
            road = "강남대로",
            nextEventType = HeadunitNavEvent.TURN.wireValue,
            turnSide = TurnSide.RIGHT.wireValue,
            turnNumber = -1,
            turnAngle = 90
        ).withRenderedHudBitmaps()

        assertNotNull(packet.roadBitmap)
        assertNotNull(packet.iconBitmap)
    }
}
