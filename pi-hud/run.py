import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from hud_pi.main import main


if __name__ == "__main__":
    raise SystemExit(main())
