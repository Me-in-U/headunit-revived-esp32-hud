# Avante HD DTC Notes

[프로젝트 README](../README.ko.md) | [OBD PID notes](avante-hd-obd-pids.ko.md) | [CAN research](avante-hd-can-research.ko.md)

이 문서는 2010년식 Avante HD / Hyundai Elantra HD 자동 차량에서 브리지 앱이 고장코드(DTC)를 읽고 HUD 또는 진단 화면에 표시하기 위한 자료 조사 결과를 정리한다.

## 대상 차량

| 항목 | 값 | DTC 영향 |
| --- | --- | --- |
| 차량 | 2010 Avante HD 1.6 gasoline automatic | 국내 1.6/A4CF1 기준으로 본다. |
| ABS | 있음 | ABS/EPS 계열 `C` 코드가 실제로 존재할 수 있다. |
| ESC/TCS | 미확인 | ESC 전용 코드는 장착 여부에 따라 다르다. |
| TPMS | 없음 | TPMS 관련 코드는 앱 보강 테이블 우선순위에서 제외한다. |
| 계기판 기어 표시 | `P/R/N/D/3/2/L` | range sensor/inhibitor 관련 변속기 DTC는 표시 가치가 높다. |
| 계기판 경고등 관찰 | door open, battery/charging, parking brake/brake, ABS, SRS airbag, oil pressure, check engine, EPS, coolant temperature | engine/ABS/EPS/SRS/charging/oil/brake/coolant/door 상태 표시는 앱 진단 화면 후보. ESC/TCS는 미확인 |

## 결론

| 항목 | 상태 | 앱 적용 |
| --- | --- | --- |
| 표준 OBD-II DTC 읽기 | Mode `03`, `07`, `0A`로 가능 | 1차 구현 |
| MIL/DTC 개수 | Mode `01 PID 01`로 가능 | HUD 상시 표시 가능 |
| A4CF2 자동변속기 DTC 표 | HD 서비스 매뉴얼에 표 있음 | HD 전용 보강 테이블에 포함 |
| 엔진 DTC 상세 조건 | AutoHex에 HD 코드별 페이지 존재 | 실제로 뜬 코드부터 보강 |
| ABS/EPS/SRS/BCM DTC | AutoHex에 일부 HD 코드별 페이지 존재 | 일반 OBD 앱으로는 제한, 제조사 진단 필요 |
| 전체 HD DTC DB | 공개 단일 파일/DBC처럼 확인된 자료 없음 | unknown code는 raw code로 표시 |

## 앱에서 읽을 명령

ELM327/iCar Pro 2S 기준 기본 명령:

```text
ATZ
ATE0
ATL0
ATS0
ATH1
ATSP0

0101
03
07
0A
```

| 명령 | 목적 | HUD 적용 |
| --- | --- | --- |
| `0101` | MIL 상태, DTC 개수, readiness | 상시 표시 |
| `03` | stored DTC | 진단 화면에서 수동 조회 |
| `07` | pending DTC | 진단 화면에서 수동 조회 |
| `0A` | permanent DTC | 지원 시 조회 |
| `04` | DTC 삭제 | 1차 구현에서는 넣지 않음 |

`0101` 응답의 첫 데이터 바이트 `A`:

```text
bit 7 = MIL on/off
bit 0..6 = stored emission-related DTC count
```

DTC 목록은 2바이트 단위로 파싱한다.

```text
43 01 33 00 00
=> 01 33
=> P0133
```

## DTC 종류

| Prefix | 영역 | 비고 |
| --- | --- | --- |
| `P0xxx` | 표준 powertrain | 일반 OBD-II 설명 매핑 가능 |
| `P1xxx` | 제조사 powertrain | 현대/HD 전용 설명 필요 |
| `P2xxx`, `P3xxx` | 표준 또는 제조사 powertrain | 코드별 확인 필요 |
| `Cxxxx` | chassis, ABS/EPS/ESC | 일반 OBD Mode 03에서 안 나올 수 있음 |
| `Bxxxx` | body, SRS/BCM | 제조사 진단 필요 가능성 큼 |
| `Uxxxx` | network/CAN 통신 | CAN/모듈 통신 문제 |

## 자동변속기 DTC

