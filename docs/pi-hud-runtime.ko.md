# Raspberry Pi HUD 런타임 가이드

이 문서는 1920x480 HDMI 보조 디스플레이를 Raspberry Pi 4B에서 직접 구동하는 HUD 버전의 기준 구조를 정리한다.

## 기준 방향

Pi가 메인 HUD 컴퓨터다. Android 브릿지 앱은 있어도 되고 없어도 되는 내비게이션 입력으로만 취급한다.

| 입력 | 담당 장치 | 없을 때 동작 |
| --- | --- | --- |
| OBD 표준 PID | Raspberry Pi + ELM327/iCar Pro 2S | OBD 상태를 stale/error로 표시하고 dummy 또는 CAN 값 유지 |
| CAN raw frame | Raspberry Pi + CANable(SocketCAN) | CAN 상태를 stale/error로 표시 |
| Android 내비 | Android bridge UDP | 내비 영역만 disconnected/stale 표시 |
| 화면 렌더링 | Raspberry Pi HDMI | 계속 표시 |

이 구조가 맞는 이유는 차량 기본 정보가 Android 브릿지에 의존하면 안 되기 때문이다. 브릿지 앱이 꺼지거나, 태블릿이 없거나, 핫스팟에서 UDP가 막혀도 속도, RPM, 냉각수, 전압, 경고등, DTC 같은 로컬 차량 정보는 계속 보여야 한다.

## 권장 하드웨어

| 용도 | 권장 |
| --- | --- |
| HUD 컴퓨터 | Raspberry Pi 4B 4GB |
| 화면 | 8.8 inch 1920x480 HDMI IPS 모듈 |
| OBD 표준 PID | Vgate iCar Pro 2S 또는 ELM327 계열 |
| CAN raw sniffing | CANable 호환 보드, candleLight 펌웨어, SocketCAN |
| OBD 분기 | OBD2 male-to-female splitter 또는 연장 케이블에서 6/14, 4/5, 16 분기 |

CANable은 OBD 포트의 표준 CAN-H/CAN-L인 6번/14번을 먼저 본다. 사용자가 확인한 DLC pin 구성에서는 6/14가 존재하고 11번은 없으므로, Qvia 문서류에서 보이는 3/11 C-CAN 후보는 이 차량의 1차 대상에서 제외한다.

## 데이터 우선순위

1. Pi 로컬 OBD/CAN에서 확실히 읽히는 값을 HUD 주 데이터로 쓴다.
2. Android bridge의 GPS speed는 `speed_kmh_backup`으로만 둔다.
3. Android bridge의 Headunit Revived 내비 정보는 `nav.*`에만 반영한다.
4. 값이 일정 시간 갱신되지 않으면 stale로 표시한다. Android speed backup freshness와 navigation freshness는 분리해서, speed packet만 계속 들어와도 내비 연결 상태를 살려두지 않는다. Android가 `active=false` 내비 packet을 보내면 Pi는 이전 안내 문구/도로명/거리 값을 지워서 stale route guidance가 화면에 남지 않게 한다.
5. 아반떼 HD 전용 CAN decode가 확정되기 전에는 raw frame count와 last CAN ID만 표시한다.

현재 ELM327/iCar 입력은 표준 OBD PID로 RPM(`010C`), speed(`010D`), coolant(`0105`), control module voltage(`0142`), MIL/DTC count(`0101`)를 읽는다. 전압은 `0142`가 응답하지 않으면 ELM adapter voltage 명령인 `ATRV`를 fallback으로 사용한다. DTC는 Mode 03(stored), Mode 07(pending), Mode 0A(permanent)를 5초 간격으로 polling해서 `dtc.stored`, `dtc.pending`, `dtc.permanent`에 넣는다.

현재 CANable/SocketCAN 입력은 차종별 decode가 확정되기 전 단계이므로 `vehicle.can_state`, `debug.can_frame_count`, `debug.last_can_id`를 먼저 제공한다. 기본 레이아웃에는 CAN 상태가 표시되고, 레이아웃 에디터의 Diagnostics 탭에서 CAN frame count, last CAN ID, OBD request/response debug text를 추가할 수 있다.

