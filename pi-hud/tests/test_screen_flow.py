from __future__ import annotations

import unittest

from hud_pi.screen_flow import (
    ScreenTransitionState,
    active_screen_name,
    advance_screen_transition,
    elements_for_screen,
    fade_active,
    fade_progress,
)


class ScreenFlowTest(unittest.TestCase):
    def test_active_screen_name_prefers_bridge_only_when_nav_connected(self) -> None:
        layout = {
            "canvas": {"width": 1920, "height": 480},
            "screens": {
                "standalone": {"elements": [{"id": "standalone"}]},
                "bridge": {"elements": [{"id": "bridge"}]},
            },
        }

        self.assertEqual("standalone", active_screen_name(layout, nav_connected=False))
        self.assertEqual("bridge", active_screen_name(layout, nav_connected=True))
        self.assertEqual("default", active_screen_name({"canvas": {"width": 1, "height": 1}}, nav_connected=True))
        self.assertEqual("aux", active_screen_name({"screens": {"aux": {"elements": []}}}, nav_connected=False))

    def test_elements_for_screen_uses_screen_elements_or_root_fallback(self) -> None:
        root_element = {"id": "root"}
        bridge_element = {"id": "bridge"}
        layout = {
            "elements": [root_element],
            "screens": {
                "bridge": {"elements": [bridge_element]},
                "empty": {},
            },
        }

        self.assertEqual([bridge_element], elements_for_screen(layout, "bridge"))
        self.assertEqual([root_element], elements_for_screen(layout, "default"))
        self.assertEqual([root_element], elements_for_screen(layout, "missing"))
        self.assertEqual([root_element], elements_for_screen(layout, "empty"))

    def test_fade_transition_active_state_and_progress_are_clamped(self) -> None:
        layout = {"screen_transition": {"type": "fade", "duration_ms": 500}}

        self.assertFalse(fade_active(layout, previous_screen_name=None, transition_started_at=1.0, now=1.1))
        self.assertTrue(fade_active(layout, previous_screen_name="standalone", transition_started_at=1.0, now=1.25))
        self.assertFalse(fade_active(layout, previous_screen_name="standalone", transition_started_at=1.0, now=1.5))
        self.assertEqual(0.0, fade_progress(layout, transition_started_at=1.0, now=0.9))
        self.assertEqual(0.5, fade_progress(layout, transition_started_at=1.0, now=1.25))
        self.assertEqual(1.0, fade_progress(layout, transition_started_at=1.0, now=2.0))
        self.assertEqual(1.0, fade_progress({}, transition_started_at=1.0, now=1.25))

    def test_advance_screen_transition_initializes_keeps_and_switches_state(self) -> None:
        initial = ScreenTransitionState()

        standalone = advance_screen_transition(initial, "standalone", now=1.0)
        self.assertEqual(ScreenTransitionState(active_screen_name="standalone"), standalone)

        unchanged = advance_screen_transition(standalone, "standalone", now=2.0)
        self.assertEqual(standalone, unchanged)

        bridge = advance_screen_transition(standalone, "bridge", now=3.0)
        self.assertEqual(
            ScreenTransitionState(
                active_screen_name="bridge",
                previous_screen_name="standalone",
                transition_started_at=3.0,
            ),
            bridge,
        )


if __name__ == "__main__":
    unittest.main()
