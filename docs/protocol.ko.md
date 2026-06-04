# Protocol Reference

[English](protocol.md) | [한국어](protocol.ko.md) | [프로젝트 README](../README.ko.md)

이 문서는 Headunit Revived, Android bridge app, ESP32 HUD firmware, Raspberry Pi HUD runtime 사이의 현재 wire contract를 설명합니다.

Protocol은 작고 additive하게 유지합니다. 새 JSON field는 시간이 지나며 추가될 수 있고, receiver는 알 수 없는 field를 무시해야 합니다.

## Compatibility Rules

- 공개된 field name은 안정적으로 유지합니다.
- rename/remove 대신 field를 추가합니다.
- optional field가 없으면 unknown value로 처리합니다.
- 알 수 없는 JSON field는 additive field로 보고 무시하지만, 알 수 없는 `type` 값을 navigation packet으로 취급하지 않습니다.
- HUD behavior는 numeric state field를 우선 사용하고, localized string은 display text로만 사용합니다.
- `docs/protocol.md`, Android packet code, ESP32 packet parsing을 함께 동기화합니다.

## Source Broadcast

Android app은 Headunit Revived navigation update를 수신합니다.

- Action: `com.andrerinas.headunitrevived.NAVIGATION_UPDATE`
- Receiver mode: Android 13+에서 runtime `registerReceiver` + `Context.RECEIVER_EXPORTED`

Expected extras:

| Extra | Type | Meaning |
| --- | --- | --- |
| `distance_meters` | int | 다음 maneuver까지 거리, meter, 또는 `-1` |
| `time_seconds` | int | 다음 maneuver까지 시간, second, 또는 `-1` |
| `total_distance_meters` | int | destination까지 남은 route distance, meter, 또는 `-1` |
| `total_time_seconds` | long | destination까지 남은 route time, second, 또는 `-1` |
| `estimated_arrival` | string | Headunit Revived의 destination ETA text |
| `road` | string | 현재 또는 target road |
| `next_event_type` | int | Headunit Revived legacy next-turn event |
| `action_text` | string | Human-readable maneuver text |
| `turn_side` | int | `1=LEFT`, `2=RIGHT`, `3=UNSPECIFIED` |
| `turn_number` | int | Roundabout/exit number, 또는 `-1` |
| `turn_angle` | int | Turn angle, 또는 `-1` |
| `cluster_age_ms` | long | 최신 cluster status snapshot age, 또는 `-1` |
| `turn_detail_age_ms` | long | 최신 turn-detail snapshot age, 또는 `-1` |
| `turn_distance_age_ms` | long | 최신 turn-distance snapshot age, 또는 `-1` |

## Direction Rule

Localized `action_text`에서 방향을 추론하지 마세요. `turn_side`와 event field를 사용합니다.

| Value | Meaning |
| --- | --- |
| `1` | left |
| `2` | right |
| `3` | unspecified |

예를 들어 `next_event_type=4`, `turn_side=2`는 localized text가 불완전해도 right-turn HUD state로 매핑합니다.

## Android Bridge Status

Android foreground service는 setup screen이 categorized state를 표시할 수 있도록 internal app-only status broadcast를 발행합니다.

| Extra | Type | Meaning |
| --- | --- | --- |
| `headunit_state` | string | `WAITING_FOR_BROADCAST`, `PROJECTION_ACTIVE`, 또는 `NAVIGATION_ACTIVE` |
| `hud_output_state` | string | `NONE`, `NAVIGATION_GUIDANCE`, 또는 `NAVIGATION_INACTIVE` |
| `esp_connection_state` | string | `DISCONNECTED`, `DISCOVERING`, `RETRY_WAITING`, 또는 `CONNECTED` |
| `last_event` | string | App log에 표시되는 마지막 bridge event key |
| `last_event_time_millis` | long | 해당 event의 wall-clock time |
| `next_esp_discovery_retry_at_millis` | long | 다음 automatic ESP32 discovery attempt wall-clock time, 또는 `0` |

## UDP HUD Packet

Bridge는 UDP datagram 하나당 JSON object 하나를 port `4210`으로 보냅니다.

ESP32 target IP를 알고 있으면 Android는 저장된 IP로만 보냅니다. Target을 모르면 `255.255.255.255:4210`으로 보냅니다.

각 payload에는 monotonic `seq` field가 포함됩니다. ESP32와 Raspberry Pi HUD receiver는 `seq`가 마지막으로 accepted packet 이하인 sequenced packet을 무시해서 delayed UDP packet이 stale HUD 값을 다시 그리지 못하게 합니다.

