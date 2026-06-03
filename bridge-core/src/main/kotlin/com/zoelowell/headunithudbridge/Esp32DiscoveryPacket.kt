package com.zoelowell.headunithudbridge

object Esp32DiscoveryPacket {
    const val DISCOVERY_PORT = 4211
    const val TYPE_DISCOVER = "headunit_hud_discover"
    const val TYPE_HELLO = "headunit_hud_hello"
    const val DEVICE_KIND_ESP32 = "esp32"
    const val DEVICE_KIND_PI_HUD = "pi_hud"
    const val FIELD_TYPE = "type"
    const val FIELD_IP = "ip"
    const val FIELD_UDP_PORT = "udp_port"
    const val FIELD_NAME = "name"
    const val FIELD_DEVICE_KIND = "device_kind"

    fun discoveryProbeJson(): String = """{"$FIELD_TYPE":"$TYPE_DISCOVER"}"""

    fun resolveTargetHost(payloadIp: String, sourceHost: String): String {
        return sourceHost.takeIf { it.isNotBlank() } ?: payloadIp
    }

    fun targetKindFromHello(name: String, deviceKind: String): HudTargetKind {
        val normalizedKind = deviceKind.trim().lowercase()
        if (normalizedKind == DEVICE_KIND_PI_HUD) {
            return HudTargetKind.PI_HUD
        }
        if (normalizedKind == DEVICE_KIND_ESP32) {
            return HudTargetKind.ESP32
        }

        val normalizedName = name.trim().lowercase()
        return if ("pi" in normalizedName || "raspberry" in normalizedName) {
            HudTargetKind.PI_HUD
        } else {
            HudTargetKind.ESP32
        }
    }
}

enum class HudTargetKind(
    val wireValue: String
) {
    ESP32(Esp32DiscoveryPacket.DEVICE_KIND_ESP32),
    PI_HUD(Esp32DiscoveryPacket.DEVICE_KIND_PI_HUD);

    val receivesEsp32Settings: Boolean
        get() = HudTargetPacketPolicy.acceptsPacketType(this, HudTargetPacketPolicy.TYPE_ESP32_SETTINGS)

    companion object {
        fun fromWireValue(value: String?): HudTargetKind {
            return entries.firstOrNull { it.wireValue == value?.trim()?.lowercase() } ?: ESP32
        }
    }
}
