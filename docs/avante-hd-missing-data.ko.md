# Avante HD Missing Data Audit

[프로젝트 README](../README.ko.md) | [OBD PID notes](avante-hd-obd-pids.ko.md) | [CAN research](avante-hd-can-research.ko.md) | [DTC notes](avante-hd-dtc-codes.ko.md)

이 문서는 2010 Avante HD 1.6 gasoline automatic HUD/OBD/CAN 자료를 검토한 뒤, 구현 전에 아직 부족한 정보를 정리한다.

## 현재 확정된 조건

| 항목 | 값 |
| --- | --- |
| 차량 | 2010 Avante HD 1.6 gasoline automatic |
| 유력 엔진 | Gamma 1.6 MPI `G4FC`, 실차 라벨/VIN으로 확인 필요 |
| 유력 변속기 | A4CF1, 실차 라벨/TCM 응답으로 확인 필요 |
| ABS | 있음 |
| ESC/TCS | 미확인 |
| TPMS | 없음 |
| 계기판 기어 표시 | `P/R/N/D/3/2/L` |
| 계기판 경고등 관찰 | door open, battery/charging, parking brake/brake, ABS, SRS airbag, oil pressure, check engine, EPS, coolant temperature |
| DLC populated pins | `16`, `15`, `14`, `12`, `8`, `6`, `5`, `4`, `3` |

## 구현을 막는 부족한 정보

| 우선순위 | 부족한 정보 | 왜 필요한가 | 확보 방법 |
| --- | --- | --- | --- |
| P0 | OBD supported PID bitmap | 표준 PID 중 실제 지원 항목만 polling해야 함 | iCar Pro 2S로 `0100`, `0120`, `0140`, 가능하면 `0160` 기록 |
| P0 | ELM327 protocol/adapter 상태 | iCar Pro 2S가 차량에서 CAN/K-line 중 무엇으로 붙는지 알아야 함 | `ATI`, `AT@1`, `ATDP`, `ATDPN`, `ATRV` 기록 |
| P0 | 표준 PID 실차 응답 | 앱 decoder와 값 범위 검증 필요 | `ATH1` 켜고 `010C`, `010D`, `0105`, `0142`, `0101`, `0902` raw response 저장 |
| P0 | Android-to-Pi HUD protocol | protocol에 Pi discovery와 Pi diagnostic packet 초안이 반영됨. Android는 navigation+backup speed만 보내고 Pi가 OBD/CAN을 직접 읽는 구조 | 실차 연결 후 packet/log replay로 schema 보정 |
| P0 | OBD reader 구현 방식 | Pi에서 iCar Pro 2S를 serial/rfcomm 또는 BLE GATT로 읽어야 함 | Classic SPP면 `/dev/rfcomm0`, BLE-only면 `scan-ble-obd.py <MAC>`로 RX/TX UUID 확인 |
| P1 | A4CF1 확정 여부 | A4CF2 DTC/ATF 자료를 그대로 쓰면 위험 | VIN/차량 라벨, TCM identification 응답, 부품 라벨 확인 |
| P1 | ESC/TCS 장착 여부 | ABS 후보와 ESC 후보 polling 범위가 달라짐 | 계기판 경고등, 퓨즈/모듈 라벨, 진단 앱 module scan 확인 |
| P1 | tire size/final drive | RPM/speed 기반 추정 기어 정확도에 필요 | 운전석 도어 라벨 또는 타이어 표기 기록 |
| P1 | TCM/ABS 제조사 진단 header | 변속기/ABS DTC와 current data는 일반 Mode 03만으로 부족 | Car Scanner/Torque plugin module scan 또는 전문 진단기 로그 |
| P1 | 확장 PID byte formula | OBDb command 후보는 있지만 앱에 넣으려면 offset/formula가 필요 | OBDb JSON에서 signal별 formula 추출, 실차 raw response와 비교 |
| P1 | CANable 6/14 실차 로그 | raw CAN ID/DBC가 없으므로 기어/브레이크/방향지시등은 로그로 찾아야 함 | CANable listen-only 500 kbps, 조건별 `candump`/SavvyCAN 로그 |
| P2 | 엔진 DTC 보강 테이블 | 전체 HD engine DTC DB가 없음 | 실제 발생 코드부터 AutoHex/서비스매뉴얼 근거로 추가 |
| P2 | warning thresholds | HUD 경고 색/아이콘 기준 필요 | 냉각수온, 전압, MIL, 통신 끊김 기준 정의 |
| P2 | Pi 4B 전원/부팅 정책 | 차량 상시 장착 안정성 문제 | ACC 감지, safe shutdown, read-only FS, 5V buck 사양 확정 |

## 현재 자료와 충돌하거나 조정된 내용

| 항목 | 기존 자료 | 현재 판단 |
| --- | --- | --- |
| Qvia `3/11` C-CAN | Avante HD 2006-2010 OBD 위치, pin `3/11` 표기 | 사용자 차량 DLC에는 pin `11`이 없으므로 1차 후보에서 제외. 표준 CAN `6/14`부터 본다. |
| TPMS 후보 | OBDb에 TPMS 관련 command 존재 | 사용자 차량 TPMS 없음. polling 제외 |
| A4CF2 service manual | Elantra HD 2.0/A4CF2 자료가 풍부함 | 사용자 차량은 1.6/A4CF1 가능성이 높아 참고 자료로만 사용 |
| 계기판 기어 표시 | gear/current gear 미확정 | `P/R/N/D/3/2/L` lever/range는 차량 내부에 존재. actual gear `1/2/3/4`와 별도 취급 |
| 계기판 경고등 | ABS/EPS/SRS/engine/charging/oil/brake/coolant/door lamp 관찰 | 해당 모듈 또는 cluster indicator는 존재한다. ESC/TCS lamp는 사진에서 확인되지 않아 장착 미확인 상태 유지 |

