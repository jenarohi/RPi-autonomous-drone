"""Procedural course textures shared by the Gazebo world builder and the vision tests.

Keeping one generator guarantees the simulated AeroTHON banner / QR codes and the synthetic test
images are identical. All functions return BGR uint8 images (OpenCV convention).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

#: Banner background ("AeroTHON 2026 Banner with Green Background"), BGR.
BANNER_GREEN_BGR = (70, 150, 0)
_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
)


def _font(size: int):
    from PIL import ImageFont
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _draw_text_centered(img: np.ndarray, text: str, cy: float, height_px: int, color=(255, 255, 255),
                        max_width_px: int | None = None) -> np.ndarray:
    """Draw ``text`` centred horizontally with its cap height ≈ ``height_px`` at row ``cy``."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:  # OpenCV fallback (cruder glyphs)
        import cv2
        scale = height_px / 22.0
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, scale, max(1, int(scale * 2)))
        org = (int((img.shape[1] - tw) / 2), int(cy + th / 2))
        cv2.putText(img, text, org, cv2.FONT_HERSHEY_DUPLEX, scale, color[::-1], max(1, int(scale * 2)), cv2.LINE_AA)
        return img
    pil = Image.fromarray(img[:, :, ::-1].copy())
    draw = ImageDraw.Draw(pil)
    size = int(height_px * 1.35)
    font = _font(size)
    box = draw.textbbox((0, 0), text, font=font)
    if max_width_px and box[2] - box[0] > max_width_px:
        size = int(size * max_width_px / (box[2] - box[0]))
        font = _font(size)
        box = draw.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    draw.text(((img.shape[1] - tw) / 2 - box[0], cy - th / 2 - box[1]), text, font=font, fill=tuple(color))
    return np.asarray(pil)[:, :, ::-1].copy()


def banner_image(width_px: int = 1500, height_px: int = 500, title: str = "AeroTHON 2026",
                 subtitle: str = "CORRIDOR ENTRANCE", bg_bgr: tuple[int, int, int] = BANNER_GREEN_BGR) -> np.ndarray:
    """The AeroTHON 2026 banner: green background, white border inset, white title + subtitle."""
    import cv2
    img = np.zeros((height_px, width_px, 3), np.uint8)
    img[:] = bg_bgr
    inset = max(4, height_px // 25)
    thick = max(2, height_px // 60)
    cv2.rectangle(img, (inset, inset), (width_px - 1 - inset, height_px - 1 - inset), (255, 255, 255), thick)
    img = _draw_text_centered(img, title, height_px * 0.42, int(height_px * 0.30), max_width_px=int(width_px * 0.86))
    if subtitle:
        img = _draw_text_centered(img, subtitle, height_px * 0.76, int(height_px * 0.09),
                                  max_width_px=int(width_px * 0.6))
    return img


def qr_image(text: str, px: int = 600, quiet_modules: int = 4) -> np.ndarray:
    """Black-on-white QR code of ``text``, ``px`` square including a ``quiet_modules`` white border."""
    import cv2
    modules: np.ndarray
    try:
        import qrcode
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=0)
        qr.add_data(text)
        qr.make(fit=True)
        modules = np.array(qr.get_matrix(), dtype=bool)
    except ImportError:
        enc = cv2.QRCodeEncoder.create()
        raw = enc.encode(text)
        dark = raw < 128
        rows, cols = np.where(dark)
        modules = dark[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
    n = modules.shape[0] + 2 * quiet_modules
    grid = np.ones((n, n), np.uint8) * 255
    grid[quiet_modules:quiet_modules + modules.shape[0], quiet_modules:quiet_modules + modules.shape[1]][modules] = 0
    img = cv2.resize(grid, (px, px), interpolation=cv2.INTER_NEAREST)
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)


def grass_image(px: int = 1024, seed: int = 0) -> np.ndarray:
    """Muted, mottled grass. Deliberately inside the banner's green hue range: a realistic distractor."""
    import cv2
    rng = np.random.default_rng(seed)
    base = np.array([45, 100, 70], np.float32)                     # BGR
    noise = rng.normal(0, 1, (px // 8, px // 8, 1)).astype(np.float32)
    noise = cv2.resize(noise, (px, px), interpolation=cv2.INTER_CUBIC)[:, :, None]
    fine = rng.normal(0, 1, (px, px, 1)).astype(np.float32)
    img = base + noise * np.array([8, 18, 10], np.float32) + fine * np.array([5, 9, 6], np.float32)
    return np.clip(img, 0, 255).astype(np.uint8)


def pad_image(px: int = 512) -> np.ndarray:
    """Take-off pad: grey square, white circle, white "H"."""
    import cv2
    img = np.full((px, px, 3), (90, 90, 90), np.uint8)
    c = px // 2
    cv2.circle(img, (c, c), int(px * 0.42), (255, 255, 255), max(3, px // 40), cv2.LINE_AA)
    w, h, t = int(px * 0.34), int(px * 0.44), int(px * 0.08)
    x0, y0 = c - w // 2, c - h // 2
    cv2.rectangle(img, (x0, y0), (x0 + t, y0 + h), (255, 255, 255), -1)
    cv2.rectangle(img, (x0 + w - t, y0), (x0 + w, y0 + h), (255, 255, 255), -1)
    cv2.rectangle(img, (x0, c - t // 2), (x0 + w, c + t // 2), (255, 255, 255), -1)
    return img


def solid_image(bgr: tuple[int, int, int], px: int = 64) -> np.ndarray:
    img = np.zeros((px, px, 3), np.uint8)
    img[:] = bgr
    return img


def save_png(path: str | Path, img: np.ndarray) -> Path:
    import cv2
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(p), img):
        raise OSError(f"could not write {p}")
    return p
