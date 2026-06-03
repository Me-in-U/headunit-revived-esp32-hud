# Avante HD OBD PID Notes

[프로젝트 README](../README.ko.md) | [Protocol reference](protocol.ko.md)

이 문서는 Avante HD / Hyundai Elantra HD 세대에서 HUD용 OBD 데이터를 읽기 위한 PID 후보를 정리한다.

목표는 Raspberry Pi HUD 런타임이 iCar/ELM327 OBD 입력을 직접 읽고, 검증된 값만 1920x480 HUD 레이아웃에 표시하는 것이다. Android 브릿지는 내비게이션 정보와 GPS backup speed만 보내며, OBD 값의 주 입력 경로가 아니다.

## 분류 기준

- **확정 PID(확실)**: SAE J1979 표준 OBD-II PID 또는 ELM327 adapter command. 차량별 지원 여부는 `0100`, `0120`, `0140` supported-PID bitmap으로 확인한다.
- **확장 PID(확실)**: 공개 Hyundai Elantra OBDb signalset에 command/header/신호 정의가 있고, Avante HD 서비스 매뉴얼의 센서 구성과 맞는 항목. 그래도 실차에서 raw response와 값 범위를 검증한 뒤 HUD에 표시한다.
- **확장 PID(불확실)**: 차량 내부 데이터 또는 앱 플러그인 기능은 확인되지만, Avante HD에서 쓸 exact header/mode/PID/formula가 공개 자료만으로 확정되지 않은 항목.

Pi HUD 런타임은 모든 항목을 hardcode-visible로 켜지 말고, 먼저 지원 여부와 sane range를 확인해야 한다.

## 2010년식 자동 조건

사용자 차량 조건은 **2010년식 Avante HD 1.6 가솔린 자동**이다.

확정된 실차 사양:

| 항목 | 값 | PID/CAN 영향 |
| --- | --- | --- |
| 연식/차종 | 2010 Avante HD | OBDb/Pelican의 2010 Elantra 후보를 우선 검증한다. |
| 엔진/변속기 | 1.6 gasoline automatic | A4CF1 가능성이 높다. A4CF2 전용 자료는 참고만 하고 실차 검증한다. |
| ABS | 있음 | `7D1/7D9` ABS wheel speed/brake 후보를 검증할 가치가 있다. |
| ESC/TCS | 미확인 | steering angle, brake pressure, TCS switch는 응답하지 않을 수 있다. |
| TPMS | 없음 | TPMS PID 후보는 우선순위에서 제외한다. |
| 계기판 기어 표시 | `P/R/N/D/3/2/L` 표시 있음 | lever/range 상태는 cluster 또는 TCM 어딘가에 존재한다. actual gear와 lever position은 구분해서 검증한다. |

이 조건에서는 시장/엔진에 따라 변속기 기준을 나눠야 한다.

| 차량 조건 | 유력 변속기 | 근거 | PID 영향 |
| --- | --- | --- | --- |
| 국내 Avante HD 1.6 자동 | A4CF1 가능성이 높음 | Avante HD 1.6L 자동 재생/정비 자료가 A4CF1을 우선 표기한다. A4CF1은 1.6L급 4단 자동이다. | 사용자 실차 조건과 일치한다. A4CF2 전용 service manual 내용을 그대로 PID 확정 근거로 쓰면 안 된다. |
| Elantra HD 2.0 자동 또는 2.0 수출형 | A4CF2 가능성이 높음 | Elantra HD service manual은 A4CF2를 gasoline 2.0L용으로 설명한다. | A4CF2의 ATF 온도, input/output speed, inhibitor switch 존재는 확실하지만 exact ELM327 PID는 별도 검증 필요. |

A4CF1과 A4CF2는 기어비가 매우 유사하거나 동일하게 공개되어 있다.

| Gear | A4CF1 공개 기어비 | A4CF2 공개 기어비 |
| --- | ---: | ---: |
| 1 | `2.919` | `2.919` |
| 2 | `1.551` | `1.551` |
| 3 | `1.000` | `1.000` |
| 4 | `0.713` | `0.713` |
| Reverse | `2.480` | `2.480` |
| Final drive | `3.849` | `3.849` |

따라서 실제 기어 PID를 못 찾더라도, `010C` RPM과 `010D` speed로 추정 기어를 만드는 fallback은 A4CF1/A4CF2 양쪽에 적용할 수 있다. 단, 토크컨버터 슬립과 락업 전 상태 때문에 HUD에는 `추정`으로 표시한다.

## 확정 PID(확실)