Elantra HD 서비스 매뉴얼의 A4CF2 troubleshooting 표 기준이다. 사용자 차량은 2010 Avante HD 1.6 자동으로 A4CF1 가능성이 높으므로, 실제 차량에서 TCM이 같은 코드를 쓰는지 검증한다. 그래도 range sensor, ATF temperature, turbine/output speed, solenoid, CAN communication 계열 코드는 앱 보강 테이블 시작점으로 유용하다.

| Code | 설명 | 한글 설명 | MIL |
| --- | --- | --- | --- |
| `P0605` | Internal Control Module ROM Error | TCM/제어모듈 ROM 오류 | O |
| `P0707` | Transmission Range Sensor Circuit Low Input | 변속 범위 센서 회로 낮은 입력 | O |
| `P0708` | Transmission Range Sensor Circuit High Input | 변속 범위 센서 회로 높은 입력 | O |
| `P0711` | Transmission Fluid Temperature Sensor A Range/Performance | ATF 온도 센서 범위/성능 이상 | O |
| `P0712` | Transmission Fluid Temperature Sensor A Low Input | ATF 온도 센서 낮은 입력 | O |
| `P0713` | Transmission Fluid Temperature Sensor A High Input | ATF 온도 센서 높은 입력 | O |
| `P0717` | Input/Turbine Speed Sensor A No Signal | 입력/터빈 속도 센서 신호 없음 | O |
| `P0721` | Output Speed Sensor Range/Performance | 출력 속도 센서 범위/성능 이상 | O |
| `P0722` | Output Speed Sensor No Signal | 출력 속도 센서 신호 없음 | O |
| `P0731` | Gear 1 Incorrect Ratio | 1단 기어비 불일치 | O |
| `P0732` | Gear 2 Incorrect Ratio | 2단 기어비 불일치 | O |
| `P0733` | Gear 3 Incorrect Ratio | 3단 기어비 불일치 | O |
| `P0734` | Gear 4 Incorrect Ratio | 4단 기어비 불일치 | O |
| `P0741` | Torque Converter Clutch Performance or Stuck Off | 토크컨버터 클러치 성능 이상/해제 고착 | O |
| `P0743` | Torque Converter Clutch Electrical | 토크컨버터 클러치 전기 회로 이상 | O |
| `P0748` | Pressure Control Solenoid Valve A Electrical | 압력 제어 솔레노이드 A 전기 회로 이상 | - |
| `P0750` | Shift Control Solenoid Valve A | 변속 제어 솔레노이드 A 이상 | O |
| `P0755` | Shift Control Solenoid Valve B | 변속 제어 솔레노이드 B 이상 | O |
| `P0760` | Shift Control Solenoid Valve C | 변속 제어 솔레노이드 C 이상 | O |
| `P0765` | Shift Control Solenoid Valve D | 변속 제어 솔레노이드 D 이상 | O |
| `P0880` | TCM Power Signal Error | TCM 전원 신호 오류 | O |
| `U0001` | High Speed CAN Communication Bus Off | 고속 CAN bus off | O |
| `U0100` | Lost Communication With ECM/PCM A | ECM/PCM 통신 끊김 | O |

서비스 매뉴얼은 A4CF2 TCM RAM에 최대 10개 DTC가 발생 순서대로 저장되고, 10개를 넘으면 오래된 코드부터 지워진다고 설명한다. 배터리를 분리하면 저장 코드가 지워질 수 있으므로, 앱은 가능하면 정비 전에 코드를 먼저 읽어 저장한다.

## HD에서 자주 확인할 가치가 있는 코드

아래는 HD 자료에서 직접 확인했거나, HD TSB/AutoHex 코드별 페이지가 존재하는 항목이다. 전체 목록은 아니며 앱의 보강 테이블 시작점으로 쓴다.

