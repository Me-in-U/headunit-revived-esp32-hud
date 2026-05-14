package com.zoelowell.headunithudbridge

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class HeadunitRevivedBroadcastTest {
    @Test
    fun keepsOriginalDestinationSummaryExtrasInBroadcastContract() {
        val values = HeadunitRevivedBroadcast::class.java.fields
            .mapNotNull { field -> field.get(null) as? String }
            .toSet()

        assertTrue(values.contains("total_distance_meters"))
        assertTrue(values.contains("total_time_seconds"))
        assertTrue(values.contains("estimated_arrival"))
    }

    @Test
    fun excludesNonHudDebugExtrasFromBroadcastContract() {
        val values = HeadunitRevivedBroadcast::class.java.fields
            .mapNotNull { field -> field.get(null) as? String }
            .toSet()

        assertFalse(values.contains("distance_source"))
        assertFalse(values.contains("time_source"))
        assertFalse(values.contains("nav_event_type"))
        assertFalse(values.contains("cluster_status"))
        assertFalse(values.contains("step_distance_meters"))
        assertFalse(values.contains("step_time_seconds"))
        assertFalse(values.contains("next_maneuver"))
        assertFalse(values.contains("maneuver_type"))
        assertFalse(values.contains("maneuver_name"))
        assertFalse(values.contains("current_road"))
        assertFalse(values.contains("step_road"))
        assertFalse(values.contains("cue_text"))
        assertFalse(values.contains("cue_texts"))
        assertFalse(values.contains("unknown_navigation_fields"))
        assertFalse(values.contains("nav_state_age_ms"))
        assertFalse(values.contains("current_position_age_ms"))
        assertFalse(values.contains("raw_navigation_text"))
    }
}
