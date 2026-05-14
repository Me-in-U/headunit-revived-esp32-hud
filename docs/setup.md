# Setup Notes

## Android Tablet

1. Install the GitHub build of Headunit Revived.
2. Install the HUD Bridge Android app from this repository.
3. Connect the tablet to the phone hotspot.
4. Open HUD Bridge and grant the permissions shown in the `권한 / 백그라운드` card.
5. In the `핫스팟 Wi-Fi` card, tap `수정` if needed and enter the phone hotspot SSID/password. The app stores those values automatically.
6. Tap `BLE로 ESP 연결` so the app can provision ESP32.
7. The app waits for Android Auto projection or the first navigation update, then automatically searches for ESP32 on Wi-Fi.
8. Watch the `상태` card. Headunit should move from `offline` to `online`; ESP32 should move through `connecting` to `connected`. If automatic discovery fails while Headunit is online, the card shows the next retry countdown.
9. If the target is empty or stale before Android Auto starts, tap `Wi-Fi 검색` in the `ESP32 대상` card.
10. Use `ESP32 디버그 영역 표시` to show or hide the OLED top/bottom debug rows.
11. Tap `백그라운드 허용` and approve Android's battery optimization exception if the tablet shows the prompt.
12. Tap `테스트 전송` and confirm the Android app reports that the UDP packet was sent and the ESP32 serial monitor prints a HUD message.
13. Start Android Auto projection in Headunit Revived.
14. Start route guidance in the phone navigation app.

## ESP32

The current PlatformIO environment targets an ESP32-S3-N16R8 style board:

```ini
[env:esp32-s3-n16r8]
board = esp32-s3-n16r8
```

1. Flash with PlatformIO: `platformio run -d esp32-hud -e esp32-s3-n16r8 -t upload`.
2. Open serial monitor at `115200`.
3. Confirm the log says BLE provisioning is advertising.
4. Provision it from the Android app over Bluetooth.
5. Confirm the log prints the Wi-Fi IP address.
6. Confirm the BLE status log includes a compact connected payload with IP, for example `{"s":"c","i":"10.233.116.145"}`.
7. Confirm packets print when the Android app sends a test packet or Headunit Revived receives navigation updates.

If serial logs do not appear after flashing over native USB, reconnect the board or press reset. The firmware enables USB CDC on boot with `ARDUINO_USB_CDC_ON_BOOT=1`.

`esp32-hud/include/config.h` is optional. If it exists and contains `HUD_WIFI_SSID` and `HUD_WIFI_PASSWORD`, ESP32 can auto-connect without BLE after flashing. For normal use, prefer BLE provisioning so credentials are not committed to the repository.

## OLED Wiring

The firmware targets two 1.3 inch 128x64 I2C OLEDs. Many 1.3 inch modules sold as SSD1306-compatible actually use an SH1106 controller, so the default driver is SH1106.

Default display 1 wiring:

| OLED Pin | ESP32-S3 Pin |
| --- | --- |
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 8 |
| SCL | GPIO 9 |

Default display 2 wiring:

| OLED Pin | ESP32-S3 Pin |
| --- | --- |
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 10 |
| SCL | GPIO 11 |

Display 1 stays on the first I2C bus at `0x78` / `0x3C`. Display 2 stays on the second I2C bus at `0x78` / `0x3C`.

Default display settings:

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

If the screen stays blank, first try address `0x3D`, then verify the board's actual SDA/SCL pins. If a confirmed SSD1306 module shows incorrect output, set `HUD_OLED_DRIVER` to `1306`. Override these values in `esp32-hud/include/config.h`.

Physical layout is `[1] [2]`. Display 1 is the speed and safety face. Display 2 is the navigation face: maneuver icon, next maneuver distance, and the selected road name.

The firmware renders fixed Korean status labels from 1-bit bitmap glyphs and renders route road names from Android-generated 1-bit road bitmaps. This avoids showing duplicate words such as `우회전`/`좌회전` when the icon already carries the direction.

## Network

After BLE provisioning, the Android bridge sends UDP packets directly to the ESP32 IP address on port `4210`. It uses `255.255.255.255:4210` only while no ESP32 target IP is known.

The app can refresh the ESP32 target by tapping `Wi-Fi 검색`. The app sends UDP discovery probes on port `4211`, listens for ESP32 hello packets, and stores the packet source address as the target host. Probes are sent to `255.255.255.255`, the tablet subnet broadcast address when Android exposes one, and the saved ESP32 target IP when one exists.

After BLE provisioning, the app does not immediately search forever. It marks discovery as pending, then runs a 30 second automatic search only after Headunit Revived signals Android Auto projection or the first navigation update. During that search, Android sends a discovery probe immediately and retries once per second until ESP32 responds or the timeout expires. The manual `Find ESP32 on Wi-Fi` button still runs a 12 second search at any time.

The foreground bridge service also runs its own recovery loop while Android Auto is active. It starts an 8 second ESP32 discovery attempt only when no ESP32 target is known. If discovery fails, it retries with backoff from 10 seconds up to 60 seconds while Headunit is online and ESP32 is still not connected. When ESP32 is found, the service stores the target, sends current ESP32 settings, and replays the latest active HUD state if one exists.

The service does not keep a broadcast fallback after discovery because duplicate UDP paths can let delayed old packets redraw stale HUD values. The intended setup path is still BLE first, Wi-Fi UDP second.

ESP32 also retries its own Wi-Fi connection. If the hotspot is unavailable at boot or the connection drops later, firmware retries the stored SSID with backoff from 5 seconds up to 60 seconds. After reconnect, it restarts the HUD UDP and discovery listeners.

If a phone hotspot blocks client-to-client traffic, the ESP32 can join the hotspot and show a private IP, but the tablet may still fail to discover it or send UDP packets to it. In that case the network path must change, for example ESP32 AP mode, USB tethering, or a separate travel router.
