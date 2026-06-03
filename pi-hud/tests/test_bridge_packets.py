from __future__ import annotations

import unittest

from hud_pi.bridge_packets import SequencedPacketGate


class BridgePacketsTest(unittest.TestCase):
    def test_sequenced_packet_gate_rejects_non_dict_and_stale_sequences(self) -> None:
        gate = SequencedPacketGate()

        self.assertFalse(gate.accepts(["not", "a", "packet"]))
        self.assertTrue(gate.accepts({"road": "current"}))
        self.assertTrue(gate.accepts({"seq": 10, "road": "fresh"}))
        self.assertFalse(gate.accepts({"seq": 10, "road": "duplicate"}))
        self.assertFalse(gate.accepts({"seq": 9, "road": "old"}))
        self.assertTrue(gate.accepts({"seq": 11, "road": "new"}))

    def test_sequenced_packet_gate_accepts_unparseable_sequences_without_advancing_state(self) -> None:
        gate = SequencedPacketGate()

        self.assertTrue(gate.accepts({"seq": "not-a-number"}))
        self.assertIsNone(gate.last_sequence)
        self.assertTrue(gate.accepts({"seq": 1}))
        self.assertFalse(gate.accepts({"seq": 1}))


if __name__ == "__main__":
    unittest.main()