Example:

```json
{"seq":123456,"distance_meters":300,"time_seconds":25,"road":"강남대로","road_bitmap_width":76,"road_bitmap_height":16,"road_bitmap_hex":"...","event_type":4,"turn_side":2,"turn_number":-1,"turn_angle":-1,"active":true,"instruction":"우회전"}
```

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `seq` | long | yes | Monotonic packet sequence |
| `distance_meters` | int | yes | 다음 maneuver까지 거리, 또는 `-1` |
| `time_seconds` | int | yes | 다음 maneuver까지 시간, 또는 `-1` |
| `road` | string | yes | Selected road 또는 fallback maneuver label |
| `event_type` | int | yes | Headunit navigation event |
| `turn_side` | int | yes | Numeric turn side |
| `turn_number` | int | yes | Roundabout/exit number, 또는 `-1` |
| `turn_angle` | int | yes | Turn angle, 또는 `-1` |
| `active` | bool | yes | Active route guidance 여부 |
| `instruction` | string | no | App/debug surface용 human-readable maneuver text. 거리 값은 중복 표시를 막기 위해 `distance_meters`에만 둡니다. |
| `road_bitmap_width` | int | no | Android-generated road bitmap width |
| `road_bitmap_height` | int | no | Android-generated road bitmap height |
| `road_bitmap_hex` | string | no | Row-major packed 1-bit bitmap data |
| `icon_bitmap_width` | int | no | Android-generated icon bitmap width |
| `icon_bitmap_height` | int | no | Android-generated icon bitmap height |
| `icon_bitmap_hex` | string | no | Row-major packed 1-bit icon bitmap data |

`active=false`이면 ESP32는 `--`나 `안내` 같은 placeholder 대신 navigation face를 clear합니다. Raspberry Pi HUD runtime은 이 packet을 `nav.connected=false`로 반영하고 road/instruction text를 비우며 numeric guidance field를 `--`로 바꿔서 이전 경로 안내가 화면에 남지 않게 합니다.

Bridge는 explicit inactive packet 또는 bridge service shutdown에서만 active guidance를 clear합니다. Android Auto가 active이지만 route guidance가 없는 상태에서는 waiting placeholder를 보내지 않습니다.

ESP32는 HUD UDP packet에 ACK하지 않습니다. Android는 live payload를 fire-and-forget으로 보내고 local send success 기준으로 UI state를 유지합니다.

## BLE Provisioning

ESP32는 Wi-Fi 사용 가능 전 BLE GATT service를 advertise합니다.

| Item | Value |
| --- | --- |
| Device name | `Headunit HUD` |
| Service UUID | `3f2d8a62-8b0f-4c0d-9d2b-7b71d831e001` |
| Wi-Fi credential characteristic | `3f2d8a62-8b0f-4c0d-9d2b-7b71d831e002` |
| Status characteristic | `3f2d8a62-8b0f-4c0d-9d2b-7b71d831e003` |
| CCC descriptor | `00002902-0000-1000-8000-00805f9b34fb` |

Android는 Wi-Fi credentials를 UTF-8 JSON으로 씁니다.

```json
{"ssid":"PhoneHotspot","password":"hotspot-password","udp_port":4210}
```

ESP32 status는 read/notify를 지원하고 compact UTF-8 JSON을 보냅니다. Connected status는 Android가 UDP discovery에 의존하지 않고 ESP32 target IP를 저장할 수 있도록 `i`를 포함해야 합니다.

```json
{"s":"c","i":"10.233.116.145"}
```

Known states:

| State | Alias | Meaning |
| --- | --- | --- |
| `idle` | `i` | BLE ready 또는 connected 상태이며 Wi-Fi 변경 중이 아님 |
| `connecting` | `g` | ESP32가 credentials를 받고 Wi-Fi join 중 |
| `connected` | `c` | ESP32가 Wi-Fi에 join했고 `ip`/`i`에 UDP target host가 있음 |
| `failed` | `f` | ESP32가 credentials를 거부했거나 Wi-Fi connection timeout |

Android app은 compact JSON과 older verbose JSON을 모두 받습니다. Firmware는 default BLE notification MTU에서 verbose status payload가 잘릴 수 있으므로 compact JSON을 우선 사용해야 합니다. Android가 `i` 없는 connected status를 받으면 status characteristic을 한 번 read하고, IP가 여전히 없으면 UDP discovery로 fallback합니다.

