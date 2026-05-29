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
| P0 | Android-to-Pi HUD protocol | 현재 protocol은 ESP32 OLED 중심이며 OBD/vehicle packet이 없음 | `vehicle_status`, `dtc_snapshot`, `vehicle_debug` packet schema 정의 |
| P0 | OBD reader 구현 방식 | 현재 Android 앱에는 iCar Pro 2S 연결/ELM327 reader가 없음 | BLE GATT인지 Bluetooth Classic SPP인지 제품 실물로 확인 후 구현 |
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

## 앱/프로토콜에서 새로 정해야 할 것

현재 `docs/protocol.ko.md`에는 navigation, speed, settings만 있다. Pi 4B HUD와 OBD를 쓰려면 새 packet을 additive하게 추가해야 한다.

초안:

```json
{
  "type": "vehicle_status",
  "seq": 123,
  "speed_kmh_obd": 42,
  "rpm": 1850,
  "coolant_c": 88,
  "voltage_v": 14.1,
  "mil": false,
  "dtc_count": 0,
  "gear_range": "D",
  "gear_actual": null,
  "source": "obd"
}
```

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
  "type": "obd_raw",
  "request": "010C",
  "response": "7E8 04 41 0C 1A F8",
  "ok": true
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
