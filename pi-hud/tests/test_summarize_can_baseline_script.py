from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


def load_summarize_can_baseline_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "summarize-can-baseline.py"
    spec = importlib.util.spec_from_file_location("summarize_can_baseline", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load summarize-can-baseline.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SummarizeCanBaselineScriptTest(unittest.TestCase):
    def test_script_reads_baseline_and_writes_can_summary_json(self) -> None:
        module = load_summarize_can_baseline_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline = Path(temp_dir) / "baseline.json"
            output = Path(temp_dir) / "summary.json"
            baseline.write_text(
                json.dumps(
                    {
                        "vehicle": "avante_hd_2010_1_6_at",
                        "can": {
                            "records": [
                                {"timestamp": 1.0, "arbitration_id": 0x316, "id": "0x316", "dlc": 4, "data": "05 20 00 FF"},
                                {"timestamp": 1.1, "arbitration_id": 0x316, "id": "0x316", "dlc": 4, "data": "05 21 00 FF"},
                                {"timestamp": 1.2, "arbitration_id": 0x329, "id": "0x329", "dlc": 2, "data": "10 00"},
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            exit_code = module.main([str(baseline), "--output", str(output)])

            summary = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(0, exit_code)
        self.assertEqual("avante_hd_2010_1_6_at", summary["vehicle"])
        self.assertEqual(3, summary["can_summary"]["frame_count"])
        self.assertEqual("0x316", summary["can_summary"]["ids"][0]["id"])
        self.assertEqual([1], summary["can_summary"]["ids"][0]["changing_byte_indexes"])


if __name__ == "__main__":
    unittest.main()
