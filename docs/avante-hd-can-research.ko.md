# Avante HD CAN Data Research

[프로젝트 README](../README.ko.md) | [OBD PID notes](avante-hd-obd-pids.ko.md)

이 문서는 2010년식 Avante HD / Hyundai Elantra HD 자동 차량에서 HUD용 CAN 데이터를 찾기 위한 공개 자료 조사 결과를 정리한다.

핵심 결론은 **HD 전용 공개 DBC는 아직 확인되지 않았고**, 바로 구현 가능한 경로는 raw CAN sniffing보다 **OBD/UDS 요청-응답 기반 확장 PID 검증**이다. passive CAN 데이터는 실차 로그로 직접 확정해야 한다.

## 대상 차량

| 항목 | 값 | CAN 조사 영향 |
| --- | --- | --- |
| 차량 | 2010 Avante HD 1.6 gasoline automatic | 국내 1.6/A4CF1 기준으로 본다. |
| ABS | 있음 | ABS wheel speed 후보는 실제 응답 가능성이 있다. |
| ESC/TCS | 미확인 | ESC/TCS 전용 brake pressure, steering angle, TCS switch는 장착 여부를 먼저 확인한다. |
| TPMS | 없음 | TPMS CAN/OBD 후보는 이번 차량에서는 제외한다. |
| 계기판 기어 표시 | `P/R/N/D/3/2/L` | lever/range 표시 신호는 cluster/TCM 쪽에 존재한다. raw CAN에서 우선 찾을 가치가 높다. |
| 계기판 경고등 관찰 | door open, battery/charging, parking brake/brake, ABS, SRS airbag, oil pressure, check engine, EPS, coolant temperature | cluster indicator 후보로 기록한다. ESC/TCS lamp는 사진에서 확인되지 않아 계속 미확인으로 둔다. |

## 결론

| 분류 | 현재 상태 | HUD 적용 판단 |
| --- | --- | --- |
| HD 전용 DBC | 공개 GitHub/OpenDBC 계열에서 Avante HD / Elantra HD 2006-2010 전용 DBC를 찾지 못함 | 바로 적용 불가 |
| 표준 OBD-II PID | SAE J1979 PID로 speed/RPM/coolant/voltage 등 확보 가능 | 1차 구현에 사용 |
| Hyundai Elantra OBDb signalset | `7E0/7E8`, `7D1/7D9`, `7C6/7CE` 등 header/request 후보가 있음 | debug screen에서 검증 후 일부 사용 |
| 정비/진단 자료 | HD가 CAN 2.0B를 쓰며 ECM, TCM, ABS/ESC 등이 CAN으로 신호를 공유한다는 근거 있음 | 어떤 신호가 CAN에 있는지 판단하는 근거 |
| 배선 자료 | 2010 Elantra computer data lines / cluster wiring 자료에서 DLC, ECM, TCM, ABS/ESC, BCM, cluster, CAN high/low 항목 확인 | 어디서 sniff할지 정하는 근거 |
| 다른 현대차 DBC | Tiburon GK, Hyundai 2015, i30 2014, Santa Fe 2007 등은 존재 | byte/formula 참고만 가능, HD에 그대로 적용 금지 |

## 추가 확인 자료

