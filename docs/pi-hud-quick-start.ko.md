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
sudo bash setup-pi-hud.sh 1
```

설치가 끝나면 HUD 서비스는 부팅 시 자동 실행된다. git 자동 업데이트도 기본으로 켜진다.

나중에 메뉴를 다시 열고 싶으면:

```bash
cd ~/headunit-revived-esp32-hud
sudo bash setup-pi-hud.sh
```

메뉴에서는 보통 이 순서로 누른다.

```text
1  설치/업데이트와 자동 실행 설정
2  OBD/CAN 없이 화면만 테스트
3  iCar/CANable 자동 설정
6  상태 점검
```

## 2. 레이아웃 에디터 수정 적용

Windows 레이아웃 에디터에서 수정한 화면은 `Field Pack` zip으로 Pi에 적용한다.

Windows에서 에디터를 열고 레이아웃을 수정한 뒤:

```text
Field Pack 버튼 -> headunit-pi-field-pack.zip 저장
```

zip 파일을 Pi로 복사한다. SSH 이름이 `user@hud`라면 Windows PowerShell에서:

```powershell
scp .\headunit-pi-field-pack.zip user@hud:~/
```

Pi 터미널에서 적용한다.

```bash
sudo /opt/headunit-pi-hud/.venv/bin/python \
  /opt/headunit-pi-hud/pi-hud/scripts/apply-field-pack.py \
  ~/headunit-pi-field-pack.zip
sudo systemctl restart headunit-pi-hud.service
```

이미 iCar/CANable 설정을 해둔 Pi에서는 `--overwrite-env`를 붙이지 않는다. 붙이면 `/etc/headunit-pi-hud.env`가 예제값으로 덮일 수 있다.

## 3. OBD/CAN 없이 화면만 테스트

CANable과 iCar가 없어도 HUD 화면 테스트는 가능하다. 설치 직후 OBD/CAN 장비가 잡히지 않았으면 별도 설정 없이 dummy 화면으로 뜬다.

```bash
sudo bash setup-pi-hud.sh 2
```

로그 화면은 `Ctrl+C`로 빠져나온다.

화면 크기만 확인한다.

```bash
sudo bash setup-pi-hud.sh 6
```

## 4. iCar/CANable 자동 설정

iCar와 CANable을 연결하고 차량은 IGN ON 상태로 둔다. 그 다음 실행한다.

```bash
sudo bash setup-pi-hud.sh 3
```

실제 입력까지 확인한다.

```bash
/opt/headunit-pi-hud/.venv/bin/python \
  /opt/headunit-pi-hud/pi-hud/scripts/first-run-status.py \
  --probe-display --probe-inputs
```

## 5. 상태 확인

```bash
sudo bash setup-pi-hud.sh 6
```

## 6. 업데이트 확인

자동 업데이트는 기본으로 켜져 있다. 바로 한 번 실행하려면:

```bash
sudo bash setup-pi-hud.sh 7
```

끄려면:

```bash
sudo bash setup-pi-hud.sh 8
```

## 막히면

전체 설명은 `docs/pi-hud-runtime.ko.md`를 본다. 이 간단 문서는 Pi에서 처음 실행할 명령만 모아둔 것이다.
