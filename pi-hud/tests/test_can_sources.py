from __future__ import annotations

import unittest

from hud_pi.can_sources import CanFrameSummary, SocketCanSource


class CanSourcesTest(unittest.TestCase):
    def test_can_sources_expose_summary_and_socketcan_source(self) -> None:
        summary = CanFrameSummary()
        source = SocketCanSource(
            lambda _source, _update: None,
            channel="can1",
            signal_definitions=[{"frame_id": "0x316", "name": "vehicle.gear_actual"}],
        )

        self.assertEqual(0, summary.frame_count)
        self.assertIsNone(summary.last_arbitration_id)
        self.assertEqual("socketcan", source.name)
        self.assertEqual("can1", source.channel)
        self.assertEqual([{"frame_id": "0x316", "name": "vehicle.gear_actual"}], source.signal_definitions)


if __name__ == "__main__":
    unittest.main()