차종별 raw CAN 매핑은 선택 차량 profile의 `can_signals` 배열에서 읽는다. 각 signal은 `confirmed:true`, `frame_id`, `name`, `start_byte`가 있어야 Pi runtime에서 decode 대상이 된다. Byte 단위 값은 `length`를 쓰고, warning lamp나 switch처럼 bit flag인 값은 `start_bit`과 `bit_length`를 쓴다. Bit 번호는 해당 byte의 LSB를 `0`으로 보는 방식이다. `value_map`이 있으면 raw 정수값을 문자열/상태값으로 치환하고, 없으면 `raw * scale + offset`을 `name` 경로에 저장한다. 예를 들어 `name:"vehicle.gear_actual"`은 HUD state의 `vehicle.gear_actual`로, `name:"warnings.abs"`는 `warnings.abs`로 들어간다. 아반떼 HD 기본 profile은 아직 실차에서 확정한 raw CAN ID가 없으므로 `can_signals: []`로 둔다.

Byte 값 예:

```json
{
  "confirmed": true,
  "frame_id": "0x316",
  "name": "vehicle.pedal_percent",
  "start_byte": 2,
  "length": 1,
  "scale": 0.5
}
```

Bit flag 예:

```json
{
  "confirmed": true,
  "frame_id": "0x420",
  "name": "warnings.abs",
  "start_byte": 0,
  "start_bit": 2,
  "bit_length": 1,
  "value_map": {"0": false, "1": true}
}
```

## 현재 구현 경로

| 경로 | 역할 |
| --- | --- |
| `pi-hud/` | Raspberry Pi에서 실행하는 pygame HUD 렌더러 |
| `layout-editor-electron/` | Windows용 Electron 레이아웃 에디터 |
| `layouts/avante_hd_2010_default.json` | 1920x480 기본 레이아웃, 차량 선택, dummy data, element 정의 |
| `vehicles/avante_hd_2010_1_6_at.json` | 아반떼 HD 2010 1.6 AT 확정값 차종 프로필 |

## Pi 실행 예시

개발용 dummy 실행:

```bash
cd pi-hud
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py --windowed --dummy
```

실차 입력 포함:

```bash
python run.py --obd-port /dev/rfcomm0 --can-channel can0
```

Windows 레이아웃 에디터에서 저장한 JSON만 현장 런타임에서 허용하려면 handoff 검증을 켠다.

```bash
python run.py --require-layout-handoff --obd-port /dev/rfcomm0 --can-channel can0
```

Pi 런타임은 기본적으로 Android 브릿지의 UDP discovery port `4211`에 응답한다. 따라서 Android 브릿지와 Pi가 같은 네트워크에 있으면 ESP32 HUD처럼 `headunit_hud_discover` probe에 `headunit_hud_hello`를 반환하고, 브릿지는 Pi의 HUD UDP port `4210`으로 내비 패킷을 보낼 수 있다. Pi hello에는 `device_kind:"pi_hud"`가 들어가므로 Android는 이 target에 ESP32 전용 settings packet을 보내지 않고 navigation packet과 backup speed packet만 보낸다.

실사용 기본값에서 Pi UDP 수신단은 Android bridge의 navigation packet과 `type=speed` backup speed만 반영한다. 알 수 없는 `type` 값은 navigation으로 해석하지 않고 무시하므로 잘못된 UDP packet이 이전 안내/차량 상태를 덮지 못한다. `vehicle_status`, `dtc_snapshot`, `vehicle_debug` 같은 원격 차량/진단 packet도 로컬 OBD/CAN 값을 대체하지 못하게 무시한다. 레이아웃 디버깅이나 실차 조사 때문에 DTC/debug UDP를 임시로 받아야 할 때만 다음처럼 명시적으로 연다.

```bash
python run.py --allow-diagnostic-udp
```

브릿지 discovery 응답을 끄고 싶을 때:

```bash
python run.py --disable-discovery
```

## 현장 전달용 패키지

개발 PC에서 레이아웃을 수정한 뒤 Pi로 옮길 파일만 zip으로 묶을 수 있다.

```bash
python pi-hud/scripts/build-field-pack.py --output field-pack/headunit-pi-field-pack.zip
```

이 스크립트는 기본 레이아웃을 1920x480 Pi 렌더러로 먼저 검증하고, `HEADUNIT_HUD_REQUIRE_HANDOFF=1`에서 쓸 수 있도록 `pi_hud_handoff` 해시도 확인한다. zip에는 다음 파일이 들어간다.

