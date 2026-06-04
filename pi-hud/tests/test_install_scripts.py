from __future__ import annotations

import unittest
from pathlib import Path


class InstallScriptsTest(unittest.TestCase):
    def test_root_setup_menu_wraps_pi_install_autostart_update_and_diagnostics(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        setup_script_path = repo_root / "setup-pi-hud.sh"

        self.assertTrue(setup_script_path.exists())
        setup_script = setup_script_path.read_text(encoding="utf-8")

        self.assertIn("Headunit Pi HUD Setup", setup_script)
        self.assertIn("install-pi.sh", setup_script)
        self.assertIn("systemctl enable headunit-pi-hud.service", setup_script)
        self.assertIn("systemctl enable headunit-pi-hud-update.timer", setup_script)
        self.assertIn("auto-configure-hardware.py", setup_script)
        self.assertIn("first-run-status.py", setup_script)
        self.assertIn("follow_journal()", setup_script)
        self.assertIn('journalctl -u "${unit}" -f --no-pager', setup_script)
        self.assertIn('trap \'kill "${pid}"', setup_script)
        self.assertIn('wait "${pid}"', setup_script)
        self.assertIn("Log view closed", setup_script)
        self.assertIn('follow_journal headunit-pi-hud.service', setup_script)
        self.assertIn("journalctl -u headunit-pi-hud-update.service", setup_script)

    def test_root_setup_applies_repo_field_pack_zip(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        setup_script = (repo_root / "setup-pi-hud.sh").read_text(encoding="utf-8")

        self.assertIn('FIELD_PACK_FILE_NAME="${HEADUNIT_HUD_FIELD_PACK_FILE_NAME:-headunit-pi-field-pack.zip}"', setup_script)
        self.assertIn("field_pack_package_path()", setup_script)
        self.assertIn("apply_field_pack_from_repo()", setup_script)
        self.assertIn('"${ROOT_DIR}/field-pack/${FIELD_PACK_FILE_NAME}"', setup_script)
        self.assertIn('"${app}/pi-hud/scripts/apply-field-pack.py"', setup_script)
        self.assertIn('"${package}" --app-dir "${app}" --env-file "${ENV_FILE}"', setup_script)
        self.assertIn("Apply Field Pack from field-pack/headunit-pi-field-pack.zip", setup_script)
        self.assertIn("9) apply_field_pack_from_repo ;;", setup_script)

    def test_field_pack_drop_folder_is_tracked_without_zip_payloads(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")

        self.assertTrue((repo_root / "field-pack" / "README.ko.md").exists())
        self.assertIn("field-pack/*.zip", gitignore)
        self.assertIn("!field-pack/README.ko.md", gitignore)
        self.assertNotIn("\nfield-pack/\n", f"\n{gitignore}\n")

    def test_root_setup_install_update_restores_real_runtime_mode(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        setup_script = (repo_root / "setup-pi-hud.sh").read_text(encoding="utf-8")
        install_start = setup_script.index("install_or_update()")
        restart_index = setup_script.index("systemctl restart headunit-pi-hud.service", install_start)
        dummy_reset_index = setup_script.index("set_env_value HEADUNIT_HUD_DUMMY 0", install_start)

        self.assertLess(dummy_reset_index, restart_index)

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
            "scan-ble-obd.py",
            "auto-configure-hardware.py",
            "build-field-pack.py",
            "apply-field-pack.py",
        ]

        missing = [helper for helper in expected_helpers if f'pi-hud/scripts/{helper}"' not in install_script]

        self.assertEqual([], missing)

    def test_pi_install_restores_real_runtime_mode_when_env_file_exists(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        install_script = (pi_hud_root / "scripts" / "install-pi.sh").read_text(encoding="utf-8")
        self.assertIn("set_env_value()", install_script)
        self.assertIn("set_env_value HEADUNIT_HUD_DUMMY 0", install_script)

        env_create_index = install_script.index('install -m 0644 "${APP_DIR}/pi-hud/config/pi-hud.env.example" "${ENV_FILE}"')
        dummy_reset_index = install_script.index("set_env_value HEADUNIT_HUD_DUMMY 0")
        auto_config_index = install_script.index("auto-configure-hardware.py")

        self.assertLess(env_create_index, dummy_reset_index)
        self.assertLess(dummy_reset_index, auto_config_index)

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

    def test_systemd_unit_does_not_restart_after_manual_hud_quit(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        service_file = (pi_hud_root / "systemd" / "headunit-pi-hud.service").read_text(encoding="utf-8")

        self.assertIn("Restart=on-failure", service_file)
        self.assertNotIn("Restart=always", service_file)

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

    def test_pi_auto_update_timer_checks_every_five_minutes(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        update_timer = (pi_hud_root / "systemd" / "headunit-pi-hud-update.timer").read_text(encoding="utf-8")

        self.assertIn("OnBootSec=3min", update_timer)
        self.assertIn("OnUnitActiveSec=5min", update_timer)
        self.assertNotIn("OnUnitActiveSec=30min", update_timer)

    def test_pi_install_runs_best_effort_hardware_autoconfig(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        install_script = (pi_hud_root / "scripts" / "install-pi.sh").read_text(encoding="utf-8")

        self.assertIn("auto-configure-hardware.py", install_script)
        self.assertIn("HEADUNIT_HUD_SKIP_AUTO_CONFIG", install_script)
        self.assertIn("--apply", install_script)
        self.assertIn("--no-restart", install_script)

    def test_pi_install_unmasks_and_copies_update_timer_as_unit_file(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        install_script = (pi_hud_root / "scripts" / "install-pi.sh").read_text(encoding="utf-8")
        setup_script = (pi_hud_root.parents[0] / "setup-pi-hud.sh").read_text(encoding="utf-8")

        self.assertIn("systemctl unmask headunit-pi-hud-update.timer", install_script)
        self.assertIn('cat "${APP_DIR}/pi-hud/systemd/headunit-pi-hud-update.timer" > "${UPDATE_TIMER_FILE}"', install_script)
        self.assertNotIn('sed \\\n  "${APP_DIR}/pi-hud/systemd/headunit-pi-hud-update.timer"', install_script)
        self.assertIn("systemctl unmask headunit-pi-hud-update.timer", setup_script)

    def test_screen_test_uses_ephemeral_env_and_detected_display_size(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        pi_hud_root = Path(__file__).resolve().parents[1]
        setup_script = (repo_root / "setup-pi-hud.sh").read_text(encoding="utf-8")
        run_script = (pi_hud_root / "scripts" / "run-from-env.sh").read_text(encoding="utf-8")
        service_file = (pi_hud_root / "systemd" / "headunit-pi-hud.service").read_text(encoding="utf-8")

        self.assertIn('TEST_ENV_FILE="${HEADUNIT_HUD_TEST_ENV_FILE:-/run/headunit-pi-hud-test.env}"', setup_script)
        self.assertIn("detect_framebuffer_size()", setup_script)
        self.assertIn("HEADUNIT_HUD_FRAMEBUFFER_SIZE_FILE", setup_script)
        self.assertIn("HEADUNIT_HUD_DUMMY=1", setup_script)
        self.assertIn("HEADUNIT_HUD_REQUIRE_HANDOFF=0", setup_script)
        self.assertIn("HEADUNIT_HUD_WINDOWED=1", setup_script)
        self.assertIn("HEADUNIT_HUD_WIDTH=%s", setup_script)
        self.assertIn("HEADUNIT_HUD_HEIGHT=%s", setup_script)
        self.assertIn("clear_screen_test_env", setup_script)
        self.assertIn("desktop_user()", setup_script)
        self.assertIn("run_desktop_hud()", setup_script)
        self.assertIn("systemctl stop headunit-pi-hud.service", setup_script)
        self.assertIn('sudo -u "${user}" env "${env_args[@]}"', setup_script)
        self.assertIn("Starting direct HUD screen test", setup_script)
        self.assertIn("press ESC or Q in the HUD window", setup_script)
        self.assertIn("Ctrl+C only exits when this terminal has focus", setup_script)
        self.assertIn("Normal HUD service remains stopped", setup_script)
        self.assertIn("EnvironmentFile=-/run/headunit-pi-hud-test.env", service_file)
        self.assertIn("HEADUNIT_HUD_TEST_ENV_FILE", run_script)
        self.assertIn('. "${TEST_ENV_FILE}"', run_script)

    def test_runtime_script_autodetects_desktop_display_for_systemd_service(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        run_script = (pi_hud_root / "scripts" / "run-from-env.sh").read_text(encoding="utf-8")

        self.assertIn("configure_display_environment()", run_script)
        self.assertIn("XDG_RUNTIME_DIR=/run/user/${uid}", run_script)
        self.assertIn("WAYLAND_DISPLAY=wayland-0", run_script)
        self.assertIn("/tmp/.X11-unix/X0", run_script)
        self.assertIn("DISPLAY=:0", run_script)
        self.assertIn("XAUTHORITY=${HOME}/.Xauthority", run_script)
        self.assertIn("SDL_VIDEODRIVER=kmsdrm", run_script)
        self.assertIn("HUD display env DISPLAY=", run_script)

    def test_git_update_script_fast_forwards_and_restarts_runtime_only_when_enabled(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        update_script = (pi_hud_root / "scripts" / "update-from-git.sh").read_text(encoding="utf-8")

        self.assertIn('truthy "${HEADUNIT_HUD_AUTO_UPDATE:-0}"', update_script)
        self.assertIn('GIT=(git -c "safe.directory=${APP_DIR}")', update_script)
        self.assertLess(update_script.index('GIT=(git -c "safe.directory=${APP_DIR}")'), update_script.index("rev-parse HEAD"))
        self.assertIn('"${GIT[@]}" fetch "${REMOTE}" "${BRANCH}"', update_script)
        self.assertIn('"${GIT[@]}" merge --ff-only FETCH_HEAD', update_script)
        self.assertIn("pip install -r", update_script)
        self.assertIn("restart_service()", update_script)
        self.assertIn("systemctl restart", update_script)
        self.assertIn("[WARN] updated git checkout, but failed to restart", update_script)
        self.assertIn("journalctl -u", update_script)

    def test_git_update_skips_pip_when_requirements_are_unchanged(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        update_script = (pi_hud_root / "scripts" / "update-from-git.sh").read_text(encoding="utf-8")

        self.assertIn("requirements_changed()", update_script)
        self.assertIn('"${GIT[@]}" diff --quiet "${CURRENT_HEAD}" "${FETCHED_HEAD}" -- pi-hud/requirements.txt', update_script)
        self.assertIn("REQUIREMENTS_CHANGED=0", update_script)
        self.assertIn("REQUIREMENTS_CHANGED=1", update_script)
        self.assertIn("requirements unchanged; skipping pip install", update_script)
        self.assertLess(update_script.index("REQUIREMENTS_CHANGED=0"), update_script.index('"${GIT[@]}" merge --ff-only FETCH_HEAD'))
        self.assertLess(update_script.index('"${GIT[@]}" merge --ff-only FETCH_HEAD'), update_script.index("pip install -r"))

    def test_git_update_logs_the_failed_step_before_exiting(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        update_script = (pi_hud_root / "scripts" / "update-from-git.sh").read_text(encoding="utf-8")

        self.assertIn("update_failed()", update_script)
        self.assertIn("trap 'update_failed", update_script)
        self.assertIn("[FAIL] update failed while running:", update_script)

    def test_git_update_leaves_manually_stopped_runtime_stopped(self) -> None:
        pi_hud_root = Path(__file__).resolve().parents[1]
        update_script = (pi_hud_root / "scripts" / "update-from-git.sh").read_text(encoding="utf-8")

        self.assertIn("service_is_active()", update_script)
        self.assertIn('systemctl is-active --quiet "${service}"', update_script)
        self.assertIn("is not active; leaving it stopped after update", update_script)
        self.assertLess(update_script.index("service_is_active()"), update_script.index("restart_service()"))


if __name__ == "__main__":
    unittest.main()
