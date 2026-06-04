# Raspberry Pi HUD 간단 설치

Pi 터미널에서 순서대로 입력한다. Raspberry Pi OS Lite 설치와 SSH 접속은 끝난 상태를 기준으로 한다.

## 1. 기본 설치

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y git
sudo reboot
```

재부팅 후 SSH로 다시 접속한다.

```bash
git clone https://github.com/Me-in-U/headunit-revived-esp32-hud.git
cd headunit-revived-esp32-hud
sudo pi-hud/scripts/install-pi.sh
```

설치가 끝나면 HUD 서비스는 부팅 시 자동 실행된다. git 자동 업데이트도 기본으로 켜진다.

## 2. OBD/CAN 없이 화면만 테스트

CANable과 iCar가 없어도 HUD 화면 테스트는 가능하다.

```bash
sudo sed -i \
  -e 's/^HEADUNIT_HUD_DUMMY=.*/HEADUNIT_HUD_DUMMY=1/' \
  -e 's/^HEADUNIT_HUD_OBD_PORT=.*/HEADUNIT_HUD_OBD_PORT=/' \
  -e 's/^HEADUNIT_HUD_ICAR_MAC=.*/HEADUNIT_HUD_ICAR_MAC=/' \
  -e 's/^HEADUNIT_HUD_OBD_BLE_MAC=.*/HEADUNIT_HUD_OBD_BLE_MAC=/' \
  -e 's/^HEADUNIT_HUD_OBD_BLE_RX_UUID=.*/HEADUNIT_HUD_OBD_BLE_RX_UUID=/' \
  -e 's/^HEADUNIT_HUD_OBD_BLE_TX_UUID=.*/HEADUNIT_HUD_OBD_BLE_TX_UUID=/' \
  -e 's/^HEADUNIT_HUD_CAN_CHANNEL=.*/HEADUNIT_HUD_CAN_CHANNEL=/' \
  /etc/headunit-pi-hud.env

sudo systemctl restart headunit-pi-hud.service
sudo journalctl -u headunit-pi-hud.service -f
```

로그 화면은 `Ctrl+C`로 빠져나온다.

화면 크기만 확인한다.

```bash
/opt/headunit-pi-hud/.venv/bin/python \
  /opt/headunit-pi-hud/pi-hud/scripts/first-run-status.py \
  --probe-display
```

## 3. iCar/CANable 자동 설정

iCar와 CANable을 연결하고 차량은 IGN ON 상태로 둔다. 그 다음 실행한다.

```bash
sudo /opt/headunit-pi-hud/.venv/bin/python \
  /opt/headunit-pi-hud/pi-hud/scripts/auto-configure-hardware.py \
  --apply --force

sudo sed -i 's/^HEADUNIT_HUD_DUMMY=.*/HEADUNIT_HUD_DUMMY=0/' /etc/headunit-pi-hud.env

sudo systemctl restart headunit-pi-hud.service
```

실제 입력까지 확인한다.

```bash
/opt/headunit-pi-hud/.venv/bin/python \
  /opt/headunit-pi-hud/pi-hud/scripts/first-run-status.py \
  --probe-display --probe-inputs
```

## 4. 상태 확인

```bash
sudo systemctl status headunit-pi-hud.service
sudo journalctl -u headunit-pi-hud.service -n 80
```

## 5. 업데이트 확인

자동 업데이트는 기본으로 켜져 있다. 바로 한 번 실행하려면:

```bash
sudo systemctl start headunit-pi-hud-update.service
sudo journalctl -u headunit-pi-hud-update.service -n 80
```

끄려면:

```bash
sudo sed -i 's/^HEADUNIT_HUD_AUTO_UPDATE=.*/HEADUNIT_HUD_AUTO_UPDATE=0/' /etc/headunit-pi-hud.env
```

## 막히면

전체 설명은 `docs/pi-hud-runtime.ko.md`를 본다. 이 간단 문서는 Pi에서 처음 실행할 명령만 모아둔 것이다.
