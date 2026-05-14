# Headunit Revived ESP32 HUD Project

## Project Goal

Build a separate companion system for Headunit Revived that forwards Android Auto navigation guidance from an Android tablet to an ESP32-based HUD.

Headunit Revived itself is treated as an upstream dependency. Do not modify or fork Headunit Revived for this project unless the user explicitly asks for that. The Android app in this repository receives Headunit Revived navigation broadcasts and bridges them to ESP32 over the local network.

## Runtime Assumptions

- The tablet runs the GitHub build of Headunit Revived from `C:\Users\Zoe_Lowell\Documents\GitHub\headunit-revived`.
- The active Headunit Revived build emits `com.andrerinas.headunitrevived.NAVIGATION_UPDATE` broadcasts without signature-only receiver restrictions.
- The phone provides a Wi-Fi hotspot/tethering network.
- The tablet and ESP32 both ultimately connect to that phone hotspot.
- ESP32 first exposes a BLE provisioning service named `Headunit HUD`.
- The Android bridge app sends the hotspot SSID/password to ESP32 over BLE.
- After ESP32 joins Wi-Fi, it sends a compact BLE status notification, advertises itself on UDP discovery port `4211`, and receives HUD UDP packets from the tablet on port `4210`.
- Android should automatically start UDP discovery after BLE credential write or connected status, because BLE status notifications may be compact and may not contain the ESP32 IP address.
- The Android foreground bridge service should keep recovering without the setup screen: retry ESP32 discovery with bounded backoff after failures, but do not delay HUD sends on ESP32 ACKs.
- ESP32 should retry stored Wi-Fi credentials with bounded backoff after boot-time connection failure or later Wi-Fi loss, then restart UDP listeners after reconnect.
- Some phone hotspots isolate clients even when both clients have private hotspot IP addresses. In that case BLE provisioning can succeed but Wi-Fi discovery and HUD UDP packets can still fail.

## Repository Layout

- `android-app/`: Kotlin Android bridge app.
  - Receives Headunit Revived navigation broadcasts.
  - Provisions ESP32 over BLE with hotspot Wi-Fi credentials.
  - Discovers a provisioned ESP32 on the hotspot using UDP discovery.
  - Retries ESP32 discovery from the foreground service while Android Auto is active.
  - Requests Android battery-optimization exemption and keeps the setup screen awake while visible.
  - Converts broadcast extras into stable HUD packet data.
  - Sends UDP packets to the provisioned ESP32 IP, using broadcast only while no ESP32 IP is known.
  - Sends ESP32 settings packets for OLED debug-overlay visibility, speed-unit visibility, and speed font size.
- `esp32-hud/`: PlatformIO ESP32-S3 firmware.
  - Targets an ESP32-S3-N16R8 style board through the `esp32-s3-n16r8` PlatformIO environment.
  - Advertises the BLE provisioning service.
  - Stores received Wi-Fi credentials in ESP32 NVS.
  - Connects to Wi-Fi in STA mode.
  - Retries stored Wi-Fi credentials with bounded backoff when the hotspot is unavailable or disconnects.
  - Responds to UDP discovery probes and periodically broadcasts discovery hello packets.
  - Listens for UDP HUD packets.
  - Accepts UDP settings packets to hide/show OLED debug header and footer.
  - Renders navigation state on a 128x64 I2C OLED and also prints parsed state over serial.
- `docs/`: Protocol notes, setup instructions, and verification steps.

## Headunit Broadcast Contract

The Android bridge app listens for:

- Action: `com.andrerinas.headunitrevived.NAVIGATION_UPDATE`

Important extras:

- `distance_meters`: distance to next maneuver, meters, `-1` if unknown.
- `time_seconds`: time to next maneuver, seconds, `-1` if unknown.
- `total_distance_meters`: remaining route distance to destination, meters, `-1` if unknown.
- `total_time_seconds`: remaining route time to destination, seconds, `-1` if unknown.
- `estimated_arrival`: destination ETA text, empty if unknown.
- `road`: road or target street text.
- `next_event_type`: Headunit Revived legacy next-turn event.
- `action_text`: localized Headunit Revived action text.
- `turn_side`: `1 = LEFT`, `2 = RIGHT`, `3 = UNSPECIFIED`.
- `turn_number`: roundabout/exit number, `-1` if unknown.
- `turn_angle`: turn angle, `-1` if unknown.
- `cluster_age_ms`: age of the latest cluster status snapshot, `-1` if unknown.
- `turn_detail_age_ms`: age of the latest turn-detail snapshot, `-1` if unknown.
- `turn_distance_age_ms`: age of the latest turn-distance snapshot, `-1` if unknown.

