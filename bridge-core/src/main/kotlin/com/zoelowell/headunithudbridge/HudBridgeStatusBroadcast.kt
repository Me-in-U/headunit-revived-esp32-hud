package com.zoelowell.headunithudbridge

object HudBridgeStatusBroadcast {
    const val ACTION_BRIDGE_STATUS = "com.zoelowell.headunithudbridge.BRIDGE_STATUS"

    const val EXTRA_HEADUNIT_STATE = "headunit_state"
    const val EXTRA_HUD_OUTPUT_STATE = "hud_output_state"
    const val EXTRA_ESP_CONNECTION_STATE = "esp_connection_state"
    const val EXTRA_LAST_EVENT = "last_event"
    const val EXTRA_LAST_EVENT_TIME_MILLIS = "last_event_time_millis"
    const val EXTRA_NEXT_ESP_DISCOVERY_RETRY_AT_MILLIS = "next_esp_discovery_retry_at_millis"
    const val EXTRA_SPEED_KMH = "speed_kmh"
}