| zip 경로 | 용도 |
| --- | --- |
| `layouts/avante_hd_2010_default.json` | Pi가 실제로 렌더링할 레이아웃 |
| `vehicles/*.json` | 레이아웃 에디터와 향후 차종 선택용 차량 프로필 |
| `pi-hud/assets/warning-icons/*.png` | 경고등 개별 요소가 사용하는 투명 PNG 아이콘 |
| `config/pi-hud.env.example` | `/etc/headunit-pi-hud.env`로 복사할 환경 예제 |
| `preview/layout-preview.png` | Pi 렌더러로 생성한 1920x480 full-resolution 미리보기 |
| `manifest.json` | 레이아웃/차량/아이콘/환경 예제의 SHA-256, 선택 차량, render 검증 결과 |
| `README-pi-field-pack.txt` | Pi에서 복사할 명령 요약 |

Pi에 런타임이 이미 설치되어 있으면 패키지를 Pi로 복사한 뒤 manifest 해시를 검증하며 적용한다.

```bash
/opt/headunit-pi-hud/.venv/bin/python \
  /opt/headunit-pi-hud/pi-hud/scripts/apply-field-pack.py \
  headunit-pi-field-pack.zip
sudo systemctl restart headunit-pi-hud.service
```

`apply-field-pack.py`는 `manifest.json`의 SHA-256과 zip 내부 파일을 먼저 비교하고, layout payload를 Pi 렌더러로 다시 열어 non-blank/handoff 검증까지 통과한 뒤 `layouts/`, `vehicles/`, `pi-hud/assets/warning-icons/`를 설치 위치에 쓴다. 기존 `/etc/headunit-pi-hud.env`가 있으면 기본적으로 보존한다. 새 예제로 env를 다시 만들 때만 다음 옵션을 붙인다.

```bash
sudo /opt/headunit-pi-hud/.venv/bin/python \
  /opt/headunit-pi-hud/pi-hud/scripts/apply-field-pack.py \
  headunit-pi-field-pack.zip \
  --overwrite-env
```

이미 `/etc/headunit-pi-hud.env`에 iCar MAC, BLE UUID, CANable channel 등을 맞춰둔 상태라면 `--overwrite-env`를 쓰지 말고 새 예제와 필요한 항목만 병합한다.

CANable을 SocketCAN으로 올리는 예:

```bash
chmod +x pi-hud/scripts/canable-up.sh
pi-hud/scripts/canable-up.sh can0 500000 on
python run.py --can-channel can0
```

세 번째 인자 `on`은 SocketCAN `listen-only` 모드다. CAN bitrate는 실차에서 먼저 확인해야 한다. 현대/기아 OBD 진단 CAN은 보통 500 kbit/s 후보부터 확인한다.

iCar Pro 2S가 Classic Bluetooth SPP로 잡히는 경우:

```bash
chmod +x pi-hud/scripts/icar-rfcomm-bind.sh
pi-hud/scripts/icar-rfcomm-bind.sh AA:BB:CC:DD:EE:FF
python run.py --obd-port /dev/rfcomm0 --can-channel can0
```

iCar Pro 2S가 BLE 전용으로만 잡히면 rfcomm 방식이 안 된다. 이 경우에는 BLE MAC과 GATT characteristic UUID를 지정해서 Pi 런타임의 BLE ELM327 경로를 쓴다. UUID 확인이 번거롭거나 연결이 불안정하면 USB ELM327/OBDLink SX 같은 serial OBD 어댑터가 더 단순하다.

BLE ELM327/iCar 경로를 직접 시도할 때:

```bash
python run.py \
  --obd-ble-mac AA:BB:CC:DD:EE:FF \
  --obd-ble-rx-uuid 0000fff1-0000-1000-8000-00805f9b34fb \
  --obd-ble-tx-uuid 0000fff2-0000-1000-8000-00805f9b34fb \
  --can-channel can0
```

여기서 RX UUID는 어댑터가 Pi로 응답을 notify하는 characteristic이고, TX UUID는 Pi가 `010C`, `010D` 같은 ELM 명령을 write하는 characteristic이다. iCar Pro 2S의 실제 UUID는 제품/펌웨어에 따라 다를 수 있으므로 Pi에서 BLE scan 또는 nRF Connect류 앱으로 확인한 값을 넣는다. `/dev/rfcomm0`처럼 serial endpoint가 이미 안정적으로 잡히면 BLE보다 serial/rfcomm 경로가 단순하다.

## Pi 설치와 자동 실행

Raspberry Pi에 repo를 받은 뒤 설치 스크립트를 실행한다.

```bash
sudo pi-hud/scripts/install-pi.sh
```

기본 설치 위치는 `/opt/headunit-pi-hud`이고, systemd unit은 `/etc/systemd/system/headunit-pi-hud.service`, 환경파일은 `/etc/headunit-pi-hud.env`에 들어간다. 다른 설치 위치를 쓰려면 첫 번째 인자로 넘긴다.