## Wi-Fi Discovery

Discovery는 UDP port `4211`을 사용합니다. BLE provisioning은 성공했지만 Android가 HUD target address를 refresh/recover해야 하는 경우를 위한 경로입니다. Raspberry Pi HUD runtime도 같은 discovery contract에 응답하므로, 같은 네트워크에 있으면 Android가 ESP32 없이도 내비와 backup speed를 Pi로 보낼 수 있습니다.

Android가 보내는 UTF-8 JSON probe:

```json
{"type":"headunit_hud_discover"}
```

Discovery target:

- `255.255.255.255:4211`
- Android가 DHCP netmask data를 노출하는 경우 tablet subnet broadcast address
- 저장된 ESP32 target IP가 있으면 해당 IP의 port `4211`

ESP32는 probe sender에 응답하고 hello를 주기적으로 broadcast합니다.

```json
{"type":"headunit_hud_hello","name":"Headunit HUD","ip":"192.168.43.23","udp_port":4210}
```

Raspberry Pi HUD는 같은 hello type으로 응답하되 `device_kind=pi_hud`로 자신을 식별합니다.

```json
{"type":"headunit_hud_hello","name":"Headunit Pi HUD","ip":"192.168.43.20","udp_port":4210,"device_kind":"pi_hud"}
```

Android는 JSON `ip` field보다 UDP packet source address를 먼저 저장합니다. JSON IP는 fallback/debug data입니다.

`device_kind`가 없으면 Android는 legacy ESP32 HUD target으로 취급합니다. `device_kind=pi_hud`이거나 hello name이 Pi HUD임을 명확히 나타내면 Android는 target을 Pi HUD로 저장하고 ESP32 전용 settings packet을 보내지 않습니다. Navigation packet과 `type=speed` backup speed packet은 계속 보냅니다.

Automatic discovery는 Android Auto activity에 의해 gate됩니다. BLE provisioning은 discovery pending만 표시하고, Android는 Headunit Revived projection request broadcast 또는 첫 navigation update broadcast를 받은 뒤 30초 automatic Wi-Fi search를 시작합니다. Manual discovery는 app UI에서 항상 가능하며 12초 search window를 사용합니다. Search 중에는 첫 probe를 즉시 보내고 1초마다 retry합니다.

Foreground bridge service에는 setup screen과 독립적인 recovery path가 있습니다. Android Auto projection 또는 navigation이 관측되면 service는 saved target이 있을 때 그 target으로 HUD packet을 보내고, 없으면 broadcast로 보냅니다. Target이 없을 때만 8초 discovery attempt를 실행합니다. 실패한 attempt는 Headunit online이고 HUD target이 connected가 아닐 때 10초에서 60초까지 exponential backoff로 retry합니다. Discovery가 성공하면 backoff를 reset하고 target host를 저장하며, ESP32 target일 때만 current ESP32 settings packet을 보내고 최신 active HUD state를 다시 보냅니다.

## Wi-Fi Reconnect

ESP32는 마지막으로 accepted SSID/password/UDP port를 NVS에 저장합니다. Boot 시 해당 network를 한 번 즉시 시도합니다. Connection이 실패하거나 established Wi-Fi connection이 나중에 끊기면 firmware는 5초에서 60초까지 exponential backoff로 retry합니다.

Reconnect 시 ESP32는 HUD UDP listener `4210`과 discovery listener `4211`을 다시 시작하고 connected BLE status를 보냅니다. Android는 network path가 돌아오면 live navigation/speed packet을 UDP로 계속 보냅니다.

## ESP32 Settings Packet

Android는 ESP32 target에만 settings packet을 HUD UDP port `4210`으로 보냅니다. Raspberry Pi HUD target은 layout/settings를 로컬에서 관리하므로 navigation과 backup speed만 받아야 합니다.

```json
{"type":"settings","debug_overlay":false,"speed_unit_visible":true,"speed_font_size":4,"language":"ko"}
```

| Field | Type | Meaning |
| --- | --- | --- |
| `type` | string | 반드시 `settings` |
| `debug_overlay` | bool | OLED debug header/footer 표시 여부 |
| `speed_unit_visible` | bool | `km/h` label 표시 여부 |
| `speed_font_size` | int | OLED text size, `2..6`으로 clamp |
| `language` | string | Fixed HUD label과 Android UI에 사용할 `ko` 또는 `en` |

