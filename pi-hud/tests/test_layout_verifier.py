from __future__ import annotations

import copy
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from hud_pi.layout import load_layout
from hud_pi import layout_verifier
from hud_pi.layout_verifier import verify_layout, verify_layout_file


def load_verify_layout_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "verify-layout.py"
    spec = importlib.util.spec_from_file_location("verify_layout", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load verify-layout.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LayoutVerifierTest(unittest.TestCase):
    def test_verify_default_layout_renders_nonblank_1920_by_480(self) -> None:
        result = verify_layout_file("layouts/avante_hd_2010_default.json", width=1920, height=480)

        self.assertTrue(result.ok, result.errors)
        self.assertEqual((1920, 480), result.render_size)
        self.assertGreater(result.non_background_pixels, 0)

    def test_verify_layout_reports_contract_errors(self) -> None:
        layout = load_layout("layouts/avante_hd_2010_default.json")
        layout["selected_vehicle"] = "missing_vehicle"

        result = verify_layout(layout, width=1920, height=480)

        self.assertFalse(result.ok)
        self.assertIn("selected_vehicle 'missing_vehicle' is not present in vehicles", result.errors)

    def test_verify_layout_writes_png_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "layout.png"

            result = verify_layout_file("layouts/avante_hd_2010_default.json", width=960, height=240, output=output)

            self.assertTrue(result.ok, result.errors)
            self.assertTrue(output.exists())
            self.assertTrue(output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))

    def test_verify_layout_fails_when_every_element_is_hidden(self) -> None:
        layout = copy.deepcopy(load_layout("layouts/avante_hd_2010_default.json"))
        for element in layout["elements"]:
            element["visible"] = False
        for screen in layout.get("screens", {}).values():
            for element in screen.get("elements", []):
                element["visible"] = False

        result = verify_layout(layout, width=1920, height=480)

        self.assertFalse(result.ok)
        self.assertIn("layout rendered blank at 1920x480", result.errors)

    def test_verify_default_layout_has_editor_handoff_metadata(self) -> None:
        result = verify_layout_file("layouts/avante_hd_2010_default.json", width=1920, height=480, require_handoff=True)

        self.assertTrue(result.ok, result.errors)

    def test_verify_layout_can_require_editor_handoff_metadata(self) -> None:
        layout = load_layout("layouts/avante_hd_2010_default.json")
        layout.pop("pi_hud_handoff", None)

        result = verify_layout(layout, width=1920, height=480, require_handoff=True)

        self.assertFalse(result.ok)
        self.assertIn("pi_hud_handoff metadata is missing", result.errors)

    def test_verify_layout_accepts_handoff_digest_and_rejects_tampering(self) -> None:
        layout = load_layout("layouts/avante_hd_2010_default.json")
        initial = verify_layout(layout, width=1920, height=480)
        layout["pi_hud_handoff"] = layout_verifier.build_layout_handoff(
            layout,
            render_size=initial.render_size,
            non_background_pixels=initial.non_background_pixels,
            verified_at_utc="2026-06-02T00:00:00Z",
        )

        result = verify_layout(layout, width=1920, height=480, require_handoff=True)

        self.assertTrue(result.ok, result.errors)

        layout["elements"][0]["x"] += 1
        tampered = verify_layout(layout, width=1920, height=480, require_handoff=True)

        self.assertFalse(tampered.ok)
        self.assertIn("pi_hud_handoff layout_sha256 does not match layout content", tampered.errors)

    def test_verify_layout_script_accepts_require_handoff_option(self) -> None:
        module = load_verify_layout_module()

        args = module.build_parser().parse_args(["--require-handoff"])

        self.assertTrue(args.require_handoff)


if __name__ == "__main__":
    unittest.main()
