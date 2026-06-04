# Headunit Revived ESP32 HUD

[English](README.md) | [한국어](README.ko.md)

Companion HUD stack for showing Headunit Revived navigation guidance on a separate display.

This project is an experimental companion stack. It does not fork Headunit Revived. The current primary target is a Raspberry Pi 4B with a 1920x480 HDMI auxiliary display. The Pi reads confirmed runtime vehicle data through iCar/ELM327 OBD and CANable/SocketCAN, renders the HUD locally, and optionally receives Android bridge navigation plus tablet/GPS backup speed when both devices are on the same network. Raw OBD/CAN investigation and live simulation are handled in the Windows Electron layout editor before deployment.

The older ESP32 dual-OLED HUD path remains in the repository and still supports BLE provisioning plus UDP packet rendering.

## Project Status

- Primary hardware target: Raspberry Pi 4B 4GB, CANable, and iCar Pro 2S/ELM327.
- Primary display target: 8.8 inch class 1920x480 HDMI IPS auxiliary display.
- Android target: a tablet running Headunit Revived and this bridge app. On the Pi path it sends navigation and backup speed only.
- Layout: a Windows layout editor saves 1920x480 JSON layouts that the Pi renders directly. Value elements such as speed and RPM support digital, bar, analog, needle, and sport gauge styles with configurable maximum values.
- Legacy target: ESP32-S3-N16R8 with two 128x64 I2C OLEDs.
- Transport: local runtime OBD/CAN on Pi, Windows OBD BLE/CANable SLCAN for analysis and simulation, UDP for optional Android navigation, and BLE only for ESP32 first-run Wi-Fi provisioning.
- Stability: active prototype. Packet fields are additive and should remain backward compatible.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `android-app/` | Kotlin Android app that receives Headunit Revived broadcasts, provisions ESP32 over BLE, discovers the HUD over Wi-Fi, and sends live HUD packets. |
| `bridge-core/` | Pure Kotlin packet, state, timing, and mapping logic with unit tests. |
| `esp32-hud/` | PlatformIO firmware for ESP32-S3, BLE provisioning, Wi-Fi reconnect, UDP discovery, packet parsing, and OLED rendering. |
| `pi-hud/` | Raspberry Pi 4B 1920x480 pygame HUD runtime that merges local OBD/CAN with optional Android navigation UDP. |
| `layout-editor-electron/` | Modern Electron layout editor for the shared 1920x480 HUD JSON. It reuses the Pi pygame renderer for accurate previews and provides Windows OBD/CAN connection, simulation, and analysis tools. |
| `layouts/` | Shared Pi HUD layout JSON files. |
| `vehicles/` | Vehicle profile JSON files for future vehicle expansion. |
| `docs/setup.md` | Setup guide for Android, ESP32, OLED wiring, and network troubleshooting. |
| `docs/protocol.md` | Wire protocol reference for broadcasts, BLE provisioning, UDP HUD packets, discovery, settings, and speed packets. |

## How It Works

1. Pi opens the 1920x480 HDMI display and renders the selected layout JSON.
2. Windows editor can connect to OBD BLE and CANable USB/SLCAN to simulate live values, inspect CAN/OBD traffic, and save confirmed profile mappings.
3. Pi reads standard OBD PIDs and confirmed CAN signals through iCar/ELM327 and CANable/SocketCAN.
4. Pi answers Android bridge discovery on UDP port `4211` with `device_kind=pi_hud`.
5. Headunit Revived emits navigation broadcasts on the tablet.
6. The bridge app maps those broadcasts into compact JSON HUD packets.
7. For Pi targets, the bridge sends navigation packets and `type=speed` backup speed only.
8. Pi receives UDP packets on port `4210`, ignores stale sequence numbers, and merges optional navigation with local vehicle data.

HUD packets are fire-and-forget. HUD receivers do not ACK live navigation packets, so delayed return traffic cannot slow down current guidance.

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

Run Pi HUD and layout checks:

```powershell
$env:PYTHONPATH=(Resolve-Path 'pi-hud').Path
.\pi-hud\.venv\Scripts\python.exe -m unittest discover -s pi-hud\tests
.\pi-hud\.venv\Scripts\python.exe pi-hud\scripts\verify-layout.py layouts\avante_hd_2010_default.json --width 1920 --height 480
```

Run or package the Electron layout editor:

```powershell
cd layout-editor-electron
npm install
npm test
npm start
npm run build
```

For JSON saved by the Windows layout editor, verify the editor handoff digest before copying it to the Pi:

```powershell
.\pi-hud\.venv\Scripts\python.exe pi-hud\scripts\verify-layout.py path\to\saved-layout.json --width 1920 --height 480 --require-handoff
```

Build a field pack for copying the layout, vehicle profiles, warning icon PNG assets, and env example to the Pi:

```powershell
.\pi-hud\.venv\Scripts\python.exe pi-hud\scripts\build-field-pack.py --output field-pack\headunit-pi-field-pack.zip
```

The Electron layout editor's `Field Pack` button writes the same zip format. Warning icons are always visible in the editor preview for placement, but the Pi runtime only shows each icon when its `warnings.*` value is active.

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
- Headunit Revived patch guide: [한국어](docs/headunit-revived-patch.ko.md)
- Raspberry Pi HUD runtime guide: [한국어](docs/pi-hud-runtime.ko.md)

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
