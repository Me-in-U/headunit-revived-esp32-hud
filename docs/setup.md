# Setup Guide

[English](setup.md) | [한국어](setup.ko.md) | [Project README](../README.md)

This guide covers the full Android tablet, ESP32 firmware, OLED wiring, and Wi-Fi path for the Headunit Revived ESP32 HUD bridge.

## Reference Screenshots

| Android bridge dashboard | ESP32 OLED HUD |
| --- | --- |
| [![Android bridge dashboard](assets/bridge-screen.png)](assets/bridge-screen.png) | [![ESP32 OLED HUD](assets/hud.png)](assets/hud.png) |

The dashboard screenshot shows the setup screen after Headunit and ESP32 are online. The HUD photo shows the physical two-display layout with speed on display 1 and maneuver guidance on display 2.

## Prerequisites

- Android tablet with the GitHub build of Headunit Revived installed.
- HUD Bridge Android app built from this repository.
- ESP32-S3-N16R8 style board.
- Two 128x64 I2C OLED displays.
- Phone hotspot or another Wi-Fi network that allows tablet-to-ESP32 UDP traffic.
- Android SDK for app builds.
- PlatformIO for ESP32 builds.

## Android Tablet Setup

1. Install Headunit Revived on the tablet.
2. Install the HUD Bridge Android app.
3. Connect the tablet to the same phone hotspot or Wi-Fi network that ESP32 will use.
4. Open HUD Bridge and grant the permissions shown in the `권한 / 백그라운드` card.
5. In `핫스팟 Wi-Fi`, tap `수정` if needed and enter the hotspot SSID/password.
6. Tap `BLE로 ESP 연결` to provision ESP32 over Bluetooth LE.
7. Start Android Auto projection in Headunit Revived.
8. Start route guidance from the phone navigation app.

The app waits for Android Auto projection or the first navigation update before automatic ESP32 Wi-Fi discovery. Manual discovery is still available through `Wi-Fi 검색`.

## ESP32 Firmware Setup

Build the firmware:

```powershell
platformio run -d esp32-hud -e esp32-s3-n16r8
```

Flash the firmware:

```powershell
platformio run -d esp32-hud -e esp32-s3-n16r8 -t upload
```

Open the serial monitor at `115200` and confirm:

1. BLE provisioning is advertising.
2. ESP32 receives Wi-Fi credentials from the Android app.
3. ESP32 prints a Wi-Fi IP address.
4. BLE status includes a compact connected payload such as `{"s":"c","i":"10.233.116.145"}`.
5. UDP packets print when Android sends a test packet or Headunit Revived receives navigation updates.

If serial logs do not appear after flashing over native USB, reconnect the board or press reset. The firmware enables USB CDC on boot with `ARDUINO_USB_CDC_ON_BOOT=1`.

`esp32-hud/include/config.h` is optional. If it defines `HUD_WIFI_SSID` and `HUD_WIFI_PASSWORD`, ESP32 can auto-connect after flashing. For normal use, prefer BLE provisioning so credentials are not committed to the repository.

## OLED Wiring

The firmware targets two 1.3 inch 128x64 I2C OLEDs. The default driver is SH1106 because many 1.3 inch modules sold as SSD1306-compatible use SH1106 controllers.

Display 1 wiring:

| OLED Pin | ESP32-S3 Pin |
| --- | --- |
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 8 |
| SCL | GPIO 9 |

Display 2 wiring:

| OLED Pin | ESP32-S3 Pin |
| --- | --- |
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 10 |
| SCL | GPIO 11 |

Default display configuration:

```c
#define HUD_OLED_SDA 8
#define HUD_OLED_SCL 9
#define HUD_OLED_ADDRESS 0x3C
#define HUD_OLED_WIDTH 128
#define HUD_OLED_HEIGHT 64
#define HUD_OLED_RESET -1
#define HUD_OLED_DRIVER 1106

#define HUD_OLED2_ENABLED 1
#define HUD_OLED2_SDA 10
#define HUD_OLED2_SCL 11
#define HUD_OLED2_ADDRESS 0x3C
#define HUD_OLED2_RESET -1
```

If a screen stays blank, first try address `0x3D`, then verify the board's actual SDA/SCL pins. If a confirmed SSD1306 module shows incorrect output, set `HUD_OLED_DRIVER` to `1306`. Override values in `esp32-hud/include/config.h`.

Physical layout is `[1] [2]`:

| Display | Role |
| --- | --- |
| 1 | Speed and safety face |
| 2 | Maneuver icon, next maneuver distance, selected road name |

Fixed Korean status labels are rendered from 1-bit bitmap glyphs. Route road names are rendered by Android into compact 1-bit road bitmaps, so ESP32 does not need to bundle a full Korean font.

## Network Behavior

After BLE provisioning, Android sends UDP packets directly to the ESP32 target on port `4210`. Broadcast packets are used only while no ESP32 IP is known.

Discovery uses UDP port `4211`:

- Android sends discovery probes to broadcast targets and any saved ESP32 target.
- ESP32 replies to probes and periodically broadcasts hello packets.
- Android stores the packet source address as the target host.

The foreground bridge service also runs recovery while Android Auto is active. If no ESP32 target is known, it retries discovery with backoff from 10 seconds up to 60 seconds. ESP32 also retries stored Wi-Fi credentials with backoff from 5 seconds up to 60 seconds after boot failures or Wi-Fi loss.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| BLE provisioning works but Wi-Fi discovery fails | Some phone hotspots block client-to-client traffic. Try ESP32 AP mode, USB tethering, or a separate travel router. |
| Android target is empty or stale | Tap `Wi-Fi 검색` in the `ESP32 대상` card. |
| ESP32 has an IP but receives no packets | Confirm tablet and ESP32 are on the same routable network and UDP port `4210` is reachable. |
| OLED is blank | Check I2C address, SDA/SCL pins, power, and `HUD_OLED_DRIVER`. |
| Android stops updating in the background | Grant battery optimization exemption through `백그라운드 허용`. |

## Verification Checklist

Run these before opening a pull request or sharing a build:

```powershell
.\gradlew.bat :bridge-core:test :android-app:testDebugUnitTest :android-app:assembleDebug --warning-mode all
platformio run -d esp32-hud -e esp32-s3-n16r8
```
