from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hud_pi.runtime_config import build_parser, can_configured, dummy_enabled, load_runtime_layout, obd_configured


class RuntimeConfigTest(unittest.TestCase):
    def test_runtime_config_parser_and_source_flags_match_main_contract(self) -> None:
        parser = build_parser()

        default_args = parser.parse_args([])
        obd_args = parser.parse_args(["--obd-port", "/dev/rfcomm0"])
        ble_args = parser.parse_args(["--obd-ble-mac", "AA:BB:CC:DD:EE:FF"])
        can_args = parser.parse_args(["--can-channel", "can0"])

        self.assertTrue(dummy_enabled(default_args))
        self.assertTrue(obd_configured(obd_args))
        self.assertTrue(obd_configured(ble_args))
        self.assertTrue(can_configured(can_args))
        self.assertFalse(dummy_enabled(can_args))

    def test_load_runtime_layout_enforces_handoff_when_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout_path = Path(temp_dir) / "missing-handoff.json"
            layout = json.loads(Path("layouts/avante_hd_2010_default.json").read_text(encoding="utf-8"))
            layout.pop("pi_hud_handoff", None)
            layout_path.write_text(json.dumps(layout, ensure_ascii=False), encoding="utf-8")
            args = build_parser().parse_args(["--layout", str(layout_path), "--require-layout-handoff"])

            with self.assertRaisesRegex(ValueError, "pi_hud_handoff metadata is missing"):
                load_runtime_layout(args)


if __name__ == "__main__":
    unittest.main()