아래 항목은 표준 OBD-II current data 또는 표준 진단 서비스다. Avante HD에서 실제 지원하는지는 supported-PID bitmap으로 결정한다.

| 목적 | 한글 설명 | Request | Response prefix | 값 | HUD 우선순위 |
| --- | --- | --- | --- | --- | --- |
| Supported PIDs 01-20 | 표준 PID 01-20 지원 여부 | `0100` | `4100` | 표준 PID 지원 bitmap | 필수 |
| Supported PIDs 21-40 | 표준 PID 21-40 지원 여부 | `0120` | `4120` | 표준 PID 지원 bitmap | 필수 |
| Supported PIDs 41-60 | 표준 PID 41-60 지원 여부 | `0140` | `4140` | 표준 PID 지원 bitmap | 필수 |
| MIL/DTC/readiness | 엔진 경고등, 고장코드 개수, 배출가스 준비 상태 | `0101` | `4101` | MIL, DTC count, readiness | 낮음 |
| Engine load | 계산된 엔진 부하율 | `0104` | `4104` | `A * 100 / 255` percent | 보조 |
| Engine coolant temperature | 엔진 냉각수 온도 | `0105` | `4105` | `A - 40` celsius | 높음 |
| Short fuel trim B1 | 단기 연료 보정값 Bank 1 | `0106` | `4106` | `(A - 128) * 100 / 128` percent | 낮음 |
| Long fuel trim B1 | 장기 연료 보정값 Bank 1 | `0107` | `4107` | `(A - 128) * 100 / 128` percent | 낮음 |
| Intake manifold pressure | 흡기 매니폴드 절대압 | `010B` | `410B` | `A` kPa | 보조 |
| Engine RPM | 엔진 회전수 | `010C` | `410C` | `((A * 256) + B) / 4` rpm | 높음 |
| Vehicle speed | 차량 속도 | `010D` | `410D` | `A` km/h | 높음 |
| Timing advance | 점화시기 진각 | `010E` | `410E` | `(A / 2) - 64` degrees | 보조 |
| Intake air temperature | 흡기 온도 | `010F` | `410F` | `A - 40` celsius | 보조 |
| MAF air flow | 흡입 공기 유량 | `0110` | `4110` | `((A * 256) + B) / 100` g/s | 보조 |
| Throttle position | 스로틀 개도율 | `0111` | `4111` | `A * 100 / 255` percent | 보조 |
| OBD compliance | 차량 OBD 표준 유형 | `011C` | `411C` | OBD standard id | 진단 |
| Engine run time | 시동 후 엔진 구동 시간 | `011F` | `411F` | `(A * 256) + B` seconds | 낮음 |
| Fuel level | 연료 잔량 | `012F` | `412F` | `A * 100 / 255` percent | 보조, 지원 시 |
| Barometric pressure | 대기압 | `0133` | `4133` | `A` kPa | 낮음 |
| Control module voltage | ECU/제어모듈 전압 | `0142` | `4142` | `((A * 256) + B) / 1000` volts | 높음 |
| VIN | 차량 식별번호 | `0902` | `4902` | VIN string | 설정/진단 |
| Stored DTC | 저장된 고장코드 | Mode `03` | `43` | stored trouble codes | 진단 |
| Pending DTC | 대기 중인 고장코드 | Mode `07` | `47` | pending trouble codes | 진단 |

ELM327 adapter voltage도 HUD/진단에 유용하다.

| 목적 | 한글 설명 | Command | 값 |
| --- | --- | --- | --- |
| Adapter detected voltage | OBD 동글이 감지한 차량 전압 | `ATRV` | adapter가 감지한 차량 전압 문자열 |

## 확장 PID(확실)

아래는 OBDb Hyundai-Elantra signalset에서 command/header/신호 정의가 확인된 확장 command 후보다. **2010년식 자동에서 모두 확정이라는 뜻은 아니다.** OBDb/Pelican 공개 support table은 2010-2012 구간에서 일부 항목을 비워 두므로, 2010 차량에서는 먼저 raw response를 저장하고 표준 PID와 계기판 값에 맞는지 비교해야 한다.

### Engine ECU

일반적으로 ELM327에서는 header와 receive address를 지정해 읽는다.

```text
ATSH7E0
ATCRA7E8
```