```bash
sudo pi-hud/scripts/install-pi.sh /opt/headunit-pi-hud
```

설치 스크립트는 `/etc/headunit-pi-hud.env`를 만들고, 가능한 경우 iCar/ELM327와 CANable을 한 번 자동 탐색해서 설정값을 채운다. systemd unit은 Raspberry Pi OS Lite에서도 부팅 경로에 걸리도록 `multi-user.target`에 enable된다. 설치 스크립트는 기본적으로 `sudo`를 실행한 사용자를 service user로 쓰며, 직접 지정하려면 `sudo HEADUNIT_HUD_USER=<pi-login-user> pi-hud/scripts/install-pi.sh`처럼 실행한다. 설치 중 자동 탐색을 건너뛰려면 `sudo HEADUNIT_HUD_SKIP_AUTO_CONFIG=1 pi-hud/scripts/install-pi.sh`처럼 실행한다.

장비를 나중에 꽂았거나 Bluetooth scan이 늦게 잡혔으면 Pi에서 자동 탐색을 다시 실행한다.

```bash
sudo /opt/headunit-pi-hud/.venv/bin/python \
  /opt/headunit-pi-hud/pi-hud/scripts/auto-configure-hardware.py \
  --apply
```

자동 탐색이 성공하면 `/etc/headunit-pi-hud.env`에 아래 값들이 채워진다.

```bash
HEADUNIT_HUD_OBD_PORT=/dev/rfcomm0
HEADUNIT_HUD_ICAR_MAC=AA:BB:CC:DD:EE:FF
HEADUNIT_HUD_CAN_CHANNEL=can0
HEADUNIT_HUD_CAN_BITRATE=500000
HEADUNIT_HUD_CAN_LISTEN_ONLY=on
```

자동 탐색은 Bluetooth 장치 이름에 `iCar`, `OBD`, `ELM327`, `V-LINK`, `Vgate` 같은 단어가 있는 후보가 정확히 하나일 때만 iCar/ELM327로 채택한다. rfcomm probe가 실패하면 BLE GATT characteristic을 검사해서 RX/TX UUID를 찾고, `ATI`, `0100` probe가 통과하면 BLE 설정을 저장한다. CANable은 `ip link`에서 `can0` 같은 SocketCAN interface를 찾고 500 kbit/s listen-only로 올린 뒤 수신 probe를 시도한다.

자동 업데이트는 기본으로 켜져 있다.

```bash
HEADUNIT_HUD_AUTO_UPDATE=1
```

`headunit-pi-hud-update.timer`가 주기적으로 git fast-forward update를 확인하고, requirements를 다시 설치한 뒤 HUD 서비스를 재시작한다. 자동 업데이트를 끄려면 `/etc/headunit-pi-hud.env`에서 `HEADUNIT_HUD_AUTO_UPDATE=0`으로 바꾼다.

OBD 또는 CAN 장치가 아직 없으면 해당 값을 비워도 Pi HUD는 실행된다. 단, 둘 다 비어 있으면 dummy source가 들어와 개발용 화면처럼 보인다. OBD/CAN 값을 설정한 직후의 초기 상태는 `configured`로 표시되며, 실제 응답을 받으면 각 source가 `live`로 바뀐다. 따라서 `configured`는 장치 경로가 설정됐다는 뜻이지 실차 값 수신 완료라는 뜻은 아니다. Dummy 값은 fallback 용도이며, `source=pi-obd` 또는 `source=pi-local` 같은 Pi 로컬 입력이 활성화된 뒤에는 기존 live 값을 덮지 않고 비어 있는 field만 채운다. 실사용 모드처럼 dummy source가 꺼진 상태에서는 layout JSON의 샘플 내비 데이터와 실차 입력이 필요한 차량 샘플값(speed/RPM/coolant/voltage/fuel/gear/ATF/pedal/backup speed)을 시작 상태에서 지운다. Android 브릿지가 실제 `active=true` navigation packet을 보내기 전까지는 이전/샘플 경로 안내가 표시되지 않아야 하고, Pi OBD speed가 없거나 stale이면 Android GPS speed는 `speed_kmh_backup`으로만 fallback된다.

설치 후 환경파일이 Pi 단독 운용 조건을 만족하는지 먼저 요약하려면:

```bash
/opt/headunit-pi-hud/.venv/bin/python /opt/headunit-pi-hud/pi-hud/scripts/first-run-status.py
```