| 자료 | 확인된 내용 | 해석 |
| --- | --- | --- |
| AutoHex `U0100` HD 2010 | powertrain 제어에 CAN 2.0B를 쓰고, ECM/TCM이 engine speed, APS, engaged gear, torque reduction 신호를 CAN으로 공유한다고 설명 | 기어/속도/RPM은 차량 내부 CAN에 존재할 가능성이 높음 |
| AutoHex `U0101` HD 2010 | ECM과 TCM 사이 통신은 CAN이며, TCM message가 없으면 DTC가 설정됨 | 자동변속기 정보는 TCM 또는 ECM-TCM CAN에서 찾아야 함 |
| AutoHex `P0700` HD 2010 | TCM이 CAN으로 ECM에 MIL 점등을 요청함 | TCM이 CAN에 붙어 있고 진단기로 TCM system을 따로 봐야 함 |
| AutoHex `C1611` HD 2007 | HECU가 torque reduction, fuel cut cylinder count, ESP request를 CAN으로 Engine PCM에 보내고, PCM/TCM이 ESP 중 current gear position을 유지한다고 설명 | ABS/ESP와 powertrain CAN 사이에 토크/기어 관련 메시지가 있음 |
| AutoHex `C1617`, `C1103` HD 2010 | EPS가 EMS에서 vehicle speed, engine RPM 신호를 CAN으로 받는다고 설명 | speed/RPM broadcast가 있을 가능성이 높음 |
| Portal Diagnostov 2010 Elantra wiring | Computer Data Lines에 DLC, ECM, TCM, ABS/ESC, EPS, BCM, cluster, CAN high/low가 등장 | OBD 단자와 각 모듈에서 CAN sniff 위치를 잡는 자료 |
| Qvia K-900 Hyundai/Kia 장착 매뉴얼 | Avante HD 2006-2010을 `C-CAN`, 연결위치 `OBD`, LOW `Y(11)`, HIGH `W(3)`, 방향지시등 지원 `X`로 표기 | 표준 진단 CAN `6/14`와 별개로 vendor-specific OBD pin `3/11`에 편의/차체 CAN이 있을 수 있다는 참고 자료. 단, 사용자 차량 DLC에는 pin `11`이 없으므로 이 차량의 1차 후보에서는 제외 |
| MonsterGauge 지원표 | Avante HD 2006-2010 diesel/gasoline 지원 | 상용 OBD/CAN 스캐너가 HD에서 일부 주행/엔진 정보를 읽는다는 간접 증거 |
| Advanced EX for HYUNDAI | AT oil temperature, AT current gear, turbine/output speed 등을 Torque Pro PID로 제공하며 Elantra/i30 2.0 tested로 표기 | exact PID는 공개되지 않았지만 TCM 확장 PID가 존재할 가능성이 큼 |

## CAN에 존재할 가능성이 높은 신호

정비 DTC 자료 기준으로 HD 계열 powertrain CAN에는 최소한 아래 신호가 오간다.

| 신호 | 근거 | HUD 가치 | 확정 방법 |
| --- | --- | --- | --- |
| Engine speed / RPM | ECM/TCM/ABS 계통에서 engine speed 공유 | 높음 | 표준 `010C`와 passive CAN 후보 비교 |
| Accelerator pedal sensor / APS | ECM/TCM CAN 공유 신호로 언급 | 보조 | OBDb `7E0 21 14` 또는 passive log와 페달 입력 비교 |
| Engaged gear / current gear | ECM/TCM CAN 공유 신호로 언급, TCM/ESC 제어에서 current gear 유지 언급 | 높음 | P/R/N/D/3/2/L 정지 로그와 주행 로그로 후보 ID 분리 |
| Torque reduction / torque request | ABS/ESC/ECM/TCM 상호제어에서 언급 | 낮음 | HUD에는 불필요, 진단 로그 가치 |
| Wheel speeds | ABS/ESC 모듈 및 OBDb 후보 | 보조 | OBDb `7D1 21 01`, `7D1 22 0104` 또는 ABS CAN sniff |
| Brake pressure / brake state | OBDb 후보 및 ABS/ESC 계통 | 보조 | 브레이크 on/off 반복 로그 |
| Steering angle | EPS/ESC/OBDb 후보 | 낮음 | 정지 상태 좌우 조향 로그 |
| Fuel level / odometer / cluster voltage | cluster OBDb 후보, cluster wiring 자료 | 보조 | `7C6 22 B002` 응답 검증 |
| Door/trunk/indicator cluster states | cluster/BCM wiring 자료에 항목 존재 | 낮음 | body/cluster bus sniff 필요, OBD 진단 CAN에서 안 보일 수 있음 |
| Warning lamps | cluster self-test에서 door open, charging, brake, ABS, SRS airbag, oil pressure, check engine, EPS, coolant temperature가 관찰됨 | 보조 | IGN ON self-test, engine start 전후, parking brake on/off, door open/close 로그 비교 |

