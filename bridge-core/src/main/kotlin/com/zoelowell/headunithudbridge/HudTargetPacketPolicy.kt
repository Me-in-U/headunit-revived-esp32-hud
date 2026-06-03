package com.zoelowell.headunithudbridge

object HudTargetPacketPolicy {
    const val TYPE_NAVIGATION = "navigation"
    const val TYPE_BACKUP_SPEED = HudSpeedPacket.TYPE_SPEED
    const val TYPE_ESP32_SETTINGS = Esp32SettingsPacket.TYPE_SETTINGS
    const val TYPE_VEHICLE_STATUS = "vehicle_status"

    fun acceptsPacketType(targetKind: HudTargetKind, packetType: String): Boolean {
        return when (targetKind) {
            HudTargetKind.ESP32 -> packetType in setOf(TYPE_NAVIGATION, TYPE_BACKUP_SPEED, TYPE_ESP32_SETTINGS)
            HudTargetKind.PI_HUD -> packetType in setOf(TYPE_NAVIGATION, TYPE_BACKUP_SPEED)
        }
    }
}