기본 HUD layout의 `dummy_data.vehicle.atf_c`는 화면/에디터 검증용 샘플값이다. 아반떼 HD 2010 1.6 AT의 실제 ATF PID나 CAN 신호가 확정됐다는 뜻은 아니며, 실차 로그로 확인하기 전까지는 표시 후보로만 둔다.

## 장비 도착 후 첫 로그 세트

### iCar Pro 2S

초기 정보:

```text
ATI
AT@1
ATDP
ATDPN
ATRV
```

표준 PID:

```text
ATH1
0100
0120
0140
0160
0101
010C
010D
0105
0142
0902
03
07
0A
```

확장 PID 후보:

```text
ATSH7E0
ATCRA7E8
2101
2102
2114

ATSH7D1
ATCRA7D9
2101
220104

ATSH7C6
ATCRA7CE
22B002
```

Windows 레이아웃 에디터의 `OBD Analysis` 탭은 위 후보를 `vehicles/avante_hd_2010_1_6_at.json`의 `obd_probe_commands`에서 읽어 probe command로 다룬다. Pi OBD baseline collector도 같은 후보를 fallback으로 실행할 수 있다. 후보는 모두 `confirmed:false`이므로 응답이 있어도 바로 HUD 표시값으로 승격하지 말고, raw response, 표준 PID, 계기판/진단 앱 값과 비교해서 formula를 확정해야 한다.

### CANable

연결:

```text
OBD pin 6  -> CANable CANH
OBD pin 14 -> CANable CANL
OBD pin 4/5 -> CANable GND
OBD pin 16 -> 연결하지 않음
CANable 120R termination -> OFF
bitrate -> 500 kbps
mode -> listen-only
```

로그 시나리오:

| 파일명 | 조건 |
| --- | --- |
| `ign_on.log` | IGN ON, engine OFF |
| `idle.log` | engine idle 1분 |
| `rpm_steps.log` | 1500/2000/2500 rpm 유지 |
| `range_prnd32l.log` | 정지 상태 `P/R/N/D/3/2/L`, 각 5초 |
| `drive_0_60.log` | 완만 가속/감속 |
| `brake.log` | 브레이크 on/off 반복 |
| `turn_signal.log` | 좌/우 방향지시등 반복 |
| `door_trunk.log` | 도어/트렁크 열고 닫기 |
| `warning_self_test.log` | IGN ON self-test, engine start, 각 경고등 소등 과정 |

Pi에 장착한 상태에서는 필요하면 OBD baseline JSON만 남긴다. CAN frame 수집과 ID/byte 분석은 Windows 레이아웃 에디터의 `CAN Analysis` 탭에서 진행한다.

```bash
python pi-hud/scripts/collect-vehicle-baseline.py \
  --obd-port /dev/rfcomm0 \
  --output /tmp/avante-hd-baseline.json
```

이 파일에는 iCar/ELM327 초기 정보, supported PID bitmap, 표준 PID/DTC raw response가 들어간다. VIN 또는 차량 상태가 섞일 수 있으므로 `vehicle-baseline/` 같은 로컬 폴더에 보관하고 그대로 commit하지 않는다.

## 앱/프로토콜 현재 상태

`docs/protocol.ko.md`에는 Raspberry Pi HUD target 식별(`device_kind=pi_hud`), Android가 Pi target에 ESP32 settings를 보내지 않는 규칙, backup speed packet, Pi diagnostic packet이 반영되어 있다. 정상 운용에서 Android는 navigation과 backup speed만 보내고, Pi가 iCar/ELM327 및 CANable/SocketCAN으로 차량 데이터를 직접 읽는다. Pi runtime은 remote `vehicle_status` packet을 무시하므로 UDP traffic이 로컬 OBD/CAN 주 차량값을 덮어쓸 수 없다.

진단 화면용:

```json
{
  "type": "dtc_snapshot",
  "seq": 124,
  "stored": ["P0700"],
  "pending": [],
  "permanent": []
}
```

raw debug용:

```json
{
  "type": "vehicle_debug",
  "can_frame_count": 128,
  "last_can_id": "0x316",
  "obd_request": "010C",
  "obd_response": "7E8 04 41 0C 1A F8"
}
```

## 판정

인터넷 공개자료 기준으로 더 찾아야 할 핵심은 거의 줄었다. 지금 부족한 것은 대부분 **실차 응답값**이다.

구현을 시작하려면 최소한 다음 3개가 필요하다.

1. iCar Pro 2S의 `ATDP`, `0100/0120/0140`, `010C/010D/0105/0142` raw response
2. `03/07/0A` DTC raw response와 `0101` MIL/DTC count
3. CANable `6/14` listen-only 로그 중 `range_prnd32l.log`

이 세트가 있으면 표준 OBD 표시, DTC 표시, 계기판 기어 표시 가능성 판단까지 다음 단계로 넘어갈 수 있다.

## Sources

- Hyundai Avante HD transmission reference: <https://at-manuals.com/transmission/avante-hd/>
- Hyundai Avante IV / G4FC listing reference: <https://buyukparts.com/price/g4fc-88826>
- Hyundai G4FC engine overview: <https://www.motorreviewer.com/engine.php?engine_id=17>
- OBDb Hyundai-Elantra signalset repository: <https://github.com/OBDb/Hyundai-Elantra>
- Hyundai Elantra HD A4CF2 troubleshooting DTC table: <https://www.hemanual.org/troubleshooting_a4cf2_-2507.html>
