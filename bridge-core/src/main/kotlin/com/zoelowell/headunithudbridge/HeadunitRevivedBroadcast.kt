package com.zoelowell.headunithudbridge

object HeadunitRevivedBroadcast {
    const val ACTION_NAVIGATION_UPDATE = "com.andrerinas.headunitrevived.NAVIGATION_UPDATE"
    const val ACTION_PROJECTION_REQUEST = "com.andrerinas.headunitrevived.ACTION_REQUEST_PROJECTION"

    const val EXTRA_DISTANCE_METERS = "distance_meters"
    const val EXTRA_TIME_SECONDS = "time_seconds"
    const val EXTRA_ROAD = "road"
    const val EXTRA_NEXT_EVENT_TYPE = "next_event_type"
    const val EXTRA_ACTION_TEXT = "action_text"
    const val EXTRA_TURN_SIDE = "turn_side"
    const val EXTRA_TURN_NUMBER = "turn_number"
    const val EXTRA_TURN_ANGLE = "turn_angle"
    const val EXTRA_TOTAL_DISTANCE_METERS = "total_distance_meters"
    const val EXTRA_TOTAL_TIME_SECONDS = "total_time_seconds"
    const val EXTRA_ESTIMATED_ARRIVAL = "estimated_arrival"

    /** Age in milliseconds for the last NavigationClusterStatus message, or -1 if not set. */
    const val EXTRA_CLUSTER_AGE_MS = "cluster_age_ms"

    /** Age in milliseconds for the last legacy NextTurnDetail message, or -1 if not set. */
    const val EXTRA_TURN_DETAIL_AGE_MS = "turn_detail_age_ms"

    /** Age in milliseconds for the last legacy NextTurnDistanceEvent message, or -1 if not set. */
    const val EXTRA_TURN_DISTANCE_AGE_MS = "turn_distance_age_ms"

    const val PERMISSION_NAVIGATION_UPDATE = "com.andrerinas.headunitrevived.permission.NAVIGATION_UPDATE"
}
