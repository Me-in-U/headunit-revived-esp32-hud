from __future__ import annotations


def background_target_rect(
    screen_size: tuple[int, int],
    image_size: tuple[int, int],
    fit: str,
) -> tuple[int, int, int, int]:
    screen_w, screen_h = screen_size
    image_w, image_h = image_size
    normalized_fit = str(fit).strip().lower()
    if normalized_fit == "stretch" or image_w <= 0 or image_h <= 0:
        return (0, 0, screen_w, screen_h)
    if normalized_fit == "contain":
        scale = min(screen_w / image_w, screen_h / image_h)
    else:
        scale = max(screen_w / image_w, screen_h / image_h)
    width = max(1, int(image_w * scale))
    height = max(1, int(image_h * scale))
    return ((screen_w - width) // 2, (screen_h - height) // 2, width, height)