이 명령은 `/etc/headunit-pi-hud.env`를 읽고 layout, 1920x480 display 설정, dummy mode, OBD/iCar transport, CANable channel, Android bridge 역할을 요약한다. `standalone_ready`는 Android 브릿지 없이 Pi만으로 차량 HUD가 가능한 설정인지 보는 값이며, layout이 유효하고 `HEADUNIT_HUD_DUMMY=0`, OBD/iCar, CANable이 모두 설정되어야 `yes`가 된다. `HEADUNIT_HUD_REQUIRE_HANDOFF=1`이면 layout에 Windows 에디터가 저장한 `pi_hud_handoff.layout_sha256`이 있어야 하고, 저장 후 JSON 본문이 바뀌면 standalone ready가 false가 된다. 결과 JSON은 기본적으로 `/opt/headunit-pi-hud/vehicle-baseline/first-run-status.json`에 저장된다.

실제 HDMI/framebuffer가 1920x480으로 잡혔는지 확인하려면 `--probe-display`를 붙인다.

```bash
/opt/headunit-pi-hud/.venv/bin/python /opt/headunit-pi-hud/pi-hud/scripts/first-run-status.py --probe-display
```

이 모드는 Pi의 `/sys/class/graphics/fb0/virtual_size`를 읽어 framebuffer가 `1920,480`인지 확인한다. 화면이 1280x720, 1920x1080 등으로 잡히면 `display_ready=false`가 된다.

실차 연결까지 한 번에 확인하려면 `--probe-inputs`를 붙인다.

```bash
/opt/headunit-pi-hud/.venv/bin/python /opt/headunit-pi-hud/pi-hud/scripts/first-run-status.py --probe-inputs
```

이 모드는 설정 요약에 더해 OBD/iCar probe와 CANable frame 수신 probe를 실행한다. `standalone_ready`는 설정 준비 상태이고, `live_input_ready`는 실제 OBD/CAN 응답까지 확인된 상태다. 하드웨어가 아직 연결되지 않았거나 시동/IG ON이 아니면 `standalone_ready=yes`여도 `live_input_ready=false`가 될 수 있다.

첫 실차 장착 때는 둘을 같이 실행한다.

```bash
/opt/headunit-pi-hud/.venv/bin/python /opt/headunit-pi-hud/pi-hud/scripts/first-run-status.py --probe-display --probe-inputs
```

실차에 가져가기 전후의 최종 체크 결과를 한 파일로 남기려면 acceptance check를 실행한다.

```bash
/opt/headunit-pi-hud/.venv/bin/python /opt/headunit-pi-hud/pi-hud/scripts/acceptance-check.py --json
```

`acceptance-check.py`는 `first-run-status.py` 결과 전체를 `first_run`에 포함하고, 상위 `acceptance` 객체에 `ready_for_car`, `layout_ready`, `display_ready`, `standalone_ready`, `live_input_ready`, `bridge_optional`, `pi_vehicle_inputs_configured`, `vehicle_profile_ready`를 따로 기록한다. 기본 실행은 하드웨어 probe 없이 `/etc/headunit-pi-hud.env` 설정만 확인하므로, iCar/OBD와 CANable 경로를 적어둔 상태면 Android 브릿지가 없어도 `ready_for_car=true`가 될 수 있다. `HEADUNIT_HUD_VEHICLES_DIR`가 지정되어 있으면 선택 차량 프로필 JSON이 그 디렉터리에 설치되어 있는지도 확인한다. 실제 HDMI와 차량 입력까지 확인하려면 다음처럼 probe를 켠다.

```bash
/opt/headunit-pi-hud/.venv/bin/python /opt/headunit-pi-hud/pi-hud/scripts/acceptance-check.py --probe-display --probe-inputs --json
```

결과 JSON은 기본적으로 `/opt/headunit-pi-hud/vehicle-baseline/acceptance-check.json`에 저장된다. `--probe-inputs`를 붙인 경우에는 OBD/iCar와 CANable live probe까지 통과해야 `ready_for_car=true`가 된다.

iCar Pro 2S가 Classic Bluetooth SPP로 잡히면 `/etc/headunit-pi-hud.env`에 Bluetooth MAC을 넣어 service 시작 전에 `/dev/rfcomm0`을 자동으로 bind할 수 있다.

```bash
HEADUNIT_HUD_OBD_PORT=/dev/rfcomm0
HEADUNIT_HUD_ICAR_MAC=AA:BB:CC:DD:EE:FF
HEADUNIT_HUD_RFCOMM_INDEX=0
HEADUNIT_HUD_RFCOMM_CHANNEL=1
```

