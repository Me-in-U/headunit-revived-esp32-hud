from __future__ import annotations

import unittest
from pathlib import Path


class InstallScriptsTest(unittest.TestCase):
    def test_pi_install_marks_runtime_helper_scripts_executable(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        install_script = (pi_hud_root / "scripts" / "install-pi.sh").read_text(encoding="utf-8")

        expected_helpers = [
            "canable-up.sh",
            "icar-rfcomm-bind.sh",
            "setup-obd-from-env.sh",
            "run-from-env.sh",
            "setup-canable-from-env.sh",
            "diagnose-inputs.py",
            "verify-layout.py",
            "probe-bridge.py",
            "collect-vehicle-baseline.py",
            "first-run-status.py",
            "acceptance-check.py",
            "summarize-can-baseline.py",
            "scan-ble-obd.py",
            "auto-configure-hardware.py",
            "build-field-pack.py",
            "apply-field-pack.py",
        ]

        missing = [helper for helper in expected_helpers if f'pi-hud/scripts/{helper}"' not in install_script]

        self.assertEqual([], missing)

    def test_pi_install_defaults_service_user_to_invoking_sudo_user_before_pi_fallback(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        install_script = (pi_hud_root / "scripts" / "install-pi.sh").read_text(encoding="utf-8")

        self.assertIn('DEFAULT_SERVICE_USER="${SUDO_USER:-}"', install_script)
        self.assertIn("logname 2>/dev/null", install_script)
        self.assertIn("getent passwd 1000", install_script)
        self.assertIn('SERVICE_USER="${HEADUNIT_HUD_USER:-${DEFAULT_SERVICE_USER}}"', install_script)
        self.assertIn('id -u "${SERVICE_USER}"', install_script)
        self.assertNotIn('SERVICE_USER="${HEADUNIT_HUD_USER:-pi}"', install_script)

    def test_canable_setup_defaults_to_listen_only_mode(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        canable_script = (pi_hud_root / "scripts" / "canable-up.sh").read_text(encoding="utf-8")
        env_setup_script = (pi_hud_root / "scripts" / "setup-canable-from-env.sh").read_text(encoding="utf-8")

        self.assertIn('LISTEN_ONLY="${3:-on}"', canable_script)
        self.assertIn('listen-only "${LISTEN_ONLY}"', canable_script)
        self.assertIn('HEADUNIT_HUD_CAN_LISTEN_ONLY:-on', env_setup_script)

    def test_icar_classic_spp_setup_is_env_driven_before_runtime_start(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        obd_setup_path = pi_hud_root / "scripts" / "setup-obd-from-env.sh"
        service_file = (pi_hud_root / "systemd" / "headunit-pi-hud.service").read_text(encoding="utf-8")
        env_example = (pi_hud_root / "config" / "pi-hud.env.example").read_text(encoding="utf-8")

        self.assertTrue(obd_setup_path.exists())
        obd_setup_script = obd_setup_path.read_text(encoding="utf-8")

        self.assertIn("HEADUNIT_HUD_ICAR_MAC", obd_setup_script)
        self.assertIn("HEADUNIT_HUD_RFCOMM_INDEX:-0", obd_setup_script)
        self.assertIn("HEADUNIT_HUD_RFCOMM_CHANNEL:-1", obd_setup_script)
        self.assertIn("icar-rfcomm-bind.sh", obd_setup_script)
        self.assertIn("setup-obd-from-env.sh", service_file)
        self.assertIn("HEADUNIT_HUD_ICAR_MAC=", env_example)
        self.assertIn("HEADUNIT_HUD_RFCOMM_INDEX=0", env_example)
        self.assertIn("HEADUNIT_HUD_RFCOMM_CHANNEL=1", env_example)

    def test_icar_ble_obd_runtime_is_env_driven_without_android_bridge_dependency(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        run_script = (pi_hud_root / "scripts" / "run-from-env.sh").read_text(encoding="utf-8")
        env_example = (pi_hud_root / "config" / "pi-hud.env.example").read_text(encoding="utf-8")

        self.assertIn("HEADUNIT_HUD_OBD_BLE_MAC", run_script)
        self.assertIn("HEADUNIT_HUD_OBD_BLE_RX_UUID", run_script)
        self.assertIn("HEADUNIT_HUD_OBD_BLE_TX_UUID", run_script)
        self.assertIn("--obd-ble-mac", run_script)
        self.assertIn("--obd-ble-rx-uuid", run_script)
        self.assertIn("--obd-ble-tx-uuid", run_script)

        self.assertIn("HEADUNIT_HUD_OBD_BLE_MAC=", env_example)
        self.assertIn("HEADUNIT_HUD_OBD_BLE_RX_UUID=", env_example)
        self.assertIn("HEADUNIT_HUD_OBD_BLE_TX_UUID=", env_example)
        self.assertIn("Android bridge packets are only navigation plus backup speed", env_example)

    def test_icar_rfcomm_bind_uses_sudo_only_when_not_already_root(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        bind_script = (pi_hud_root / "scripts" / "icar-rfcomm-bind.sh").read_text(encoding="utf-8")

        self.assertIn('if [ "$(id -u)" -eq 0 ]; then', bind_script)
        self.assertIn('rfcomm "$@"', bind_script)
        self.assertIn('sudo rfcomm "$@"', bind_script)
        self.assertNotIn("sudo rfcomm release", bind_script)
        self.assertNotIn("sudo rfcomm bind", bind_script)

    def test_systemd_unit_enables_pi_hud_on_lite_boot_target(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        service_file = (pi_hud_root / "systemd" / "headunit-pi-hud.service").read_text(encoding="utf-8")

        self.assertIn("WantedBy=multi-user.target", service_file)

    def test_runtime_can_require_editor_layout_handoff_from_env(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        run_script = (pi_hud_root / "scripts" / "run-from-env.sh").read_text(encoding="utf-8")
        env_example = (pi_hud_root / "config" / "pi-hud.env.example").read_text(encoding="utf-8")

        self.assertIn("HEADUNIT_HUD_REQUIRE_HANDOFF", run_script)
        self.assertIn("--require-layout-handoff", run_script)
        self.assertIn("HEADUNIT_HUD_REQUIRE_HANDOFF=1", env_example)

    def test_env_example_declares_installed_vehicle_profiles_dir_for_acceptance_checks(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        env_example = (pi_hud_root / "config" / "pi-hud.env.example").read_text(encoding="utf-8")

        self.assertIn("HEADUNIT_HUD_VEHICLES_DIR=/opt/headunit-pi-hud/vehicles", env_example)

    def test_runtime_language_is_env_driven_for_korean_and_english_layouts(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        run_script = (pi_hud_root / "scripts" / "run-from-env.sh").read_text(encoding="utf-8")
        env_example = (pi_hud_root / "config" / "pi-hud.env.example").read_text(encoding="utf-8")

        self.assertIn("HEADUNIT_HUD_LANGUAGE", run_script)
        self.assertIn("--language", run_script)
        self.assertIn("HEADUNIT_HUD_LANGUAGE=ko", env_example)
        self.assertIn("ko or en", env_example)

    def test_pi_install_sets_up_default_enabled_git_auto_update_timer(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        install_script = (pi_hud_root / "scripts" / "install-pi.sh").read_text(encoding="utf-8")
        env_example = (pi_hud_root / "config" / "pi-hud.env.example").read_text(encoding="utf-8")

        self.assertTrue((pi_hud_root / "scripts" / "update-from-git.sh").exists())
        self.assertTrue((pi_hud_root / "systemd" / "headunit-pi-hud-update.service").exists())
        self.assertTrue((pi_hud_root / "systemd" / "headunit-pi-hud-update.timer").exists())
        self.assertIn("git", install_script)
        self.assertNotIn("--exclude .git", install_script)
        self.assertIn("headunit-pi-hud-update.service", install_script)
        self.assertIn("headunit-pi-hud-update.timer", install_script)
        self.assertIn("systemctl enable headunit-pi-hud-update.timer", install_script)
        self.assertIn("HEADUNIT_HUD_AUTO_UPDATE=1", env_example)
        self.assertIn("HEADUNIT_HUD_GIT_REMOTE=origin", env_example)
        self.assertIn("HEADUNIT_HUD_GIT_BRANCH=main", env_example)

    def test_pi_install_runs_best_effort_hardware_autoconfig(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        install_script = (pi_hud_root / "scripts" / "install-pi.sh").read_text(encoding="utf-8")

        self.assertIn("auto-configure-hardware.py", install_script)
        self.assertIn("HEADUNIT_HUD_SKIP_AUTO_CONFIG", install_script)
        self.assertIn("--apply", install_script)
        self.assertIn("--no-restart", install_script)

    def test_git_update_script_fast_forwards_and_restarts_runtime_only_when_enabled(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        update_script = (pi_hud_root / "scripts" / "update-from-git.sh").read_text(encoding="utf-8")

        self.assertIn('truthy "${HEADUNIT_HUD_AUTO_UPDATE:-0}"', update_script)
        self.assertIn("git fetch", update_script)
        self.assertIn("git merge --ff-only", update_script)
        self.assertIn("pip install -r", update_script)
        self.assertIn("systemctl restart headunit-pi-hud.service", update_script)


if __name__ == "__main__":
    unittest.main()
