# Headunit Revived ESP32 HUD

[English](README.md) | [한국어](README.ko.md)

Headunit Revived의 내비게이션 안내를 별도 HUD에 표시하는 companion stack입니다.

이 프로젝트는 Headunit Revived를 포크하지 않는 실험적 companion stack입니다. 현재 주 대상은 Raspberry Pi 4B + 1920x480 HDMI 보조 디스플레이이며, Pi가 iCar/ELM327 OBD와 CANable/SocketCAN으로 확정된 런타임 차량값을 직접 읽고 화면도 직접 렌더링합니다. Raw OBD/CAN 조사와 live simulation은 Pi에 적용하기 전에 Windows Electron 레이아웃 에디터에서 처리합니다. Android 앱은 같은 네트워크에 있을 때 Headunit Revived 내비게이션 정보와 태블릿/GPS backup speed만 UDP로 보냅니다.

ESP32 dual-OLED HUD 경로도 저장소에 남아 있으며, BLE provisioning과 UDP packet 렌더링을 계속 지원합니다. Raspberry Pi 기준 구조는 [Raspberry Pi HUD 런타임 가이드](docs/pi-hud-runtime.ko.md)를 참고하세요.

## 프로젝트 상태

- 주 하드웨어 대상: Raspberry Pi 4B 4GB, CANable, iCar Pro 2S/ELM327.
- 주 디스플레이 대상: 8.8 inch급 1920x480 HDMI IPS 보조 디스플레이.
- Android 대상: Headunit Revived와 이 브리지 앱이 설치된 태블릿. Pi 경로에서는 내비 정보와 backup speed만 보냅니다.
- 레이아웃: Windows exe 에디터에서 1920x480 JSON 레이아웃을 저장하고 Pi가 그대로 렌더링합니다. 속도/RPM 같은 값은 digital, bar, analog, needle, sport gauge 스타일과 최대값을 지정할 수 있습니다.
- Legacy 대상: ESP32-S3-N16R8 + 128x64 I2C OLED 2개.
- 전송 방식: Pi 런타임 차량 정보는 로컬 OBD/CAN, Windows 분석/시뮬레이션은 OBD BLE와 CANable SLCAN, Android 내비 보강은 UDP. ESP32 초기 Wi-Fi 설정은 BLE.
- 안정성: active prototype. 패킷 필드는 추가 방식으로 확장하며 backward compatibility를 유지합니다.

## 저장소 구조

| 경로 | 역할 |
| --- | --- |
| `android-app/` | Headunit Revived 브로드캐스트 수신, ESP32 BLE provisioning, Wi-Fi discovery, 실시간 HUD 패킷 전송을 담당하는 Kotlin Android 앱. |
| `bridge-core/` | 패킷, 상태, 타이밍, 매핑 로직을 담은 순수 Kotlin 모듈과 unit test. |
| `esp32-hud/` | ESP32-S3용 PlatformIO 펌웨어. BLE provisioning, Wi-Fi reconnect, UDP discovery, packet parsing, OLED rendering을 담당합니다. |
| `pi-hud/` | Raspberry Pi 4B + HDMI 보조 디스플레이용 1920x480 HUD 런타임. OBD/CAN 로컬 입력과 Android 내비 UDP 입력을 병합합니다. |
| `layout-editor-electron/` | 1920x480 HUD JSON 레이아웃을 편집하는 현대식 Electron 에디터. Pi pygame 렌더러를 재사용해 preview가 런타임과 맞고, Windows OBD/CAN 연결, 시뮬레이션, 분석 도구를 제공합니다. |
| `layouts/` | Pi HUD와 레이아웃 에디터가 공유하는 화면 JSON. |
| `vehicles/` | 레이아웃 에디터에서 선택 가능한 차종 프로필 JSON. 선택한 프로필은 저장 레이아웃에 함께 embed됩니다. |
| `docs/setup.md` | Android, ESP32, OLED wiring, network troubleshooting 설정 가이드. |
| `docs/protocol.md` | broadcast, BLE provisioning, UDP HUD packet, discovery, settings, speed packet wire protocol reference. |

## 동작 흐름

1. Pi가 1920x480 HDMI 화면을 열고 레이아웃 JSON을 렌더링합니다.
2. Windows 에디터가 OBD BLE와 CANable USB/SLCAN에 연결해 live 값을 시뮬레이션하고, CAN/OBD traffic을 분석하며, 확정된 profile mapping을 저장합니다.
3. Pi가 iCar/ELM327에서 표준 OBD PID를 읽고, CANable/SocketCAN에서 확정된 CAN 신호만 decode합니다.
4. Pi가 UDP port `4211`에서 Android bridge discovery에 `device_kind=pi_hud`로 응답합니다.
5. Headunit Revived가 태블릿에서 내비게이션 브로드캐스트를 발행합니다.
6. 브리지 앱이 브로드캐스트를 compact JSON HUD packet으로 변환합니다.
7. 브리지 앱은 Pi target에 navigation packet과 `type=speed` backup speed만 보냅니다.
8. Pi는 port `4210`에서 UDP packet을 받고, stale sequence number를 무시한 뒤 로컬 차량 데이터와 병합해 HUD를 렌더링합니다.

