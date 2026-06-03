from __future__ import annotations

import unittest

from hud_pi.warning_row_layout import warning_row_entries


class WarningRowLayoutTest(unittest.TestCase):
    def test_warning_row_entries_compute_slots_and_localized_labels(self) -> None:
        entries = warning_row_entries(
            ["warnings.door_open", "warnings.check_engine", "warnings.coolant_temp"],
            rect=(20, 10, 300, 50),
            gap=4,
            language="ko",
        )

        self.assertEqual(
            [
                ("warnings.door_open", "도어", (20, 10, 96, 50)),
                ("warnings.check_engine", "엔진", (120, 10, 96, 50)),
                ("warnings.coolant_temp", "수온", (220, 10, 96, 50)),
            ],
            [(entry.binding, entry.label, entry.rect) for entry in entries],
        )

    def test_warning_row_entries_return_empty_for_no_bindings(self) -> None:
        self.assertEqual([], warning_row_entries([], rect=(0, 0, 100, 20), gap=4, language="en"))

    def test_warning_row_entries_preserve_renderer_minimum_step_rule(self) -> None:
        entries = warning_row_entries(["a", "b", "c"], rect=(0, 0, 2, 20), gap=4, language="en")

        self.assertEqual([(0, 0, -3, 20), (1, 0, -3, 20), (2, 0, -3, 20)], [entry.rect for entry in entries])


if __name__ == "__main__":
    unittest.main()
