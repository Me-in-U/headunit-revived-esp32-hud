from __future__ import annotations

import unittest

from hud_pi.source_threads import SourceThread


class SourceThreadsTest(unittest.TestCase):
    def test_source_thread_sets_daemon_name_and_stop_event(self) -> None:
        thread = SourceThread(lambda _source, _update: None, "test-source")

        self.assertTrue(thread.daemon)
        self.assertEqual("test-source", thread.name)
        self.assertFalse(thread.stop_event.is_set())

        thread.stop()

        self.assertTrue(thread.stop_event.is_set())


if __name__ == "__main__":
    unittest.main()