HUD packet은 fire-and-forget 방식입니다. HUD receiver는 실시간 내비게이션 패킷에 ACK를 보내지 않으므로, 지연된 return traffic이 현재 안내를 늦추지 않습니다.

## 스크린샷

| Android bridge dashboard | ESP32 OLED HUD |
| --- | --- |
| [![Android bridge dashboard](docs/assets/bridge-screen.png)](docs/assets/bridge-screen.png) | [![ESP32 OLED HUD](docs/assets/hud.png)](docs/assets/hud.png) |

이미지를 누르면 원본 크기로 열 수 있습니다.

## 빠른 시작

Android 쪽 build/test:

```powershell
.\gradlew.bat :bridge-core:test :android-app:testDebugUnitTest :android-app:assembleDebug --warning-mode all
```

Pi HUD와 레이아웃 검증:

```powershell
$env:PYTHONPATH=(Resolve-Path 'pi-hud').Path
.\pi-hud\.venv\Scripts\python.exe -m unittest discover -s pi-hud\tests
.\pi-hud\.venv\Scripts\python.exe pi-hud\scripts\verify-layout.py layouts\avante_hd_2010_default.json --width 1920 --height 480
```

Electron 레이아웃 에디터 실행/패키징:

```powershell
cd layout-editor-electron
npm install
npm test
npm start
npm run build
```

Windows 레이아웃 에디터에서 저장한 JSON은 Pi에 올리기 전에 handoff 해시까지 확인할 수 있습니다.

```powershell
.\pi-hud\.venv\Scripts\python.exe pi-hud\scripts\verify-layout.py path\to\saved-layout.json --width 1920 --height 480 --require-handoff
```

Pi로 옮길 레이아웃/차량 프로필/경고등 PNG/환경 예제를 묶는 현장 패키지:

```powershell
.\pi-hud\.venv\Scripts\python.exe pi-hud\scripts\build-field-pack.py --output field-pack\headunit-pi-field-pack.zip
```

Electron 레이아웃 에디터의 `Field Pack` 버튼도 같은 형식의 zip을 만든다. 에디터 preview에서는 경고등 배치를 위해 아이콘이 항상 보이고, Pi 런타임에서는 해당 `warnings.*` 값이 true일 때만 표시된다.

ESP32 firmware build:

```powershell
platformio run -d esp32-hud -e esp32-s3-n16r8
```

ESP32 firmware flash:

```powershell
platformio run -d esp32-hud -e esp32-s3-n16r8 -t upload
```

Android APK build에는 `ANDROID_HOME` 또는 `local.properties`로 설정된 Android SDK가 필요합니다. ESP32 build에는 PlatformIO가 필요합니다.

## 하드웨어 메모

기본 OLED driver는 SH1106입니다. SSD1306-compatible로 판매되는 많은 1.3 inch 128x64 모듈이 실제로는 SH1106 controller를 사용하기 때문입니다. 핀, address, driver가 다른 경우 `esp32-hud/include/config.h`에서 display configuration을 override하세요.

기본 display role:

| Display | Role | Default bus |
| --- | --- | --- |
| 1 | Speed and safety face | GPIO 8/9, `0x3C` |
| 2 | Navigation face | GPIO 10/11, `0x3C` |

## 문서

- Setup guide: [English](docs/setup.md) | [한국어](docs/setup.ko.md)
- Protocol reference: [English](docs/protocol.md) | [한국어](docs/protocol.ko.md)
- Headunit Revived patch guide: [한국어](docs/headunit-revived-patch.ko.md)
- Raspberry Pi HUD quick start: [한국어](docs/pi-hud-quick-start.ko.md)
- Raspberry Pi HUD runtime guide: [한국어](docs/pi-hud-runtime.ko.md)

## 기여

이슈와 pull request는 환영합니다. 이 프로젝트에서 좋은 기여는 보통 다음을 포함합니다.

- 명확한 hardware/software setup 설명,
- runtime 문제에 대한 log 또는 screenshot,
- bridge logic 변경에 대한 Android unit test,
- firmware 변경에 대한 PlatformIO compile verification,
- packet field가 바뀔 때 protocol documentation update.

secret은 commit하지 마세요. Wi-Fi SSID, password, local SDK path, signing key, device-specific private IP address를 저장소에 넣지 않습니다.

## 라이선스

아직 license file이 선택되지 않았습니다. license가 추가되기 전까지는 코드를 review와 collaboration을 위한 source-available 상태로 보고, 광범위한 재배포 라이선스가 부여된 것으로 간주하지 마세요.
