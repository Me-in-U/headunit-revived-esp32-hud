# Avante HD CANable Checklist

[프로젝트 README](../README.ko.md) | [CAN research](avante-hd-can-research.ko.md) | [Missing data audit](avante-hd-missing-data.ko.md)

이 문서는 2010 Avante HD 1.6 gasoline automatic 차량에 CANable을 연결한 뒤 확인할 체크리스트다.

## 0. 준비물

| 항목 | 확인 |
| --- | --- |
| MKS CANable V2.0 Pro S 또는 CANable compatible adapter | 준비 |
| OBD2 male open cable | 준비 |
| 노트북 | 준비 |
| SavvyCAN 또는 Cangaroo | 설치 |
| 멀티미터 | 있으면 좋음 |
| CANable 120R termination | OFF로 시작 |

## 1. 차량 OBD 핀 확인

사용자 차량에서 확인된 populated pin:

```text
16, 15, 14, 12, 8, 6, 5, 4, 3
```

1차 연결은 표준 CAN만 사용한다.

```text
OBD pin 6  -> CANable CANH
OBD pin 14 -> CANable CANL
OBD pin 4 또는 5 -> CANable GND
OBD pin 16 -> 연결하지 않음
```

주의:

```text
pin 16 +12V는 CANable에 연결하지 않는다.
pin 3은 단독으로 쓰지 않는다.
pin 11이 없으므로 Qvia 3/11 C-CAN 후보는 현재 차량에서 제외한다.
```

## 2. 전원 OFF 상태 안전 확인

차량 전원 OFF, 가능하면 키 OFF 상태에서 확인한다.

| 확인 | 정상 기대 | 비고 |
| --- | --- | --- |
| CANable USB 전원 | 노트북 USB로만 공급 | OBD +12V 사용 금지 |
| CANable termination | OFF | 차량 CAN bus는 이미 종단되어 있음 |
| OBD 6-14 저항 | 대략 60 ohm 근처면 일반적인 CAN bus 가능성 높음 | 전원 켠 상태에서 저항 측정 금지 |
| open cable 단선/쇼트 | CANH/CANL/GND가 서로 쇼트되지 않음 | 색상보다 pin 번호 우선 |

저항이 이상해도 바로 단정하지 않는다. 일부 차량/게이트웨이 구성에서는 측정값이 다를 수 있으므로, 배선 실수와 termination ON 여부를 먼저 확인한다.

## 3. 노트북에서 CANable 인식 확인

Windows 기준:

| 확인 | 기대 |
| --- | --- |
| 장치관리자 | COM 포트 또는 USB-CAN 장치로 인식 |
| SavvyCAN/Cangaroo | CANable 선택 가능 |
| firmware mode | `slcan` 또는 `candleLight` 중 하나로 동작 |

처음 설정:

```text
bitrate: 500000
mode: listen-only / no transmit
termination: OFF
```

Car Scanner가 사용자 차량을 ISO-15765-4, 11bit ID, 500 kbaud로 확인했으므로 DLC `6/14` 표준 진단 CAN의 첫 bitrate는 500k로 둔다.

송신 기능, replay, transmit 버튼은 누르지 않는다.

## 4. 첫 프레임 확인

순서:

1. CANable을 노트북에 연결한다.
2. OBD open cable을 차량에 꽂는다.
3. `6/14/GND`만 CANable에 연결한다.
4. SavvyCAN/Cangaroo에서 500 kbps listen-only로 연다.
5. IGN ON으로 돌린다.
6. frame이 올라오는지 본다.
7. 시동을 건다.
8. frame rate가 늘거나 값이 변하는지 본다.

정상 예:

```text
ID       DLC  DATA
0x316    8    05 20 00 00 ...
0x329    8    ...
0x545    8    ...
```

이 단계에서는 ID 의미를 해석하지 않는다. **프레임이 보이는지**만 확인한다.

## 5. 아무 프레임도 안 보일 때

순서대로 확인:

| 순서 | 확인 |
| --- | --- |
| 1 | CANH/CANL이 뒤바뀌지 않았는지 확인 |
| 2 | GND가 OBD pin 4 또는 5에 연결됐는지 확인 |
| 3 | bitrate 500k 재확인 |
| 4 | listen-only가 켜져 있어도 수신은 되는지 프로그램 설정 확인 |
| 5 | CANable termination이 OFF인지 확인 |
| 6 | IGN ON 또는 engine running 상태인지 확인 |
| 7 | 250k, 125k는 나중에만 시도 |

