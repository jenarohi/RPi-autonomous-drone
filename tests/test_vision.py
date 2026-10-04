"""Vision unit tests: QR detection, payload parsing, and banner detector."""
import numpy as np
import pytest

from skyscan.geo import CameraModel
from skyscan.sim.textures import banner_image, qr_image
from skyscan.types import Frame
from skyscan.vision.banner import BannerDetector
from skyscan.vision.qr import QRScanner, parse_qr_payload


def test_parse_qr_payload():
    # JSON payload
    p1 = parse_qr_payload('{"target": "C", "zone": "DELIVERY-C"}')
    assert p1.valid and p1.target == "C" and p1.kind == "json"

    # Key-value payload
    p2 = parse_qr_payload("TARGET: B, LAT: 12.34, LON: 78.56")
    assert p2.valid and p2.target == "B" and p2.kind == "kv"

    # Simple target string
    p3 = parse_qr_payload("DELIVERY-A")
    assert p3.valid and p3.target == "A"

    p4 = parse_qr_payload("TARGET_D")
    assert p4.valid and p4.target == "D"

    # Empty payload
    p5 = parse_qr_payload("")
    assert not p5.valid


def test_qr_scanner_synthetic():
    scanner = QRScanner(type("Cfg", (), {"confirm_votes": 2, "vote_window_s": 10.0, "upscale_below_px": 100.0}))
    scanner.reset(1)

    img = qr_image('{"target": "C"}', px=400)
    frame = Frame(cam="down", seq=1, t=100.0, img=img)
    cam_model = CameraModel.from_hfov(400, 400, 60.0)

    det = scanner.scan(frame, camera_model=cam_model, rel_alt_m=5.0)
    assert det.found and det.text is not None
    assert "target" in det.text

    # Second frame to reach 2 votes
    det2 = scanner.scan(Frame(cam="down", seq=2, t=100.5, img=img), camera_model=cam_model, rel_alt_m=5.0)
    status = scanner.status()
    assert status.confirmed is not None
    assert status.payload and status.payload.target == "C"


def test_banner_detector_synthetic():
    class BannerCfg:
        size_m = [3.0, 1.0]
        hsv_lo = [40, 80, 50]
        hsv_hi = [85, 255, 255]
        min_area_frac = 0.001
        max_area_frac = 0.8
        aspect_range = [1.5, 6.0]
        min_fill = 0.6
        text_ratio_range = [0.01, 0.6]
        plane_tilt_max_deg = 35.0
        min_score = 0.4

    detector = BannerDetector(BannerCfg())

    # Generate synthetic banner on black background
    bg = np.zeros((720, 1280, 3), dtype=np.uint8)
    banner = banner_image(width_px=600, height_px=200)
    # Paste centered
    y0, x0 = (720 - 200) // 2, (1280 - 600) // 2
    bg[y0:y0 + 200, x0:x0 + 600] = banner

    frame = Frame(cam="front", seq=1, t=10.0, img=bg)
    cam_model = CameraModel.from_hfov(1280, 720, 74.5)

    det = detector.detect(frame, camera_model=cam_model, gimbal_pitch_deg=0.0)
    assert det.found, f"Banner not detected: {det.reason}"
    assert det.distance_m is not None and det.distance_m > 0
    assert det.plane_ok is True