기본 language는 `ko`입니다. Unknown 또는 missing language value는 older Android build와 firmware compatibility를 위해 Korean-compatible behavior로 유지/fallback합니다.

## Speed Packet

Android는 최신 tablet GPS speed packet을 저장하고 1초마다 retransmit합니다.

```json
{"type":"speed","speed_kmh":42}
```

Android에 current speed value가 없으면 HUD가 `--` 대신 stationary speed를 표시하도록 `speed_kmh=0`을 보냅니다. Android는 500ms 간격 location update를 요청하지만 callback timing은 OS/GPS behavior에 따라 달라질 수 있습니다. 1초 speed replay가 HUD speed face refresh를 유지합니다.

Raspberry Pi HUD는 이 packet을 `vehicle.speed_kmh_backup`으로만 저장합니다. 로컬 OBD/CAN 값이 차량 주 데이터 source입니다.
Pi runtime은 navigation freshness와 backup speed freshness를 따로 추적하므로, Android speed packet이 계속 들어와도 오래된 길안내를 connected 상태로 유지하지 않습니다.

## Raspberry Pi Diagnostic Packets

실사용 Pi HUD 경로는 iCar/ELM327와 CANable/SocketCAN의 확정 mapping에서 차량 데이터를 로컬로 읽습니다. Raw OBD/CAN 조사와 live simulation은 layout/profile을 Pi에 배포하기 전에 Windows Electron 레이아웃 에디터에서 처리합니다. Android bridge는 navigation과 backup speed만 보내야 합니다.

Pi runtime은 remote `vehicle_status` packet을 의도적으로 무시합니다. 따라서 UDP traffic이 Pi 로컬 OBD/CAN 주 차량값을 대체할 수 없습니다. Android bridge target policy는 명시적으로 나뉩니다. ESP32 target은 navigation, backup speed, ESP32 settings packet을 받을 수 있지만 Raspberry Pi HUD target은 navigation과 `type=speed` backup-speed packet만 받을 수 있습니다. Android는 production HUD target으로 `vehicle_status`, `dtc_snapshot`, `vehicle_debug` packet을 보내면 안 됩니다.

Debug-only packet은 Pi runtime 기본값에서는 무시합니다. Layout debugging이나 legacy field diagnostics가 필요할 때만 Pi runtime을 `--allow-diagnostic-udp`로 실행하면 같은 UDP port `4210`에서 받을 수 있습니다. 지원되는 CAN/OBD 조사 경로는 Windows 에디터입니다.

DTC snapshot:

```json
{"type":"dtc_snapshot","seq":124,"stored":["P0133"],"pending":[],"permanent":[]}
```

Pi runtime은 이 값을 `dtc.stored`, `dtc.pending`, `dtc.permanent`에 반영하고 `dtc.count`는 stored plus pending count로 다시 계산합니다.

Vehicle debug:

```json
{"type":"vehicle_debug","seq":125,"can_frame_count":128,"last_can_id":"0x316","obd_request":"010C","obd_response":"7E8 04 41 0C 1A F8"}
```

이 field들은 모두 optional이며 `debug.*` 아래에 들어갑니다. Android navigation bridge용이 아니며, 지원되는 Windows CAN/OBD 분석 workflow를 대체하지 않는 layout debugging/legacy diagnostics 용도입니다.

## Dual OLED Layout

현재 firmware는 물리 배치 `[1] [2]`를 사용합니다.

| Display | Role | Content |
| --- | --- | --- |
| 1 | Speed | GPS speed |
| 2 | Navigation | Maneuver icon, distance, selected road name |

OLED 1은 첫 번째 ESP32-S3 I2C bus의 `0x78` / `0x3C`에 있고, OLED 2는 두 번째 I2C bus의 `0x78` / `0x3C`에 있습니다.

Direction icon은 localized `instruction`이 아니라 `event_type`, `turn_side` 같은 numeric field에서 선택합니다. Distance 아래에 표시되는 text는 selected road name이며, 가능하면 Android-generated road bitmap으로 렌더링합니다.

## Privacy and Security Notes

- 실제 Wi-Fi credentials를 commit하지 마세요.
- BLE provisioning payload는 trusted local setup을 전제로 합니다.
- UDP HUD packet은 public internet이 아니라 private local network용입니다.
- Phone hotspot은 client isolation을 적용할 수 있습니다. BLE provisioning 성공이 UDP reachability를 보장하지는 않습니다.