| Code | 영역 | 의미 | 앱 처리 |
| --- | --- | --- | --- |
| `P0300` | engine | 랜덤/다중 실화 | 중요 경고 |
| `P0301`-`P0304` | engine | 1-4번 실린더 실화 | 중요 경고 |
| `P0420` | engine | 촉매 효율 저하 Bank 1 | 정비 필요 |
| `P0507` | engine | idle rpm higher than expected | 정비 필요 |
| `P0561` | engine/power | system voltage unstable | 전압 경고와 연동 |
| `P0700` | transmission | TCM이 ECM에 MIL 점등 요청 | TCM 별도 조회 필요 |
| `P0750` | transmission | shift solenoid A 회로 이상 | 변속기 경고 |
| `P0880` | transmission | TCM power signal error | 변속기 경고 |
| `U0100` | network | ECU CAN timeout | 통신/CAN 경고 |
| `U0001` | network | high speed CAN bus off | 통신/CAN 경고 |
| `C1611` | ABS/ESC | CAN time-out EMS | ABS/ESC 제조사 진단 |
| `C1617` | EPS | CAN invalid value, vehicle speed signal | EPS 제조사 진단 |
| `C1702` | ABS/ESC | variant coding | ABS/ESC 제조사 진단 |
| `C1704` | EPS | ECU failsafe relay fault | EPS 제조사 진단 |
| `B1328` | SRS | driver front impact sensor defect | SRS 진단기 필요 |
| `B1333` | SRS | passenger front impact sensor defect | SRS 진단기 필요 |

## 앱 데이터 모델

1차 구현은 코드를 모두 “고장 내용 확정”처럼 보이지 않게 한다. 사용자에게는 코드, 상태, 설명 출처를 같이 보여준다.

```json
{
  "type": "dtc_snapshot",
  "mil": true,
  "dtc_count": 2,
  "stored": [
    {
      "code": "P0700",
      "status": "stored",
      "scope": "transmission-request",
      "descriptionKo": "TCM이 ECM에 MIL 점등을 요청함. 실제 변속기 코드는 TCM에서 별도 조회 필요.",
      "source": "avante-hd-local"
    }
  ],
  "pending": [],
  "permanent": []
}
```

## 구현 방침

- HUD 상시 화면에는 `MIL`, `DTC count`, `전압` 정도만 표시한다.
- 진단 화면에서만 `03`, `07`, `0A`를 요청한다.
- `P0700`이 뜨면 “변속기 코드 별도 조회 필요”로 표시한다. `P0700` 자체가 실제 원인 코드는 아니다.
- `C`, `B`, `U` 코드는 일반 OBD 조회에서 안 나올 수 있으므로 “제조사 진단 필요”로 표시한다.
- `04` clear DTC는 기본 UI에 넣지 않는다. 나중에 넣더라도 길게 누르기와 확인창이 필요하다.
- 설명 없는 코드는 raw code만 보여주고, 사용자가 앱 로그를 내보내면 보강 테이블에 추가한다.

## Sources

- Hyundai Elantra HD A4CF2 troubleshooting DTC table: <https://www.hemanual.org/troubleshooting_a4cf2_-2507.html>
- Hyundai Elantra HD engine control OBD-II description: <https://www.hemanual.org/description_and_operation-2403.html>
- AutoHex Hyundai ELANTRA(HD) 2010 P0700: <https://www.autohex.net/dtc-help/hyundai/61/2010/12055/P0700/>
- AutoHex Hyundai ELANTRA(HD) 2010 U0100: <https://www.autohex.net/dtc-help/hyundai/61/2010/12055/U0100/>
- AutoHex Hyundai ELANTRA(HD) 2007 C1611: <https://www.autohex.net/dtc-help/hyundai/61/2007/12055/C1611/>
- AutoHex Hyundai ELANTRA(HD) 2010 P0507: <https://www.autohex.net/dtc-help/hyundai/61/2010/12055/P0507/>
- AutoHex Hyundai ELANTRA(HD) 2008 P0420: <https://www.autohex.net/dtc-help/hyundai/61/2008/12055/P0420/>
- AutoHex Hyundai ELANTRA(HD) 2010 B1328: <https://www.autohex.net/dtc-help/hyundai/61/2010/12055/B1328/>
- AutoHex Hyundai ELANTRA(HD) 2010 B1333: <https://www.autohex.net/dtc-help/hyundai/61/2010/12055/B1333/>
- Operation CHARM / Hyundai TSB 11-FL-002-1, 2007-2010 Elantra HD misfire DTC P0300-P0304: <https://charm.li/Hyundai/2008/Elantra%20L4-2.0L/Repair%20and%20Diagnosis/Technical%20Service%20Bulletins/Customer%20Interest/Fuel%20System%20-%20MIL%20ON%2FMisfire%20DTC%27s%20After%20Long%20Storage/>
