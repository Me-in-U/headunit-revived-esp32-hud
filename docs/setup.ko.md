# 설정 가이드

[English](setup.md) | [한국어](setup.ko.md) | [프로젝트 README](../README.ko.md)

이 문서는 Headunit Revived ESP32 HUD 브리지를 Android 태블릿, ESP32 firmware, OLED wiring, Wi-Fi 경로까지 한 번에 설정하기 위한 가이드입니다.

## 준비물

- Headunit Revived GitHub build가 설치된 Android 태블릿.
- 이 저장소에서 빌드한 HUD Bridge Android 앱.
- ESP32-S3-N16R8 계열 보드.
- 128x64 I2C OLED display 2개.
- 태블릿과 ESP32 간 UDP 통신을 허용하는 phone hotspot 또는 Wi-Fi network.
- Android 앱 빌드를 위한 Android SDK.
- ESP32 빌드를 위한 PlatformIO.

## Android 태블릿 설정

1. 태블릿에 Headunit Revived를 설치합니다.
2. HUD Bridge Android 앱을 설치합니다.
3. 태블릿을 ESP32가 사용할 같은 phone hotspot 또는 Wi-Fi network에 연결합니다.
4. HUD Bridge를 열고 `권한 / 백그라운드` 카드에 표시되는 권한을 허용합니다.
5. `핫스팟 Wi-Fi`에서 필요하면 `수정`을 누르고 hotspot SSID/password를 입력합니다.
6. `BLE로 ESP 연결`을 눌러 Bluetooth LE로 ESP32를 provision합니다.
7. Headunit Revived에서 Android Auto projection을 시작합니다.
8. 휴대폰 내비게이션 앱에서 route guidance를 시작합니다.

앱은 Android Auto projection 또는 첫 navigation update가 들어오기 전까지 자동 ESP32 Wi-Fi discovery를 시작하지 않습니다. 수동 discovery는 `Wi-Fi 검색`으로 언제든 실행할 수 있습니다.

## ESP32 Firmware 설정

Firmware build:

```powershell
platformio run -d esp32-hud -e esp32-s3-n16r8
```

Firmware flash:

```powershell
platformio run -d esp32-hud -e esp32-s3-n16r8 -t upload
```

Serial monitor를 `115200`으로 열고 다음을 확인합니다.

1. BLE provisioning advertising이 시작됩니다.
2. ESP32가 Android 앱에서 Wi-Fi credentials를 받습니다.
3. ESP32가 Wi-Fi IP address를 출력합니다.
4. BLE status에 `{"s":"c","i":"10.233.116.145"}` 같은 compact connected payload가 포함됩니다.
5. Android test packet 전송 또는 Headunit Revived navigation update 시 UDP packet log가 출력됩니다.

Native USB로 flash한 뒤 serial log가 보이지 않으면 보드를 다시 연결하거나 reset을 누르세요. Firmware는 `ARDUINO_USB_CDC_ON_BOOT=1`로 USB CDC on boot를 활성화합니다.

`esp32-hud/include/config.h`는 optional입니다. `HUD_WIFI_SSID`와 `HUD_WIFI_PASSWORD`를 정의하면 flash 후 ESP32가 자동 연결할 수 있습니다. 일반 사용에서는 credentials가 저장소에 들어가지 않도록 BLE provisioning을 권장합니다.

## OLED Wiring

Firmware는 1.3 inch 128x64 I2C OLED 2개를 대상으로 합니다. 기본 driver는 SH1106입니다. SSD1306-compatible로 판매되는 1.3 inch 모듈 중 실제 controller가 SH1106인 경우가 많기 때문입니다.

Display 1 wiring:

| OLED Pin | ESP32-S3 Pin |
| --- | --- |
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 8 |
| SCL | GPIO 9 |

Display 2 wiring:

| OLED Pin | ESP32-S3 Pin |
| --- | --- |
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 10 |
| SCL | GPIO 11 |

기본 display configuration:

```c
#define HUD_OLED_SDA 8
#define HUD_OLED_SCL 9
#define HUD_OLED_ADDRESS 0x3C
#define HUD_OLED_WIDTH 128
#define HUD_OLED_HEIGHT 64
#define HUD_OLED_RESET -1
#define HUD_OLED_DRIVER 1106

#define HUD_OLED2_ENABLED 1
#define HUD_OLED2_SDA 10
#define HUD_OLED2_SCL 11
#define HUD_OLED2_ADDRESS 0x3C
#define HUD_OLED2_RESET -1
```

화면이 켜지지 않으면 먼저 address `0x3D`를 시도하고, 실제 SDA/SCL pin과 전원을 확인하세요. SSD1306 module이 확실한데 표시가 이상하면 `HUD_OLED_DRIVER`를 `1306`으로 설정합니다. 값은 `esp32-hud/include/config.h`에서 override합니다.

물리 배치는 `[1] [2]`입니다.

| Display | Role |
| --- | --- |
| 1 | Speed and safety face |
| 2 | Maneuver icon, next maneuver distance, selected road name |

고정 Korean status label은 1-bit bitmap glyph로 렌더링합니다. Route road name은 Android가 compact 1-bit road bitmap으로 만들어 보내므로 ESP32에 전체 Korean font를 넣지 않아도 됩니다.

## Network Behavior

BLE provisioning 이후 Android는 ESP32 target port `4210`으로 UDP packet을 직접 보냅니다. Broadcast packet은 ESP32 IP를 모를 때만 사용합니다.

Discovery는 UDP port `4211`을 사용합니다.

- Android는 broadcast target과 저장된 ESP32 target으로 discovery probe를 보냅니다.
- ESP32는 probe에 응답하고 hello packet을 주기적으로 broadcast합니다.
- Android는 packet source address를 target host로 저장합니다.

Foreground bridge service도 Android Auto가 active일 때 recovery를 수행합니다. ESP32 target이 없으면 10초에서 60초까지 backoff하며 discovery를 재시도합니다. ESP32도 boot failure 또는 Wi-Fi loss 이후 저장된 credentials로 5초에서 60초까지 backoff하며 재연결합니다.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| BLE provisioning은 되지만 Wi-Fi discovery가 실패함 | 일부 phone hotspot은 client-to-client traffic을 차단합니다. ESP32 AP mode, USB tethering, 별도 travel router를 시도하세요. |
| Android target이 비어 있거나 stale함 | `ESP32 대상` 카드에서 `Wi-Fi 검색`을 누르세요. |
| ESP32에 IP가 있지만 packet을 받지 못함 | 태블릿과 ESP32가 같은 routable network에 있고 UDP port `4210`이 도달 가능한지 확인하세요. |
| OLED가 blank임 | I2C address, SDA/SCL pin, power, `HUD_OLED_DRIVER`를 확인하세요. |
| Android가 background에서 갱신을 멈춤 | `백그라운드 허용`으로 battery optimization exemption을 허용하세요. |

## Verification Checklist

Pull request를 열거나 build를 공유하기 전에 다음을 실행하세요.

```powershell
.\gradlew.bat :bridge-core:test :android-app:testDebugUnitTest :android-app:assembleDebug --warning-mode all
platformio run -d esp32-hud -e esp32-s3-n16r8
```
