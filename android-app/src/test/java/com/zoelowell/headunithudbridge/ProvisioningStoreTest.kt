package com.zoelowell.headunithudbridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class ProvisioningStoreTest {
    private val context = RuntimeEnvironment.getApplication()

    @Before
    fun clearPreferences() {
        context.getSharedPreferences("hud_provisioning", 0)
            .edit()
            .clear()
            .commit()
    }

    @Test
    fun defaultsHudLanguageToKorean() {
        assertEquals(Esp32SettingsPacket.LANGUAGE_KOREAN, ProvisioningStore.hudLanguage(context))
    }

    @Test
    fun defaultsDebugOverlayToOff() {
        assertFalse(ProvisioningStore.debugOverlayEnabled(context))
    }

    @Test
    fun storesEnglishHudLanguage() {
        ProvisioningStore.saveHudLanguage(context, Esp32SettingsPacket.LANGUAGE_ENGLISH)

        assertEquals(Esp32SettingsPacket.LANGUAGE_ENGLISH, ProvisioningStore.hudLanguage(context))
    }

    @Test
    fun normalizesUnsupportedHudLanguageToKorean() {
        ProvisioningStore.saveHudLanguage(context, "jp")

        assertEquals(Esp32SettingsPacket.LANGUAGE_KOREAN, ProvisioningStore.hudLanguage(context))
    }

    @Test
    fun hudLocaleLocalizesDashboardStateText() {
        ProvisioningStore.saveHudLanguage(context, Esp32SettingsPacket.LANGUAGE_KOREAN)

        val koreanContext = context.withHudLocale()

        assertEquals("온라인 · 내비게이션 안내 수신", koreanContext.getString(R.string.headunit_navigation_active))
        assertEquals("연결됨 · UDP 대상 준비", koreanContext.getString(R.string.esp_connected))

        ProvisioningStore.saveHudLanguage(context, Esp32SettingsPacket.LANGUAGE_ENGLISH)

        val englishContext = context.withHudLocale()

        assertEquals("online - navigation guidance received", englishContext.getString(R.string.headunit_navigation_active))
        assertEquals("connected - UDP target ready", englishContext.getString(R.string.esp_connected))
    }

    @Test
    fun hudLocaleLocalizesRawNavigationTableText() {
        ProvisioningStore.saveHudLanguage(context, Esp32SettingsPacket.LANGUAGE_KOREAN)

        val koreanContext = context.withHudLocale()

        assertEquals("Raw 내비 브로드캐스트", koreanContext.getString(R.string.card_raw_navigation))
        assertEquals("필드", koreanContext.getString(R.string.raw_table_field))
        assertEquals("거리", koreanContext.getString(R.string.raw_field_distance_meters))

        ProvisioningStore.saveHudLanguage(context, Esp32SettingsPacket.LANGUAGE_ENGLISH)

        val englishContext = context.withHudLocale()

        assertEquals("Raw Nav Broadcast", englishContext.getString(R.string.card_raw_navigation))
        assertEquals("Field", englishContext.getString(R.string.raw_table_field))
        assertEquals("Distance", englishContext.getString(R.string.raw_field_distance_meters))
    }

    @Test
    fun hudLocaleUsesProgressAndCompleteSuffixesForKoreanDiscoveryStates() {
        ProvisioningStore.saveHudLanguage(context, Esp32SettingsPacket.LANGUAGE_KOREAN)

        val koreanContext = context.withHudLocale()

        assertEquals("연결중 · Wi-Fi 검색중", koreanContext.getString(R.string.esp_discovering))
        assertEquals("진행중", koreanContext.getString(R.string.retry_in_progress))
        assertEquals(
            "ESP32 Wi-Fi 검색중: UDP 4211",
            koreanContext.getString(R.string.discovery_searching, Esp32DiscoveryPacket.DISCOVERY_PORT)
        )
        assertEquals(
            "Android Auto 온라인. ESP32 Wi-Fi 자동 검색중",
            koreanContext.getString(R.string.status_android_auto_online_auto_search)
        )
        assertEquals(
            "Android Auto 프로젝션 온라인. ESP32 Wi-Fi 자동 검색중",
            koreanContext.getString(
                R.string.status_android_auto_source_online,
                koreanContext.getString(R.string.source_projection)
            )
        )
        assertEquals(
            "ESP32 Wi-Fi 검색됨: 10.0.0.4:4210",
            koreanContext.getString(R.string.status_esp_wifi_discovery_success, "10.0.0.4", 4210)
        )
        assertEquals("ESP 자동 검색중", koreanContext.getString(R.string.event_esp32_discovery_started))
        assertEquals("ESP 자동 검색됨, 설정 전송됨", koreanContext.getString(R.string.event_esp32_discovery_found_sent))
        assertEquals(
            "ESP32 연결 상태 일부 수신. Wi-Fi 검색중",
            koreanContext.getString(R.string.ble_compact_status_received)
        )
    }
}