Every Android-to-ESP32 UDP payload includes a monotonic `seq` field. ESP32 must ignore a sequenced packet when `seq` is less than or equal to the last accepted sequence so delayed UDP packets cannot redraw stale HUD values.

The bridge must not rely only on `action_text` for direction. Korean strings such as `회전` can omit left/right direction, so direction must be derived from `turn_side` and event fields.

## BLE Provisioning Contract

The ESP32 advertises:

- Device name: `Headunit HUD`
- Service UUID: `3f2d8a62-8b0f-4c0d-9d2b-7b71d831e001`
- Wi-Fi credential write UUID: `3f2d8a62-8b0f-4c0d-9d2b-7b71d831e002`
- Status notify/read UUID: `3f2d8a62-8b0f-4c0d-9d2b-7b71d831e003`

Credential writes are UTF-8 JSON:

```json
{"ssid":"PhoneHotspot","password":"hotspot-password","udp_port":4210}
```

Status notifications are UTF-8 JSON:

```json
{"s":"c"}
```

The bridge still accepts older verbose status JSON, but the firmware should prefer compact status JSON so BLE notifications do not get truncated by small MTU links.

## HUD Packet Contract

Default transport is UDP to port `4210`.

ESP32 does not ACK HUD UDP packets. Android sends HUD packets fire-and-forget so stale return traffic cannot delay current navigation guidance.

Android retransmits the latest speed packet once per second. Location callbacks may arrive faster or slower than that depending on Android/GPS behavior.

Android may include `road_bitmap_width`, `road_bitmap_height`, and `road_bitmap_hex` so ESP32 can draw arbitrary Hangul road names without bundling a full Korean font.

The initial wire format is one compact UTF-8 JSON object per packet:

```json
{"distance_meters":300,"time_seconds":25,"road":"강남대로","road_bitmap_width":76,"road_bitmap_height":16,"road_bitmap_hex":"...","event_type":4,"turn_side":2,"instruction":"300m 후 우회전"}
```

Keep the packet backward compatible when adding fields. ESP32 firmware should ignore unknown fields.

## ESP32 Settings Packet Contract

Settings use the same HUD UDP port `4210`.

```json
{"type":"settings","debug_overlay":false,"speed_unit_visible":true,"speed_font_size":4,"language":"ko"}
```

When `debug_overlay` is `false`, ESP32 hides the OLED top `NAV/IP` header and bottom road/debug line and expands the main maneuver layout. `speed_font_size` is clamped to `2..6`. `language` accepts `ko` or `en` and controls fixed ESP32 OLED HUD labels; Android uses the same saved value for the app UI. These settings are stored in ESP32 NVS.

## ESP32 Discovery Contract

Discovery uses UDP port `4211`.

Android sends this probe:

```json
{"type":"headunit_hud_discover"}
```

ESP32 responds directly to the probe sender and periodically broadcasts this hello:

```json
{"type":"headunit_hud_hello","name":"Headunit HUD","ip":"192.168.43.23","udp_port":4210}
```

Android must prefer the UDP packet source address over the JSON `ip` field because the source address is the routable address observed by the tablet.

## Engineering Rules

- Keep Headunit Revived integration isolated behind constants and parsing helpers.
- Prefer simple, testable pure Kotlin for packet formatting and maneuver mapping.
- Keep Android service/network code separate from packet formatting.
- Do not commit Wi-Fi SSIDs, passwords, IP addresses, signing keys, or local Android SDK paths.
- Keep ESP32 display-driver code behind a small function boundary so the transport path can be tested with serial output first.
- Current OLED layout is physical `[1] [2]`: display 1 speed/safety on GPIO 8/9 at `0x3C`, and display 2 navigation on GPIO 10/11 at `0x3C`; keep these overrideable through `config.h`.
- Keep BLE UUIDs, discovery constants, settings fields, and packet fields synchronized between `BleProvisioningContract.kt`, `Esp32DiscoveryPacket.kt`, `Esp32SettingsPacket.kt`, `ProvisioningStore.kt`, `esp32-hud/src/main.cpp`, and `docs/protocol.md`.
- Update `docs/protocol.md` when the UDP schema changes.
- Use Korean user-facing wording where appropriate, but keep code identifiers and protocol fields in English.

## Verification

Preferred checks:

- Android unit tests: `gradle :android-app:testDebugUnitTest`
- Android lint/build, once SDK dependencies are available: `gradle :android-app:assembleDebug`
- ESP32 compile, once PlatformIO is installed: `platformio run -d esp32-hud -e esp32-s3-n16r8`

If a tool is missing locally, state that clearly and verify the parts that can run.
