# Headunit Revived ESP32 HUD

Companion project for forwarding Headunit Revived Android Auto navigation guidance to an ESP32 HUD.

The repository is intentionally split into three parts:

- `android-app/`: Kotlin Android bridge app installed on the tablet running Headunit Revived.
- `bridge-core/`: Pure Kotlin packet mapping and formatting logic shared by the Android app and unit tests.
- `esp32-hud/`: PlatformIO firmware for an ESP32-S3-N16R8 style board that is provisioned over BLE, joins Wi-Fi, listens for UDP HUD packets, and renders them on two 128x64 I2C OLEDs. The default OLED driver is SH1106 because many 1.3 inch modules use that controller even when sold as SSD1306-compatible.

The first-run setup path is BLE provisioning:

1. ESP32 advertises `Headunit HUD` over Bluetooth LE.
2. The Android app writes the phone hotspot SSID/password to ESP32.
3. ESP32 joins the hotspot and sends a compact BLE status notification that includes the ESP32 IP address.
4. The Android app automatically discovers ESP32 on the hotspot using UDP discovery port `4211`.
5. The Android app sends HUD navigation packets to that ESP32 IP over UDP port `4210`. Broadcast is used only while no ESP32 IP is known.
6. ESP32 renders speed/safety and maneuver guidance across two OLEDs in physical order `[1] [2]`.

HUD packets are sent fire-and-forget over UDP so navigation updates are not delayed by return traffic from ESP32. Each UDP payload includes a monotonic `seq` value, and ESP32 ignores stale packets that arrive after newer packets.

ESP32 stores Wi-Fi credentials in NVS and retries hotspot reconnection with backoff after boot failures or Wi-Fi loss.

The Android app dashboard groups live state into Headunit, ESP32, HUD output, Wi-Fi credentials, permissions, and background-running categories. ESP32 state is shown as `connected`, `connecting`, or `disconnected`, and failed automatic discovery shows the next retry countdown while Android Auto is active. Automatic discovery is skipped once an ESP32 target is known.

If both devices are on the same phone hotspot but discovery still times out, the hotspot is likely blocking client-to-client traffic. In that case use ESP32 AP mode, a separate router, or another network path that allows tablet-to-ESP32 UDP.

The app includes an ESP32 debug overlay switch. When disabled, the OLED hides the top `NAV/IP` header and bottom road/debug line, then expands the main maneuver area.

## Initial Verification

```powershell
gradle :bridge-core:test :android-app:assembleDebug --warning-mode all
```

Android APK builds require an Android SDK configured via `ANDROID_HOME` or `local.properties`.

ESP32 builds require PlatformIO:

```powershell
platformio run -d esp32-hud -e esp32-s3-n16r8
```

The ESP32 environment uses a project-local custom board definition for generic ESP32-S3-N16R8 modules in `esp32-hud/boards/esp32-s3-n16r8.json`.