처음부터 다른 pin에 연결하지 않는다. 사용자 차량에는 `6/14`가 있으므로 표준 CAN부터 확정한다.

## 6. 필수 로그 세트

로그 파일은 같은 날짜/장소 기준으로 저장한다.

| 파일명 | 조건 | 목적 |
| --- | --- | --- |
| `01_ign_on.log` | IGN ON, engine OFF, 30초 | 기본 활성 frame |
| `02_idle.log` | engine idle, 60초 | RPM/coolant/voltage 후보 |
| `03_rpm_steps.log` | 1500, 2000, 2500 rpm 각 10초 | RPM byte 후보 |
| `04_range_prnd32l.log` | 브레이크 밟고 `P/R/N/D/3/2/L` 각 5초 | lever/range 후보 |
| `05_brake.log` | 브레이크 on/off 20회 | brake switch/pressure 후보 |
| `06_turn_signal.log` | 좌깜빡이 20초, 우깜빡이 20초 | indicator 후보 |
| `07_door_trunk.log` | 도어/트렁크 열고 닫기 | body/cluster 후보 |
| `08_drive_0_60.log` | 안전한 곳에서 0-60 km/h 완만 가속/감속 | speed/wheel/actual gear 후보 |
| `09_warning_self_test.log` | IGN ON self-test, 시동, 경고등 소등 과정 | battery/oil/check engine/EPS/ABS/SRS/coolant cluster 후보 |

주행 로그는 안전한 장소에서 동승자 또는 고정된 노트북으로 기록한다. 운전자가 노트북을 조작하지 않는다.

Pi + SocketCAN으로 바로 남길 때는 같은 시나리오 이름을 JSON에도 넣는다.

```bash
pi-hud/scripts/setup-canable-from-env.sh

python pi-hud/scripts/collect-vehicle-baseline.py \
  --scenario 02_idle \
  --can-channel can0 \
  --can-duration 60 \
  --output vehicle-baseline/02_idle.json

python pi-hud/scripts/summarize-can-baseline.py \
  vehicle-baseline/02_idle.json \
  --output vehicle-baseline/02_idle-can-summary.json
```

OBD를 아직 같이 연결하지 않았거나 CAN frame만 먼저 보고 싶으면 `--skip-obd`를 추가한다. 반대로 OBD baseline만 남길 때는 `--skip-can`을 추가한다.

## 7. iCar Pro 2S와 같이 쓸 때

OBD splitter를 쓰는 경우:

```text
차량 OBD
 -> OBD splitter
    -> iCar Pro 2S
    -> OBD open cable -> CANable
```

이 상태에서 iCar Pro 2S가 `010C`, `010D` 같은 요청을 보내면 CANable 로그에 `7E0/7E8` 진단 요청/응답이 보일 수 있다.

이건 문제라기보다 도움이 된다.

```text
7E0 = tester/request 쪽
7E8 = ECU response 쪽
41 0C = RPM 응답
41 0D = speed 응답
```

단, passive broadcast CAN을 찾을 때는 iCar 요청이 로그에 섞인다는 점을 기록한다.

## 8. 로그 중 적어둘 메모

로그 파일과 별도로 메모를 남긴다.

```text
날짜/시간:
차량 상태:
CANable firmware:
프로그램:
bitrate:
termination:
연결 pin:
시동 전 전압:
시동 후 전압:
계기판 속도/RPM 대략값:
기어 조작 순서:
IGN ON self-test에서 켜진 경고등:
특이사항:
```

## 9. 다음 분석 기준

우선 찾을 것:

| 신호 | 비교 기준 |
| --- | --- |
| RPM | `010C` 또는 계기판 tachometer |
| Speed | `010D` 또는 계기판 speedometer |
| Lever/range | `P/R/N/D/3/2/L` 조작 순서 |
| Brake | brake on/off 로그 |
| Turn signal | 좌/우 방향지시등 주기 |

처음부터 DBC를 만들려고 하지 않는다. 먼저 조건별로 변하는 ID 후보를 좁힌다.

## 10. 중단해야 하는 상황

아래 상황이면 연결을 멈춘다.

```text
CANable 또는 케이블이 뜨거워짐
차량 경고등이 갑자기 다수 점등
계기판이 꺼졌다 켜짐
SavvyCAN에서 transmit/replay를 실수로 실행함
CANH/CANL/GND 외에 +12V가 CANable에 닿음
```

문제가 생기면 OBD 케이블을 먼저 뽑고, 그 다음 CANable USB를 뽑는다.
