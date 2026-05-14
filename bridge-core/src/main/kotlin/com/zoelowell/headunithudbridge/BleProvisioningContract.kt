package com.zoelowell.headunithudbridge

object BleProvisioningContract {
    const val DEVICE_NAME = "Headunit HUD"
    const val SERVICE_UUID = "3f2d8a62-8b0f-4c0d-9d2b-7b71d831e001"
    const val WIFI_CREDENTIALS_UUID = "3f2d8a62-8b0f-4c0d-9d2b-7b71d831e002"
    const val STATUS_UUID = "3f2d8a62-8b0f-4c0d-9d2b-7b71d831e003"
    const val CLIENT_CHARACTERISTIC_CONFIG_UUID = "00002902-0000-1000-8000-00805f9b34fb"

    const val FIELD_SSID = "ssid"
    const val FIELD_PASSWORD = "password"
    const val FIELD_UDP_PORT = "udp_port"
    const val FIELD_STATE = "state"
    const val FIELD_IP = "ip"
    const val FIELD_MESSAGE = "message"
    const val FIELD_COMPACT_STATE = "s"
    const val FIELD_COMPACT_IP = "i"
    const val FIELD_COMPACT_MESSAGE = "m"

    const val STATE_IDLE = "idle"
    const val STATE_CONNECTING = "connecting"
    const val STATE_CONNECTED = "connected"
    const val STATE_FAILED = "failed"

    const val COMPACT_STATE_IDLE = "i"
    const val COMPACT_STATE_CONNECTING = "g"
    const val COMPACT_STATE_CONNECTED = "c"
    const val COMPACT_STATE_FAILED = "f"

    const val DEFAULT_UDP_PORT = 4210
}