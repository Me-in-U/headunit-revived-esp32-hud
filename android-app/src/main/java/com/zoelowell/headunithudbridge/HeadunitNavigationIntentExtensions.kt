package com.zoelowell.headunithudbridge

import android.content.Intent

fun Intent.toHudNavigationPacket(): HudNavigationPacket {
    return HudNavigationPacket.fromHeadunitValues(
        distanceMeters = getIntExtra(HeadunitRevivedBroadcast.EXTRA_DISTANCE_METERS, -1),
        timeSeconds = getIntExtra(HeadunitRevivedBroadcast.EXTRA_TIME_SECONDS, -1),
        road = getStringExtra(HeadunitRevivedBroadcast.EXTRA_ROAD),
        nextEventType = getIntExtra(
            HeadunitRevivedBroadcast.EXTRA_NEXT_EVENT_TYPE,
            HeadunitNavEvent.UNKNOWN.wireValue
        ),
        turnSide = getIntExtra(
            HeadunitRevivedBroadcast.EXTRA_TURN_SIDE,
            TurnSide.UNSPECIFIED.wireValue
        ),
        turnNumber = getIntExtra(HeadunitRevivedBroadcast.EXTRA_TURN_NUMBER, -1),
        turnAngle = getIntExtra(HeadunitRevivedBroadcast.EXTRA_TURN_ANGLE, -1)
    )
}

fun Intent.toNavigationFreshnessSample(): NavigationFreshnessSample {
    return NavigationFreshnessSample(
        distanceMeters = getIntExtra(HeadunitRevivedBroadcast.EXTRA_DISTANCE_METERS, -1),
        timeSeconds = getIntExtra(HeadunitRevivedBroadcast.EXTRA_TIME_SECONDS, -1),
        eventType = getIntExtra(
            HeadunitRevivedBroadcast.EXTRA_NEXT_EVENT_TYPE,
            HeadunitNavEvent.UNKNOWN.wireValue
        ),
        turnSide = getIntExtra(
            HeadunitRevivedBroadcast.EXTRA_TURN_SIDE,
            TurnSide.UNSPECIFIED.wireValue
        ),
        road = getStringExtra(HeadunitRevivedBroadcast.EXTRA_ROAD).orEmpty(),
        distanceAgeMs = getLongExtra(HeadunitRevivedBroadcast.EXTRA_TURN_DISTANCE_AGE_MS, -1L),
        turnAgeMs = getLongExtra(HeadunitRevivedBroadcast.EXTRA_TURN_DETAIL_AGE_MS, -1L),
        clusterAgeMs = getLongExtra(HeadunitRevivedBroadcast.EXTRA_CLUSTER_AGE_MS, -1L)
    )
}

fun HudNavigationPacket.withRenderedHudBitmaps(): HudNavigationPacket {
    return copy(
        roadBitmap = HudRoadBitmapRenderer.render(road),
        iconBitmap = HudManeuverIconBitmapRenderer.render(eventType, turnSide)
    )
}
