# HUD Protocol

## Source Broadcast

The Android app receives Headunit Revived navigation updates:

- Action: `com.andrerinas.headunitrevived.NAVIGATION_UPDATE`
- Receiver mode: runtime `registerReceiver` with `Context.RECEIVER_EXPORTED` on Android 13+

Expected extras:

| Extra | Type | Meaning |
| --- | --- | --- |
| `distance_meters` | int | Distance to next maneuver, meters, or `-1` |
| `time_seconds` | int | Time to next maneuver, seconds, or `-1` |
| `total_distance_meters` | int | Remaining route distance to destination, meters, or `-1` |
| `total_time_seconds` | long | Remaining route time to destination, seconds, or `-1` |
| `estimated_arrival` | string | Destination ETA text from Headunit Revived, if available |
| `road` | string | Current or target road |
| `next_event_type` | int | Headunit Revived legacy next-turn event |
| `action_text` | string | Human-readable maneuver text |
| `turn_side` | int | `1=LEFT`, `2=RIGHT`, `3=UNSPECIFIED` |
| `turn_number` | int | Roundabout/exit number, or `-1` |
| `turn_angle` | int | Turn angle, or `-1` |
| `cluster_age_ms` | long | Age of the latest cluster status snapshot, or `-1` |
| `turn_detail_age_ms` | long | Age of the latest turn-detail snapshot, or `-1` |
| `turn_distance_age_ms` | long | Age of the latest turn-distance snapshot, or `-1` |

## Android Bridge Status

The Android foreground service also publishes an internal app-only status broadcast so the setup screen can show categorized state.

| Extra | Type | Meaning |
| --- | --- | --- |
| `headunit_state` | string | `WAITING_FOR_BROADCAST`, `PROJECTION_ACTIVE`, or `NAVIGATION_ACTIVE` |
| `hud_output_state` | string | `NONE`, `NAVIGATION_GUIDANCE`, or `NAVIGATION_INACTIVE` |
| `esp_connection_state` | string | `DISCONNECTED`, `DISCOVERING`, `RETRY_WAITING`, or `CONNECTED` |
| `last_event` | string | Last bridge event key shown in the app log |
| `last_event_time_millis` | long | Wall-clock time of that event |
| `next_esp_discovery_retry_at_millis` | long | Wall-clock time for the next automatic ESP32 discovery attempt, or `0` |

## UDP Packet

The bridge sends one JSON object per UDP datagram to port `4210`.
When an ESP32 target IP is known, the payload is sent only to that saved IP.
When no ESP32 target is known, the payload is sent to `255.255.255.255:4210`.
Each payload includes a monotonic `seq` field; ESP32 ignores sequenced packets
whose `seq` is less than or equal to the last accepted packet so delayed UDP
packets cannot redraw stale HUD values.

```json
{"seq":123456,"distance_meters":300,"time_seconds":25,"road":"강남대로","road_bitmap_width":76,"road_bitmap_height":16,"road_bitmap_hex":"...","event_type":4,"turn_side":2,"turn_number":-1,"turn_angle":-1,"active":true,"instruction":"300m 후 우회전"}
```

Fields are additive. ESP32 firmware must ignore unknown fields.

`road_bitmap_width`, `road_bitmap_height`, and `road_bitmap_hex` are optional. The Android bridge renders the selected road text into a compact 1-bit monochrome bitmap so ESP32 can display arbitrary Hangul road names without carrying a full Korean font. `road_bitmap_hex` is row-major packed bits, most-significant bit first in each byte.

When `active=false`, ESP32 clears the navigation faces instead of showing placeholder content such as `--` or `안내`.

The bridge clears active guidance only on an explicit inactive packet or bridge service shutdown. It does not send a waiting/placeholder state when Android Auto is active without route guidance.

ESP32 does not reply with an ACK. Android sends each UDP payload fire-and-forget and keeps the UI state based on local send success.

## Direction Rule

Do not infer direction from localized `action_text`. Use `turn_side`:

- `1`: left
- `2`: right
- `3`: unspecified

For example, `next_event_type=4` and `turn_side=2` becomes `우회전`.

## BLE Provisioning

ESP32 advertises a BLE GATT service before Wi-Fi is available.

| Item | Value |
| --- | --- |
| Device name | `Headunit HUD` |
| Service UUID | `3f2d8a62-8b0f-4c0d-9d2b-7b71d831e001` |
| Wi-Fi credential characteristic | `3f2d8a62-8b0f-4c0d-9d2b-7b71d831e002` |
| Status characteristic | `3f2d8a62-8b0f-4c0d-9d2b-7b71d831e003` |
| CCC descriptor | `00002902-0000-1000-8000-00805f9b34fb` |

The Android app writes Wi-Fi credentials as UTF-8 JSON:

```json
{"ssid":"PhoneHotspot","password":"hotspot-password","udp_port":4210}
```

The ESP32 status characteristic supports read/notify and sends compact UTF-8 JSON. Connected status must include `i` so Android can store the ESP32 target IP without depending on UDP discovery:

```json
{"s":"c","i":"10.233.116.145"}
```

Known states:

| State | Meaning |
| --- | --- |
| `idle` | BLE is ready or connected, but Wi-Fi is not being changed. |
| `connecting` | ESP32 received credentials and is joining Wi-Fi. |
| `connected` | ESP32 joined Wi-Fi and `ip` contains the UDP target host. |
| `failed` | ESP32 rejected credentials or Wi-Fi connection timed out. |

Compact aliases:

| Alias | State |
| --- | --- |
| `i` | `idle` |
| `g` | `connecting` |
| `c` | `connected` |
| `f` | `failed` |

The Android app accepts both compact JSON and the older verbose JSON. Firmware should prefer compact JSON because default BLE notification MTU can truncate verbose status payloads. If Android receives a connected status without `i`, it performs one explicit status characteristic read, then falls back to UDP discovery if the IP is still missing.

## Wi-Fi Discovery

Discovery uses UDP port `4211`. It exists for the case where BLE provisioning succeeded but the Android app needs to refresh or recover the ESP32 target address.

Android sends this UTF-8 JSON probe to discovery targets and listens on local UDP port `4211`:

```json
{"type":"headunit_hud_discover"}
```

Discovery targets are:

- `255.255.255.255:4211`
- the tablet subnet broadcast address when Android exposes DHCP netmask data
- the saved ESP32 target IP on port `4211`, if one exists

ESP32 responds to the probe sender and also broadcasts a hello every few seconds:

```json
{"type":"headunit_hud_hello","name":"Headunit HUD","ip":"192.168.43.23","udp_port":4210}
```

Android stores the UDP packet source address first, not the JSON `ip` field. The JSON IP is kept for fallback and debugging only.

Automatic discovery is gated by Android Auto activity. BLE provisioning marks discovery as pending, but Android does not begin the 30 second automatic Wi-Fi search until it receives Headunit Revived's projection request broadcast or the first navigation update broadcast. Manual discovery remains available from the app UI and uses a 12 second search window. While a search is active, the Android app sends the first probe immediately and retries once per second.

The foreground bridge service has a second recovery path that is independent of the setup screen. Once Android Auto projection or navigation is observed, the service sends HUD packets to the saved target when known, or to broadcast when no ESP32 target is known. It runs 8 second discovery attempts only when no ESP32 target is known. Failed attempts are retried with exponential backoff from 10 seconds up to 60 seconds while Headunit is online and ESP32 is not connected. A successful discovery resets the backoff, stores the target host, sends the current ESP32 settings packet, and replays the latest active HUD state if one exists.

If both devices are on the same phone hotspot but no hello reaches Android, the hotspot is probably blocking client-to-client traffic. BLE provisioning may still work in that state because BLE does not prove that Wi-Fi peer traffic is allowed.

## Wi-Fi Reconnect

ESP32 stores the latest accepted SSID/password/UDP port in NVS. On boot, it attempts that network once immediately. If connection fails, or if an established Wi-Fi connection drops later, firmware retries with exponential backoff from 5 seconds up to 60 seconds.

On reconnect, ESP32 restarts both the HUD UDP listener on `4210` and the discovery listener on `4211`, then emits a connected BLE status. Android keeps sending live navigation and speed packets over UDP after the network path returns.

## ESP32 Settings

Android sends settings packets to the HUD UDP port `4210`.

```json
{"type":"settings","debug_overlay":false,"speed_unit_visible":true,"speed_font_size":4,"language":"ko"}
```

`debug_overlay=false` hides the OLED top `NAV/IP` header and bottom road/debug line. `speed_unit_visible=false` hides the `km/h` label. `speed_font_size` accepts OLED text sizes `2` through `6`; firmware clamps unsupported values and stores the result in NVS.

`language` controls fixed ESP32 OLED HUD labels and accepts `ko` or `en`. Android also uses the same saved setting for the bridge app UI. The default is `ko`; unknown or missing language values keep/fall back to Korean-compatible behavior so older Android builds and firmware remain compatible.

## Speed Packet

Android stores the latest tablet GPS speed packet and retransmits it once per second:

```json
{"type":"speed","speed_kmh":42}
```

If Android has no current speed value, it sends `speed_kmh=0` so the HUD shows a stationary speed instead of `--`. The Android location listener requests updates every 500 ms, but Android does not guarantee a callback at that exact interval, especially while stationary. The 1 second speed replay is what keeps the HUD speed face refreshed.

## Dual OLED Layout

The current firmware uses physical layout `[1] [2]`.

| Display | Role | Content |
| --- | --- | --- |
| 1 | Speed | GPS speed |
| 2 | Navigation | Maneuver icon, distance, selected road name |

OLED 1 stays on the first ESP32-S3 I2C bus at `0x78` / `0x3C`. OLED 2 remains on the second I2C bus at `0x78` / `0x3C`.

Direction icons are selected from numeric fields such as `event_type` and `turn_side`, not from localized `instruction`. The visible text under the distance is the selected road name, preferably rendered through the Android-generated road bitmap.