## 공개 OBDb 후보

OBDb Hyundai-Elantra signalset는 raw broadcast DBC가 아니라 **진단 요청/응답 command 정의**에 가깝다. ELM327 계열 OBD 동글로 검증하기 쉽기 때문에 HUD 프로젝트에는 이쪽이 우선이다.

| 모듈 추정 | Header | Receive | Request | 후보 신호 | 2010 HD 판단 |
| --- | --- | --- | --- | --- | --- |
| Engine ECU | `7E0` | `7E8` | `21 01` | RPM, coolant temperature, oil temperature, voltage 계열 | 일부 2010-2012 후보. 실차 응답 필요 |
| Engine ECU | `7E0` | `7E8` | `21 02` | vehicle speed v2, O2, fuel injection timing | 실차 응답 필요 |
| Engine ECU | `7E0` | `7E8` | `21 14` | accelerator pedal position, requested torque, throttle, fan PWM | 실차 응답 필요 |
| ABS/ESP | `7D1` | `7D9` | `21 01` | wheel speed | ABS/ESP 장착 여부 의존 |
| ABS/ESP | `7D1` | `7D9` | `22 0104` | steering angle, brake pressure, average speed, wheel speeds | ABS/ESP 장착 여부 의존 |
| Cluster | `7C6` | `7CE` | `22 B002` | fuel level volume, cluster voltage, odometer | 응답하면 HUD/진단에 유용 |
| TPMS | `7A0` | `7A8` | `22 C00B` | tire pressure | 사용자 차량은 TPMS 없음. 제외 |
| Newer gear signal | `770` | `778` | `22 BC04` | reverse gear selected | OBDb상 2021+ 계열로 보이며 2010 HD에는 우선 제외 |

## Raw CAN 스니핑 후보

HD 전용 DBC가 없으므로 아래는 **확정 ID가 아니라 실차 로그에서 먼저 찾을 후보 패턴**이다.

| 후보 | 예상 bus | 찾는 방법 |
| --- | --- | --- |
| RPM/speed broadcast | powertrain CAN | 시동 idle, 1500/2000/2500 rpm 유지, 저속 주행 로그를 표준 PID와 시간 동기화 |
| lever/range `P/R/N/D/3/2/L` | powertrain CAN, TCM, cluster 관련 bus | 사용자 차량 계기판에 표시됨. 브레이크 밟고 `P -> R -> N -> D -> 3 -> 2 -> L` 전환, 각 상태 5초 이상 로그 |
| actual gear `1/2/3/4` | TCM/powertrain CAN | `D` 주행 중 변속 시점과 speed/RPM 변화에 맞춰 후보를 찾음. lever/range와 별도 신호로 취급 |
| brake/ABS | ABS/ESC CAN | 정지 상태 브레이크 on/off 20회, 서행 제동 로그 |
| steering angle | EPS/ESC CAN | 정지 상태 핸들 중앙/좌/우 끝단 로그 |
| turn/high beam/door/trunk | body/cluster CAN 또는 hardwire input | 방향지시등/상향등/도어/트렁크 반복. 진단 CAN에서 안 보일 수 있음 |
| cluster warning lamps | cluster/BCM, 각 제어모듈 warning request | IGN ON self-test와 시동 후 소등 전환 비교. door, parking brake는 조건 조작 가능 |
| fuel/cluster | cluster/BCM | 연료량은 단기 변화가 작아 진단 요청 `7C6 22 B002`를 우선 확인 |

## OBD 포트와 bus 주의점

표준 OBD-II 진단 CAN은 보통 DLC pin `6` CAN-H, pin `14` CAN-L이다. 다만 일부 국산차/장착 매뉴얼 자료에서는 body 또는 convenience CAN을 DLC의 vendor-specific pin에 노출하는 경우가 있다.