| Header | Receive | Request | 후보 신호 | HUD 우선순위 |
| --- | --- | --- | --- | --- |
| `7E0` | `7E8` | `21 01` | control module voltage, voltage after ignition, engine RPM, commanded idle RPM, MAP sensor voltage, intake manifold pressure, coolant sensor voltage, coolant temperature, IAT sensor voltage, intake air temperature, engine oil temperature | 높음 |
| `7E0` | `7E8` | `21 02` | O2 sensor B1S1/B1S2, vehicle speed v2, commanded evaporative purge, fuel injection timing cyl 1-4 | 보조 |
| `7E0` | `7E8` | `21 13` | timing advance 1-4, barometric pressure | 보조 |
| `7E0` | `7E8` | `21 14` | commanded throttle actuator, throttle position 1/2, throttle sensor voltage, coolant fan PWM, accelerator pedal position voltage/percent, requested torque | 높음 |
| `7E0` | `7E8` | `21 16` | knock retard cyl 1-4 | 낮음 |
| `7E0` | `7E8` | `21 17` | intake camshaft position commanded/actual | 낮음 |
| `7E0` | `7E8` | `22 E001` | intake air temperature, engine oil temperature | 보조 |
| `7E0` | `7E8` | `22 E002` | injection duration cyl 1-4 | 낮음 |
| `7E0` | `7E8` | `22 E00A` | knock retard cyl 1-4, knock learn cyl 1-4 | 낮음 |

HUD에 바로 넣기 좋은 확장 항목은 `engine oil temperature`, `accelerator pedal position`, `requested torque`, `coolant fan PWM` 정도다. RPM, coolant temperature, speed, voltage는 표준 PID와 중복되므로 표준 PID를 우선하고 확장 PID는 비교/백업으로 둔다.

### ABS/ESP and movement

아래 항목은 ABS/ESP 장착 및 모듈 응답에 따라 달라질 수 있다.

| Header | Receive | Request | 후보 신호 | HUD 우선순위 |
| --- | --- | --- | --- | --- |
| `7D1` | `7D9` | `21 01` | front/rear wheel speed | 보조 |
| `7D1` | `7D9` | `22 0104` | average speed, wheel speeds, TCS switch, steering angle, brake pressure | 보조 |
| `7D4` | `7DC` | `21 01` | steering angle v2 | 낮음 |

wheel speed와 brake pressure는 HUD 표시보다 진단/로그 가치가 높다. 주행 중 update rate가 높을 수 있으므로 navigation/speed 전송을 방해하지 않게 polling 주기를 낮춰야 한다.

### Cluster

| Header | Receive | Request | 후보 신호 | HUD 우선순위 |
| --- | --- | --- | --- | --- |
| `7C6` | `7CE` | `22 B002` | fuel level volume, cluster voltage, odometer km/miles | 보조 |

연료량은 표준 `012F`가 지원되면 표준 PID를 우선한다. odometer는 HUD 표시보다 진단 화면에서만 다룬다.

## 확장 PID(불확실)

아래 항목은 차량 내부 데이터 또는 앱 플러그인 기능은 확인되지만, Avante HD에서 Pi HUD 런타임에 바로 넣을 exact command가 아직 불확실하다.

| 항목 | 상태 | 조사 근거 | 다음 검증 |
| --- | --- | --- | --- |
| ATF temperature | 차량에 센서와 GDS current data가 있음. exact ELM327 PID는 미확정 | A4CF2 service manual은 ATF temperature sensor를 thermistor로 설명하고, 2007 Elantra TSB도 GDS/Hi-Scan의 Automatic Transaxle `Fluid Temperature Sensor` readout을 언급 | Torque Pro + Advanced LT/EX 또는 Car Scanner에서 실제 표시 여부 확인 후 raw command 캡처 |
| Current gear, actual gear | Advanced EX for HYUNDAI 기능 목록에 `AT Current Gear`가 있음. exact PID는 미공개 | Torque plugin 설명, A4CF1/A4CF2 전자제어 4단 자동 구조 | `AT Current Gear`가 뜨는지 확인. 뜨면 동일 조건에서 raw response를 로그 |
| Shift lever position `P/R/N/D/3/2/L` | inhibitor/range switch가 있으므로 차량 내부에는 존재. OBD read command 미확정 | A4CF2 service manual은 gear shift position을 `7 range (P,R,N,D,3,2,L)`로 명시하고, inhibitor switch가 select lever position을 감지한다고 설명 | TCM/BCM current data에서 읽을 수 있는지 확인 |
| AT turbine speed / output speed | Advanced EX 기능 목록에 있음. exact PID 미공개 | Torque plugin 설명 | 실제 앱 표시 여부 확인 |
| Damper clutch lockup | Advanced EX 기능 목록에 있음. exact PID 미공개 | Torque plugin 설명 | 값 범위와 토크컨버터 lockup 상태 비교 |
| HIVEC mode | Advanced EX 기능 목록에 있음. exact PID 미공개 | Torque plugin 설명 | 실제 앱 표시 여부 확인 |
| TPMS pressure/temperature | OBDb에 `7A0/7A8 22 C00B`, `7D6/7DE 21 06` 후보가 있음. 사용자 차량은 TPMS가 없으므로 우선 제외 | OBDb signalset | 현재 차량에서는 polling하지 않는다 |
| Reverse gear selected | OBDb/Pelican에는 `ELANTRA_GEAR_R`가 있지만 2021+ 계열로 보이며 2010 HD에는 적용 불확실 | 공개 support table에서 2010-2012가 아니라 2021-2025 쪽만 표시됨 | 2010 차량에는 우선 넣지 않는다. 레버 위치는 inhibitor/TCM current data로 별도 확인 |

