# Headunit Revived HUD Project

## Project Goal

Build a companion HUD system for Headunit Revived without forking Headunit Revived.

The current primary target is a Raspberry Pi 4B driving a 1920x480 HDMI auxiliary display. The Pi must be able to run standalone: it reads vehicle data locally through iCar/ELM327 OBD and CANable/SocketCAN, renders the HUD locally, and treats the Android bridge as an optional navigation input only. When the Android bridge is on the same network, it sends Headunit Revived navigation plus tablet/GPS backup speed to the Pi.

The older ESP32 OLED HUD path remains in the repository and should continue to work unless the user explicitly asks to remove or replace it.

## Runtime Assumptions

- The tablet runs the GitHub build of Headunit Revived from `C:\Users\Zoe_Lowell\Documents\GitHub\headunit-revived`.
- The active Headunit Revived build emits `com.andrerinas.headunitrevived.NAVIGATION_UPDATE` broadcasts without signature-only receiver restrictions.
- Raspberry Pi 4B is the main 1920x480 HUD computer.
- Pi local vehicle input is iCar/ELM327 for standard OBD PIDs and CANable with candleLight/SocketCAN for raw CAN.
- Android bridge is optional for the Pi path. If Android is absent or unreachable, the Pi HUD still renders local vehicle data and marks navigation stale/disconnected.
- Android bridge packets to a Pi target must be limited to navigation and `type=speed` backup speed. ESP32-only settings packets must not be sent to Pi targets.
- Phone hotspot/tethering may be used as the shared network for Android and Pi. Some hotspots isolate clients; in that case Pi local vehicle data still works but Android navigation UDP may not reach the Pi.
- ESP32 still uses BLE provisioning, UDP discovery, UDP HUD packets, and OLED rendering for the legacy compact HUD path.

## Repository Layout

- `android-app/`: Kotlin Android bridge app.
  - Receives Headunit Revived navigation broadcasts.
  - Sends navigation packets and tablet/GPS backup speed over UDP.
  - Discovers ESP32 and Raspberry Pi HUD targets using UDP discovery.
  - Stores target kind so Pi targets do not receive ESP32 settings packets.
  - Keeps ESP32 BLE provisioning/settings support for the legacy OLED path.
- `bridge-core/`: Pure Kotlin packet, timing, state, and discovery contract code with unit tests.
- `pi-hud/`: Raspberry Pi 1920x480 pygame HUD runtime.
  - Loads the same layout JSON that the Windows editor saves.
  - Reads OBD via ELM327/iCar serial or rfcomm.
  - Reads CAN via CANable/SocketCAN.
  - Responds to Android bridge discovery with `device_kind=pi_hud`.
  - Receives Android navigation and backup speed on UDP port `4210`.
  - Ignores stale sequenced UDP packets.
- `layout-editor-electron/`: primary Windows Electron layout editor.
  - Shows the actual Pi `HudRenderer` output in the central preview through the Python bridge.
  - Keeps JSON, snapshot export, validation, and field-pack export compatible with the Pi runtime.
- `layouts/`: Shared 1920x480 HUD layout JSON files.
- `vehicles/`: Vehicle profile JSON files for future vehicle expansion.
- `esp32-hud/`: PlatformIO ESP32-S3 firmware for the legacy dual-OLED HUD.
- `docs/`: Protocol notes, setup guides, Pi runtime guide, vehicle research, and verification steps.

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

Every Android-to-HUD UDP payload includes a monotonic `seq` field. ESP32 and Raspberry Pi HUD receivers ignore sequenced packets when `seq` is less than or equal to the last accepted sequence so delayed UDP packets cannot redraw stale HUD values.

The bridge must not rely only on `action_text` for direction. Korean strings such as `회전` can omit left/right direction, so direction must be derived from `turn_side` and event fields.

## UDP HUD Packet Contract

Default transport is UDP to port `4210`.

Android sends HUD packets fire-and-forget. HUD receivers do not ACK live packets, so stale return traffic cannot delay current navigation guidance.

Android retransmits the latest tablet/GPS speed packet once per second. On Raspberry Pi targets this is backup speed only; local OBD/CAN remains the primary vehicle source.

The wire format is one compact UTF-8 JSON object per packet:

```json
{"seq":123456,"distance_meters":300,"time_seconds":25,"road":"강남대로","event_type":4,"turn_side":2,"instruction":"300m 후 우회전"}
```

Keep packets backward compatible when adding fields. Receivers should ignore unknown fields.

## Discovery Contract

Discovery uses UDP port `4211`.

Android sends this probe:

```json
{"type":"headunit_hud_discover"}
```

ESP32 responds with the legacy hello:

```json
{"type":"headunit_hud_hello","name":"Headunit HUD","ip":"192.168.43.23","udp_port":4210}
```

Raspberry Pi responds with the same hello type and identifies itself as a Pi HUD:

```json
{"type":"headunit_hud_hello","name":"Headunit Pi HUD","ip":"192.168.43.20","udp_port":4210,"device_kind":"pi_hud"}
```

Android must prefer the UDP packet source address over the JSON `ip` field because the source address is the routable address observed by the tablet. Missing `device_kind` means legacy ESP32 target. `device_kind=pi_hud` means Android stores a Pi target and sends navigation plus backup speed only.

## ESP32 Provisioning And Settings

The ESP32 advertises:

- Device name: `Headunit HUD`
- Service UUID: `3f2d8a62-8b0f-4c0d-9d2b-7b71d831e001`
- Wi-Fi credential write UUID: `3f2d8a62-8b0f-4c0d-9d2b-7b71d831e002`
- Status notify/read UUID: `3f2d8a62-8b0f-4c0d-9d2b-7b71d831e003`

Credential writes are UTF-8 JSON:

```json
{"ssid":"PhoneHotspot","password":"hotspot-password","udp_port":4210}
```

ESP32 settings use the same HUD UDP port `4210` and must only be sent to ESP32 targets:

```json
{"type":"settings","debug_overlay":false,"speed_unit_visible":true,"speed_font_size":4,"language":"ko"}
```

Raspberry Pi HUD targets manage layout/settings locally through JSON layout files and the Electron Windows editor.

## Engineering Rules

- Keep Headunit Revived integration isolated behind constants and parsing helpers.
- Prefer simple, testable pure Kotlin for Android packet formatting and maneuver mapping.
- Keep Android service/network code separate from packet formatting.
- Keep Pi runtime data sources (`OBD`, `CAN`, `bridge`, `dummy`) separated so each can be tested independently.
- Keep layout JSON as the shared contract between `layout-editor-electron/` and `pi-hud/`; renderer-visible changes need tests or layout verification.
- Keep vehicle-specific confirmed facts in `vehicles/*.json`, default layout `vehicles`, and vehicle docs synchronized.
- Android must not send ESP32 settings packets to Pi targets.
- Do not commit Wi-Fi SSIDs, passwords, IP addresses, signing keys, local Android SDK paths, generated baseline captures, or device-specific private data.
- Keep ESP32 display-driver code behind a small function boundary so the transport path can be tested with serial output first.
- Keep BLE UUIDs, discovery constants, settings fields, and packet fields synchronized between Kotlin code, Pi discovery/runtime code, ESP32 firmware where applicable, and `docs/protocol.md`.
- Update `docs/protocol.md` and `docs/protocol.ko.md` when the UDP schema changes.
- Use Korean user-facing wording where appropriate, but keep code identifiers and protocol fields in English.

## Verification

Preferred checks:

- Pi runtime tests on Windows from repo root: `$env:PYTHONPATH=(Resolve-Path 'pi-hud').Path; .\pi-hud\.venv\Scripts\python.exe -m unittest discover -s pi-hud\tests`.
- Electron layout editor checks from `layout-editor-electron/`: `npm test`, `npm audit --audit-level=high`, `npm run build`.
- Pi/Linux runtime tests from `pi-hud/`: `.venv/bin/python -m unittest discover -s tests`.
- Layout render check: `python pi-hud/scripts/verify-layout.py layouts/avante_hd_2010_default.json --width 1920 --height 480 --output <png>`.
- Android unit tests: `gradle :bridge-core:test :android-app:testDebugUnitTest`.
- Android build: `gradle :android-app:assembleDebug`.
- ESP32 compile, once PlatformIO is installed: `platformio run -d esp32-hud -e esp32-s3-n16r8`.

If a tool is missing locally, state that clearly and verify the parts that can run.
