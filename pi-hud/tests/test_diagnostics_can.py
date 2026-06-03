from __future__ import annotations

import unittest

from hud_pi.diagnostics_can import open_socketcan_bus


class LegacyCanInterface:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def Bus(self, **kwargs: str) -> dict[str, str]:
        self.calls.append(kwargs)
        if "interface" in kwargs:
            raise TypeError("legacy python-can uses bustype")
        return kwargs


class LegacyCanModule:
    def __init__(self) -> None:
        self.interface = LegacyCanInterface()


class DiagnosticsCanTest(unittest.TestCase):
    def test_open_socketcan_bus_falls_back_to_legacy_bustype_argument(self) -> None:
        can_module = LegacyCanModule()

        bus = open_socketcan_bus(can_module, "can0")

        self.assertEqual({"channel": "can0", "bustype": "socketcan"}, bus)
        self.assertEqual(
            [
                {"channel": "can0", "interface": "socketcan"},
                {"channel": "can0", "bustype": "socketcan"},
            ],
            can_module.interface.calls,
        )


if __name__ == "__main__":
    unittest.main()