Qvia K-900 장착 매뉴얼은 Avante HD 2006-2010에 대해 `C-CAN`, OBD 위치, LOW pin `11`, HIGH pin `3`을 적고 있다. 이 자료는 aftermarket remote-start/경보기 장착용이므로 진단 CAN 표준 pinout으로 일반화하면 안 된다. 사용자 차량에서 확인된 DLC populated pin은 `16`, `15`, `14`, `12`, `8`, `6`, `5`, `4`, `3`이고 pin `11`이 없으므로, 이 차량에서는 `3/11` C-CAN 후보를 우선 제외한다.

실차에서는 다음 순서로 확인한다.

1. OBD 스캐너/ELM327로 표준 PID가 읽히는지 확인한다.
2. CAN adapter를 listen-only로 놓고 DLC `6/14`, 500 kbps부터 passive log를 본다.
3. frame이 없거나 기대 신호가 부족하면 배선도 기준으로 모듈 커넥터 쪽 CAN pair를 찾는다. 현재 차량의 DLC에서는 pin `3`만으로 CAN pair를 만들 수 없다.
4. 모르는 frame은 절대 송신하지 않는다. 먼저 listen-only로 수집한다.
5. bus 저항은 전원 OFF 상태에서 CAN-H/CAN-L 사이 약 60 ohm 수준인지 확인한다.

## 로깅 시나리오

HUD에 필요한 신호를 분리하려면 같은 조건에서 표준 OBD 값과 raw CAN 로그를 동시에 남기는 것이 좋다.

| 시나리오 | 목적 |
| --- | --- |
| IGN OFF / ACC / ON / engine running | 전원 상태, cluster/ECU 활성 frame 구분 |
| idle 1분 | RPM, coolant, voltage 기본값 |
| 1500/2000/2500 rpm 유지 | RPM byte/formula 후보 찾기 |
| 0-60 km/h 완만 가속/감속 | vehicle speed, wheel speed 후보 찾기 |
| P/R/N/D/3/2/L 전환 | lever/range byte 찾기. 계기판 표시와 동기화 |
| D range 완만 가속/감속 | actual gear byte 또는 추정 gear 검증 |
| 브레이크 on/off 반복 | brake switch/pressure 후보 찾기 |
| 핸들 중앙/좌/우 | steering angle 후보 찾기 |
| 방향지시등/상향등/도어/트렁크 반복 | body/cluster 상태 후보 확인 |
| 시동 전후 warning lamp self-test | check engine, battery, oil pressure, EPS, ABS, SRS, coolant warning 상태 후보 확인 |
| 냉간 -> 예열 | coolant/ATF temperature 후보 검증 |

## 구현 우선순위

1. **Pi 로컬 OBD reader**: 표준 PID `010D`, `010C`, `0105`, `0142` 또는 `ATRV`부터 안정화한다.
2. **Pi 확장 PID debug mode**: OBDb 후보를 request 단위로 켜고 raw response, decoded value, timeout을 저장한다.
3. **HUD state 확장**: 검증된 값만 `vehicle.*`, `warnings.*`, `dtc.*` 같은 Pi 로컬 상태로 추가한다.
4. **Pi Raw CAN logger**: 기어 위치, 방향지시등, cluster 상태처럼 OBD로 안 잡히는 항목만 CANable/SocketCAN으로 조사한다.
5. **DBC 작성**: 실차에서 확정한 frame만 `docs/can/avante_hd_2010.dbc` 같은 별도 파일로 누적한다.