기어 표시가 꼭 필요하면 1차 구현은 실제 PID 대신 추정 기어를 쓸 수 있다.

```text
estimated_gear = speed_kmh + engine_rpm + tire_size + A4CF2 gear ratio 기반 추정
```

A4CF2 기준 기어비:

| Gear | Ratio |
| --- | ---: |
| 1 | `2.919` |
| 2 | `1.551` |
| 3 | `1.000` |
| 4 | `0.713` |
| Final drive | `3.849` |

추정 기어는 토크컨버터 슬립, 저속, 변속 중, 락업 전 상태에서 틀릴 수 있으므로 HUD에는 `추정` 상태로만 표시한다.

## Pi HUD 구현 순서

1. 표준 PID scanner를 먼저 만든다: `0100`, `0120`, `0140`으로 지원 목록을 만들고, 지원되는 표준 PID만 polling한다.
2. HUD 1차 값은 `010D`, `010C`, `0105`, `0142` 또는 `ATRV`로 제한한다.
3. 확장 PID는 별도 debug screen에서만 raw response, decode value, sane range를 보여준다.
4. 같은 값을 표준 PID와 확장 PID가 모두 제공하면 표준 PID를 우선하고, 확장 PID는 비교 로그로만 둔다.
5. ATF temperature/current gear는 앱 플러그인 또는 전문 진단기에서 실제 표시를 확인하기 전까지 HUD contract에 넣지 않는다.
6. 확장 PID 하나가 응답하지 않아도 OBD polling loop 전체를 막지 않는다. timeout, no data, invalid response는 field 단위로 격리한다.

현재 Pi baseline collector는 기본 표준 PID/DTC 명령 뒤에 차량 profile의 `obd_probe_commands`를 자동으로 추가한다. `avante_hd_2010_1_6_at` profile에는 위 Engine ECU, ABS/ESP, Cluster 후보가 들어 있으며 모두 `confirmed:false`다. 이 값은 실차 응답 수집용이지 HUD 표시 확정값이 아니다.

## 실차 검증 체크리스트

- 시동 OFF/ACC/ON/engine running 상태별 연결 로그를 저장한다.
- `ATH1`을 켜서 response header를 포함한 raw frame을 저장한다.
- idle, 정속, 가속, 감속, warm-up 구간을 각각 1분 이상 기록한다.
- 냉각수온은 냉간에서 외기 근처로 시작해 80-100도 범위로 상승하는지 본다.
- 전압은 시동 전 약 12V대, 시동 후 약 13-14V대인지 본다.
- RPM과 속도는 계기판/표준 PID와 확장 PID가 크게 어긋나지 않는지 본다.
- ATF temperature/current gear는 값이 표시되더라도 range와 변화 패턴이 맞기 전까지 HUD에 표시하지 않는다.

## Sources

- OBDb Hyundai-Elantra signalset: <https://github.com/OBDb/Hyundai-Elantra>
- Pelican Hyundai Elantra OBD support table: <https://pelican.clutch.engineering/cars/hyundai/elantra/>
- python-OBD command table for standard PIDs: <https://python-obd.readthedocs.io/en/latest/Command%20Tables/>
- Advanced EX for HYUNDAI Torque plugin: <https://play.google.com/store/apps/details?id=com.ideeo.hnadvanced>
- 2007 Elantra ATF temperature TSB: <https://static.oemdtc.com/TSB/07-40-012.pdf>
- Elantra HD engine sensor service manual mirror: <https://www.hemanual.org/components_and_components_location-2404.html>
- A4CF2 gear ratio reference: <https://gearboxlist.com/hyundai/a4cf2/>
- A4CF1 gear ratio/reference: <https://gearboxlist.com/hyundai/a4cf1/>
- Avante HD transmission reference: <https://at-manuals.com/transmission/avante-hd/>
