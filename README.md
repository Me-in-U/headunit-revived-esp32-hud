# Headunit Revived ESP32 HUD

[English](README.md) | [한국어](README.ko.md)

Android-to-ESP32 bridge for showing Headunit Revived navigation guidance on a small OLED HUD.

This project is an experimental companion stack. It does not fork Headunit Revived. Instead, a tablet-side Android app listens for Headunit Revived navigation broadcasts, converts them into compact UDP packets, and sends them to ESP32 firmware that renders speed and maneuver guidance on OLED displays.

## Project Status

- Hardware target: ESP32-S3-N16R8 style boards.
- Display target: two 128x64 I2C OLEDs in physical layout `[1] [2]`.
- Android target: a tablet running Headunit Revived and this bridge app.
- Transport: BLE for first-run Wi-Fi provisioning, UDP for live HUD packets.
- Stability: active prototype. Packet fields are additive and should remain backward compatible.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `android-app/` | Kotlin Android app that receives Headunit Revived broadcasts, provisions ESP32 over BLE, discovers the HUD over Wi-Fi, and sends live HUD packets. |
| `bridge-core/` | Pure Kotlin packet, state, timing, and mapping logic with unit tests. |
| `esp32-hud/` | PlatformIO firmware for ESP32-S3, BLE provisioning, Wi-Fi reconnect, UDP discovery, packet parsing, and OLED rendering. |
| `docs/setup.md` | Setup guide for Android, ESP32, OLED wiring, and network troubleshooting. |
| `docs/protocol.md` | Wire protocol reference for broadcasts, BLE provisioning, UDP HUD packets, discovery, settings, and speed packets. |

## How It Works

1. ESP32 advertises `Headunit HUD` over Bluetooth LE.
2. The Android app writes phone hotspot credentials to ESP32 over BLE.
3. ESP32 joins Wi-Fi and starts UDP listeners.
4. The Android app discovers the ESP32 target on UDP port `4211`.
5. Headunit Revived emits navigation broadcasts on the tablet.
6. The bridge app maps those broadcasts into compact JSON HUD packets.
7. ESP32 receives UDP packets on port `4210`, ignores stale sequence numbers, and renders the HUD.

HUD packets are fire-and-forget. ESP32 does not ACK live navigation packets, so delayed return traffic cannot slow down current guidance.

## Screenshots

| Android bridge dashboard | ESP32 OLED HUD |
| --- | --- |
| [![Android bridge dashboard](docs/assets/bridge-screen.png)](docs/assets/bridge-screen.png) | [![ESP32 OLED HUD](docs/assets/hud.png)](docs/assets/hud.png) |

Click either image to open the full-size reference.

## Quick Start

Build and test the Android side:

```powershell
.\gradlew.bat :bridge-core:test :android-app:testDebugUnitTest :android-app:assembleDebug --warning-mode all
```

Build the ESP32 firmware:

```powershell
platformio run -d esp32-hud -e esp32-s3-n16r8
```

Flash the ESP32 firmware:

```powershell
platformio run -d esp32-hud -e esp32-s3-n16r8 -t upload
```

Android APK builds require an Android SDK configured through `ANDROID_HOME` or `local.properties`. ESP32 builds require PlatformIO.

## Hardware Notes

The default OLED driver is SH1106 because many 1.3 inch 128x64 modules sold as SSD1306-compatible use SH1106 controllers. Override the display configuration in `esp32-hud/include/config.h` when your module uses different pins, address, or driver.

Default physical display roles:

| Display | Role | Default bus |
| --- | --- | --- |
| 1 | Speed and safety face | GPIO 8/9, `0x3C` |
| 2 | Navigation face | GPIO 10/11, `0x3C` |

## Documentation

- Setup guide: [English](docs/setup.md) | [한국어](docs/setup.ko.md)
- Protocol reference: [English](docs/protocol.md) | [한국어](docs/protocol.ko.md)

## Contributing

Focused issues and pull requests are welcome. Good contributions for this project usually include:

- a clear hardware/software setup description,
- logs or screenshots for runtime problems,
- Android unit tests for bridge logic changes,
- PlatformIO compile verification for firmware changes,
- protocol documentation updates when packet fields change.

Keep secrets out of commits. Do not commit Wi-Fi SSIDs, passwords, local SDK paths, signing keys, or device-specific private IP addresses.

## License

No license file has been selected yet. Until a license is added, treat the code as source-available for review and collaboration, not as broadly licensed for redistribution.