`HEADUNIT_HUD_ICAR_MAC`이 비어 있으면 rfcomm setup은 건너뛴다. iCar Pro 2S가 BLE-only로만 보이면 이 rfcomm 경로는 동작하지 않으므로 BLE MAC/UUID를 지정하거나 USB serial ELM327/OBDLink SX 계열을 쓴다.

BLE-only로 보이면 rfcomm 값은 비워두고 BLE MAC/UUID를 넣는다.

```bash
HEADUNIT_HUD_OBD_PORT=
HEADUNIT_HUD_OBD_BLE_MAC=AA:BB:CC:DD:EE:FF
HEADUNIT_HUD_OBD_BLE_RX_UUID=0000fff1-0000-1000-8000-00805f9b34fb
HEADUNIT_HUD_OBD_BLE_TX_UUID=0000fff2-0000-1000-8000-00805f9b34fb
```

`HEADUNIT_HUD_OBD_PORT`가 설정되어 있으면 serial/rfcomm이 우선이고 BLE 설정은 쓰지 않는다. BLE MAC만 있고 UUID가 비어 있으면 HUD는 계속 뜨지만 OBD 상태는 `ble-config-missing`으로 표시된다.

BLE MAC은 보이지만 RX/TX UUID를 모르면 Pi에서 자동 탐색을 먼저 다시 실행한다. 특정 MAC만 직접 확인해야 할 때는 GATT characteristic 후보를 별도로 확인한다.

```bash
/opt/headunit-pi-hud/.venv/bin/python /opt/headunit-pi-hud/pi-hud/scripts/auto-configure-hardware.py --apply --force
/opt/headunit-pi-hud/.venv/bin/python /opt/headunit-pi-hud/pi-hud/scripts/scan-ble-obd.py AA:BB:CC:DD:EE:FF
```

이 스크립트는 notify/indicate characteristic을 `HEADUNIT_HUD_OBD_BLE_RX_UUID` 후보로, write/write-without-response characteristic을 `HEADUNIT_HUD_OBD_BLE_TX_UUID` 후보로 출력하고 `/etc/headunit-pi-hud.env`에 넣을 줄을 제안한다. 제안값을 저장한 뒤 `diagnose-inputs.py`로 `ATI`, `0100` 응답이 실제로 오는지 확인한다.

입력 진단:

```bash
/opt/headunit-pi-hud/.venv/bin/python /opt/headunit-pi-hud/pi-hud/scripts/diagnose-inputs.py
```

이 명령은 기본적으로 `/etc/headunit-pi-hud.env`를 먼저 읽고, `HEADUNIT_HUD_ENV_FILE`이 지정되어 있으면 그 파일을 대신 읽는다. 따라서 설치 후 환경파일에 `HEADUNIT_HUD_OBD_PORT`, `HEADUNIT_HUD_CAN_CHANNEL`을 넣어두면 별도 `set -a` 없이 같은 값으로 진단한다. Serial/rfcomm OBD가 비어 있고 `HEADUNIT_HUD_OBD_BLE_MAC`, `HEADUNIT_HUD_OBD_BLE_RX_UUID`, `HEADUNIT_HUD_OBD_BLE_TX_UUID`가 있으면 BLE ELM327 probe로 `ATI`, `0100` 응답을 확인한다. BLE MAC만 있고 UUID가 없으면 `missing RX/TX UUID`로 실패하므로, 이 상태에서는 BLE characteristic을 먼저 확인해야 한다.

실차 baseline 증거 수집:

```bash
/opt/headunit-pi-hud/.venv/bin/python /opt/headunit-pi-hud/pi-hud/scripts/collect-vehicle-baseline.py \
  --can-duration 30 \
  --output /tmp/avante-hd-baseline.json
```

이 명령도 `/etc/headunit-pi-hud.env` 또는 `HEADUNIT_HUD_ENV_FILE`을 먼저 읽어서 `HEADUNIT_HUD_OBD_PORT`, `HEADUNIT_HUD_OBD_BAUD`, `HEADUNIT_HUD_OBD_BLE_*`, `HEADUNIT_HUD_CAN_CHANNEL`을 기본값으로 쓴다. 필요하면 `--obd-port`, `--obd-baud`, `--obd-ble-mac`, `--obd-ble-rx-uuid`, `--obd-ble-tx-uuid`, `--can-channel`로 임시 override할 수 있다. iCar/ELM327의 `ATI`, `ATDP`, supported PID bitmap, 표준 PID, DTC raw response와 CANable/SocketCAN frame sample을 JSON으로 저장한다. Serial/rfcomm이 설정되어 있으면 serial transport를 우선하고, serial이 비어 있을 때 BLE MAC이 있으면 BLE transport로 OBD baseline을 수집한다. 기본 표준 PID/DTC 명령 뒤에는 차량 profile의 `obd_probe_commands`가 이어서 실행된다. 아반떼 HD profile에는 `7E0/7E8 21 01`, `21 02`, `21 14`, `7D1/7D9 21 01`, `22 0104`, `7C6/7CE 22 B002` 후보가 들어 있지만 모두 `confirmed:false`이며, HUD 상시 표시값으로 쓰기 전에 raw response와 값 범위를 실차에서 확인해야 한다. 이 파일은 실제 차량/어댑터 응답 증거이므로 repo에는 commit하지 않는다.

