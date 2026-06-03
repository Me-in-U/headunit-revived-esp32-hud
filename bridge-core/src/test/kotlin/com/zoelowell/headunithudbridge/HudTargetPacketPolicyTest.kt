package com.zoelowell.headunithudbridge

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class HudTargetPacketPolicyTest {
    @Test
    fun piHudAcceptsOnlyNavigationAndBackupSpeedPacketsFromAndroidBridge() {
        assertTrue(HudTargetPacketPolicy.acceptsPacketType(HudTargetKind.PI_HUD, HudTargetPacketPolicy.TYPE_NAVIGATION))
        assertTrue(HudTargetPacketPolicy.acceptsPacketType(HudTargetKind.PI_HUD, HudTargetPacketPolicy.TYPE_BACKUP_SPEED))

        assertFalse(HudTargetPacketPolicy.acceptsPacketType(HudTargetKind.PI_HUD, HudTargetPacketPolicy.TYPE_ESP32_SETTINGS))
        assertFalse(HudTargetPacketPolicy.acceptsPacketType(HudTargetKind.PI_HUD, HudTargetPacketPolicy.TYPE_VEHICLE_STATUS))
    }

    @Test
    fun esp32AcceptsNavigationBackupSpeedAndEsp32SettingsPackets() {
        assertTrue(HudTargetPacketPolicy.acceptsPacketType(HudTargetKind.ESP32, HudTargetPacketPolicy.TYPE_NAVIGATION))
        assertTrue(HudTargetPacketPolicy.acceptsPacketType(HudTargetKind.ESP32, HudTargetPacketPolicy.TYPE_BACKUP_SPEED))
        assertTrue(HudTargetPacketPolicy.acceptsPacketType(HudTargetKind.ESP32, HudTargetPacketPolicy.TYPE_ESP32_SETTINGS))

        assertFalse(HudTargetPacketPolicy.acceptsPacketType(HudTargetKind.ESP32, HudTargetPacketPolicy.TYPE_VEHICLE_STATUS))
    }
}
