package com.zoelowell.headunithudbridge

import android.content.Context

object ProvisioningStore {
    private const val PREFS_NAME = "hud_provisioning"
    private const val KEY_TARGET_HOST = "target_host"
    private const val KEY_TARGET_PORT = "target_port"
    private const val KEY_TARGET_KIND = "target_kind"
    private const val KEY_DEBUG_OVERLAY = "debug_overlay"
    private const val KEY_SPEED_UNIT_VISIBLE = "speed_unit_visible"
    private const val KEY_SPEED_FONT_SIZE = "speed_font_size"
    private const val KEY_WIFI_SSID = "wifi_ssid"
    private const val KEY_WIFI_PASSWORD = "wifi_password"
    private const val KEY_HUD_LANGUAGE = "hud_language"

    fun saveTarget(
        context: Context,
        host: String,
        port: Int = BleProvisioningContract.DEFAULT_UDP_PORT,
        targetKind: HudTargetKind = HudTargetKind.ESP32
    ) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_TARGET_HOST, host)
            .putInt(KEY_TARGET_PORT, port)
            .putString(KEY_TARGET_KIND, targetKind.wireValue)
            .apply()
    }

    fun targetHost(context: Context): String? {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getString(KEY_TARGET_HOST, null)
            ?.takeIf { it.isNotBlank() }
    }

    fun targetPort(context: Context): Int {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getInt(KEY_TARGET_PORT, BleProvisioningContract.DEFAULT_UDP_PORT)
    }

    fun targetKind(context: Context): HudTargetKind {
        return HudTargetKind.fromWireValue(
            context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                .getString(KEY_TARGET_KIND, HudTargetKind.ESP32.wireValue)
        )
    }

    fun clearTarget(context: Context) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .remove(KEY_TARGET_HOST)
            .remove(KEY_TARGET_PORT)
            .remove(KEY_TARGET_KIND)
            .apply()
    }

    fun saveWifiCredentials(context: Context, ssid: String, password: String) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_WIFI_SSID, ssid)
            .putString(KEY_WIFI_PASSWORD, password)
            .apply()
    }

    fun wifiSsid(context: Context): String {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getString(KEY_WIFI_SSID, "")
            .orEmpty()
    }

    fun wifiPassword(context: Context): String {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getString(KEY_WIFI_PASSWORD, "")
            .orEmpty()
    }

    fun saveDebugOverlayEnabled(context: Context, enabled: Boolean) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(KEY_DEBUG_OVERLAY, enabled)
            .apply()
    }

    fun debugOverlayEnabled(context: Context): Boolean {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getBoolean(KEY_DEBUG_OVERLAY, false)
    }

    fun saveSpeedUnitVisible(context: Context, visible: Boolean) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(KEY_SPEED_UNIT_VISIBLE, visible)
            .apply()
    }

    fun speedUnitVisible(context: Context): Boolean {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getBoolean(KEY_SPEED_UNIT_VISIBLE, true)
    }

    fun saveSpeedFontSize(context: Context, size: Int) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putInt(
                KEY_SPEED_FONT_SIZE,
                size.coerceIn(Esp32SettingsPacket.MIN_SPEED_FONT_SIZE, Esp32SettingsPacket.MAX_SPEED_FONT_SIZE)
            )
            .apply()
    }

    fun speedFontSize(context: Context): Int {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getInt(KEY_SPEED_FONT_SIZE, Esp32SettingsPacket.DEFAULT_SPEED_FONT_SIZE)
            .coerceIn(Esp32SettingsPacket.MIN_SPEED_FONT_SIZE, Esp32SettingsPacket.MAX_SPEED_FONT_SIZE)
    }

    fun saveHudLanguage(context: Context, language: String) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_HUD_LANGUAGE, Esp32SettingsPacket.cleanLanguage(language))
            .apply()
    }

    fun hudLanguage(context: Context): String {
        return Esp32SettingsPacket.cleanLanguage(
            context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                .getString(KEY_HUD_LANGUAGE, Esp32SettingsPacket.DEFAULT_LANGUAGE)
                .orEmpty()
        )
    }
}