CAN frame sample을 수집한 뒤 ID별 빈도와 변하는 byte 위치를 요약하려면:

```bash
/opt/headunit-pi-hud/.venv/bin/python /opt/headunit-pi-hud/pi-hud/scripts/summarize-can-baseline.py \
  /tmp/avante-hd-baseline.json \
  --output /tmp/avante-hd-can-summary.json
```

요약 파일에는 `frame_count`, `unique_id_count`, ID별 `count`, `dlc`, `changing_byte_indexes`, `sample_data`가 들어간다. 기어 위치, 방향지시등, 브레이크처럼 표준 OBD로 안 잡히는 항목은 조건별 baseline을 여러 개 수집한 뒤 이 요약을 비교해서 후보 CAN ID와 byte를 좁힌다.

레이아웃을 Pi에 올리기 전 실제 1920x480 렌더러로 검증:

```bash
/opt/headunit-pi-hud/.venv/bin/python /opt/headunit-pi-hud/pi-hud/scripts/verify-layout.py \
  /opt/headunit-pi-hud/layouts/avante_hd_2010_default.json \
  --width 1920 \
  --height 480 \
  --output /tmp/headunit-hud-layout.png
```

이 명령은 layout schema 검증, dummy binding 검증, 선택 차량 검증, 1920x480 non-blank 렌더링 검증을 같이 수행한다. `--output`을 주면 Pi와 같은 `HudRenderer`가 그린 PNG snapshot을 남긴다.

환경파일을 shell에 로드해서 같은 값으로 진단하려면:

```bash
set -a
. /etc/headunit-pi-hud.env
set +a
/opt/headunit-pi-hud/.venv/bin/python /opt/headunit-pi-hud/pi-hud/scripts/diagnose-inputs.py
```

Service 시작 전에는 `setup-obd-from-env.sh`와 `setup-canable-from-env.sh`가 순서대로 실행된다. OBD setup은 `HEADUNIT_HUD_ICAR_MAC`이 있을 때만 iCar rfcomm bind를 시도한다. CANable은 `HEADUNIT_HUD_CAN_CHANNEL`이 있으면 `setup-canable-from-env.sh`가 `canable-up.sh`를 호출해서 SocketCAN interface를 올린다. 기본값은 `HEADUNIT_HUD_CAN_LISTEN_ONLY=on`이므로 CANable은 raw sniffing용 listen-only로 시작한다. 실패해도 HUD는 계속 뜨고, 화면에는 OBD/CAN 상태가 error/stale로 남는다.

서비스 시작과 로그:

```bash
sudo systemctl restart headunit-pi-hud.service
sudo journalctl -u headunit-pi-hud.service -f
```

Android 브릿지가 같은 네트워크에서 Pi를 찾을 수 있는지 별도 장치에서 확인:

```bash
python pi-hud/scripts/probe-bridge.py 192.168.43.20 --send-sample --speed 57
```

Pi IP를 모르면 broadcast로 시도할 수 있다.

```bash
python pi-hud/scripts/probe-bridge.py 255.255.255.255 --send-sample
```

성공하면 `headunit_hud_discover` probe에 Pi가 `device_kind=pi_hud` hello로 응답하고, probe script가 샘플 navigation packet과 backup speed packet을 Pi HUD UDP port로 보낸다. 이때 HUD 화면의 내비 영역이 샘플 안내로 바뀌면 Android 브릿지가 붙을 네트워크 경로가 열려 있는 것이다. 차량 속도는 Pi OBD/CAN 값이 우선이고, 이 샘플 speed는 `speed_kmh_backup`에만 들어간다.

화면이 Raspberry Pi OS Lite에서 직접 KMS fullscreen으로 떠야 하는 경우 `/etc/headunit-pi-hud.env`에 다음 값을 넣어 확인한다.