런타임 쪽 확정 CAN 매핑은 차량 profile의 `can_signals` 배열에 넣는다. 실차 로그로 frame ID, byte/bit 위치, scale/offset 또는 value map이 확인된 항목만 `confirmed:true`로 저장하며, Pi SocketCAN source는 이 항목만 decode해서 HUD state에 합친다. Byte 값은 `start_byte` + `length`로, warning lamp나 switch 같은 bit flag는 `start_byte` + `start_bit` + `bit_length`로 정의한다. Bit 번호는 해당 byte의 LSB를 `0`으로 본다. 현재 `avante_hd_2010_1_6_at` profile은 HD 전용 CAN ID가 아직 확정되지 않았으므로 `can_signals: []`가 정상 상태다.

## 필요한 장비

| 목적 | 장비 | 비고 |
| --- | --- | --- |
| 표준/확장 OBD | Vgate iCar Pro 2S, BLE/BT ELM327 | Pi HUD 런타임에서 직접 읽는 1차 입력 |
| passive CAN sniff | CANable, CANtact, USBtin, CANedge, comma panda | listen-only 지원 중요 |
| Pi 기반 HUD와 같이 로깅 | Raspberry Pi + USB-CAN + SavvyCAN/can-utils | HDMI bar LCD HUD와 궁합 좋음 |
| 안전 확인 | multimeter | CAN pair 저항/전압 확인 |

## 판정

테슬라 보조 HUD처럼 만들 목적이면, 지금 당장 쓸 수 있는 안정 데이터는 다음 정도다.

| 바로 사용 | 검증 후 사용 | raw CAN 필요 가능성 높음 |
| --- | --- | --- |
| speed, RPM, coolant, voltage, DTC | oil temperature, pedal position, torque, wheel speed, brake pressure, fuel volume, odometer | actual gear/range, turn signal, high beam, door/trunk, cluster indicator |

기어 위치는 CAN에 존재할 가능성이 높지만, **2010 HD에서 바로 쓸 수 있는 공개 PID/DBC는 못 찾았다**. 1차 HUD는 RPM/speed/기어비 기반 `추정 기어`로 표시하고, 실차 로그로 actual gear를 찾으면 교체하는 방식이 현실적이다.

## Sources

- OBDb Hyundai-Elantra signalset repository: <https://github.com/OBDb/Hyundai-Elantra>
- Pelican Hyundai Elantra OBD support table: <https://pelican.clutch.engineering/cars/hyundai/elantra/>
- AutoHex Hyundai ELANTRA(HD) 2010 U0100 CAN timeout: <https://www.autohex.net/dtc-help/hyundai/61/2010/12055/U0100/>
- AutoHex Hyundai ELANTRA(HD) 2010 P0701 TCM status error: <https://www.autohex.net/dtc-help/hyundai/61/2010/12055/P0701/>
- AutoHex Hyundai ELANTRA(HD) 2007 C1611 CAN timeout EMS: <https://www.autohex.net/dtc-help/hyundai/61/2007/12055/C1611/>
- Portal Diagnostov Hyundai Elantra SE 2010 computer data lines: <https://portal-diagnostov.com/en/2020/04/02/elektroshemy-sistema-peredachi-dannyh-hyundai-elantra-se-2010/>
- Portal Diagnostov Hyundai Elantra Blue 2010 instrument cluster wiring: <https://portal-diagnostov.com/en/2020/03/26/instrument-cluster-hyundai-elantra-blue-2010-system-wiring-diagrams/>
- Qvia K-900 Hyundai/Kia installation manual: <https://www.qvia1.com/manual/K-900_hyundai_kia.pdf>
- MonsterGauge supported vehicle list: <https://www.monstergauge.com/noticelist/b96e2e48928611eb9630fa163e30e7b7>
- KBench CruzePlus Intensive X1 / MonsterGauge review: <https://kbench.com/?q=node%2F161987>
- Advanced EX for HYUNDAI Torque plugin: <https://play.google.com/store/apps/details?id=com.ideeo.hnadvanced>
- comma.ai opendbc DBC directory: <https://github.com/commaai/opendbc/tree/master/opendbc/dbc>
- OpenGK Hyundai Tiburon CAN messages, reference only: <https://opengk.org/index.php?title=CAN_Bus_messages>