```bash
HEADUNIT_HUD_SDL_VIDEODRIVER=kmsdrm
```

## Electron 레이아웃 에디터

개발 실행:

```powershell
cd layout-editor-electron
npm install
npm start
```

Windows 패키징:

```powershell
npm run build
```

빌드 결과물은 `layout-editor-electron/dist/HeadunitHudLayoutEditor-win32-x64/HeadunitHudLayoutEditor.exe`에 생성된다. 기존 exe가 실행 중이면 Windows가 파일 교체를 막으므로 편집기 창을 닫고 다시 빌드한다.

Electron 에디터는 Python bridge를 통해 Pi 런타임과 같은 `HudRenderer`로 1920x480 preview를 생성한다. 카테고리 탭에서 speed, gear, RPM, 개별 warning icon, navigation text, OBD/CAN 진단값, text label 등을 추가하고, 캔버스에서 위치/크기를 조정하거나 인스펙터에서 font/binding을 수정한 뒤 JSON으로 저장한다. 저장과 `Validate` 버튼은 Pi 렌더러의 non-blank 검증을 수행하며, 저장된 JSON에는 `pi_hud_handoff` 메타데이터가 들어간다. `PNG`는 현재 레이아웃의 full-resolution snapshot을 저장하고, `Field Pack`은 레이아웃, 차량 프로필, warning icon PNG, 환경 예제, preview, manifest를 `headunit-pi-field-pack.zip`으로 묶는다. Pi 런타임은 같은 JSON과 아이콘 자산을 그대로 렌더링한다.

최신 기본 레이아웃은 `gear_indicator`와 `nav_icon`을 별도 element type으로 쓴다. `gear_indicator`는 `P,R,N,D,3,2,L` 전체를 나열하고 현재 `vehicle.gear_range`만 크게 강조하는 `strip` 스타일과 현재 기어만 표시하는 `active_only` 스타일을 지원한다. `nav_icon`은 localized `nav.instruction` 문자열을 파싱하지 않고 `nav.event_type`, `nav.turn_side` 숫자 필드로 방향 아이콘을 선택한다. `nav.instruction`은 `우회전` 같은 maneuver text만 저장하고, `300 m` 같은 거리는 `nav.distance_meters` 요소에서만 표시한다. 팔레트 버튼은 현재 screen에 이미 들어간 요소를 색상과 체크 표시로 구분하고, 같은 팔레트 요소를 다시 누르면 중복 생성하지 않고 기존 요소를 선택한다. Delete 버튼과 Delete 키는 현재 screen snapshot까지 즉시 동기화한다. `Pick Color`, `Pick Active`, `Pick Accent` 버튼은 color chooser를 열어 `color`, `active_color`, `accent` 값을 바로 반영한다.

기본 visual direction은 Bosch Digital Instrument Cluster product sheet의 high-contrast digital cluster 표현과 ISO 2575:2021의 tell-tale symbol 체계를 참고했다. 경고등 PNG는 Wikimedia Commons `Dashboard icons`/`Dashboard SVG icons` 계열 파일을 RGBA PNG로 정리해서 사용하며, 파일별 attribution은 `pi-hud/assets/warning-icons/README.md`에 남긴다.

에디터에서 저장한 파일을 Pi에 올리기 전에는 handoff hash까지 검증할 수 있다. systemd/env 경로에서는 `HEADUNIT_HUD_REQUIRE_HANDOFF=1`을 켜면 런타임 시작 전에도 같은 검증을 수행한다.

```bash
/opt/headunit-pi-hud/.venv/bin/python /opt/headunit-pi-hud/pi-hud/scripts/verify-layout.py \
  /opt/headunit-pi-hud/layouts/my-layout.json \
  --width 1920 --height 480 --require-handoff
```

## 아직 확정해야 할 것

- iCar Pro 2S가 Pi에서 Classic Bluetooth SPP로 잡히는지, BLE-only인지 확인하고 BLE-only라면 실제 RX/TX UUID 확인.
- 아반떼 HD 2010 1.6 AT의 CAN ID별 의미 확정.
- 기어 위치가 CAN/확장 PID 중 어디서 안정적으로 나오는지 확인.
- ABS/EPS/SRS 같은 모듈별 DTC를 표준 OBD만으로 볼 수 있는지, 제조사 진단 요청이 필요한지 확인.
- iCar Pro 2S가 실제 차량/Pi에서 serial/rfcomm 또는 BLE로 안정적으로 표준 PID를 응답하는지 확인.
