"""The procedural course textures must be decodable / detectable by construction."""
import cv2
import numpy as np

from skyscan.sim import textures


def test_qr_texture_decodes():
    img = textures.qr_image("TARGET:C", px=400)
    assert img.shape == (400, 400, 3)
    assert (img[:10, :10] == 255).all()           # quiet zone
    text, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
    assert text == "TARGET:C"


def test_banner_texture_is_green_with_white_text():
    img = textures.banner_image(1200, 400)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    green = cv2.inRange(hsv, (40, 90, 60), (85, 255, 255)) > 0
    white = (hsv[:, :, 1] < 60) & (hsv[:, :, 2] > 200)
    assert 0.55 < green.mean() < 0.95
    assert 0.03 < white.mean() < 0.4
    # the title occupies the middle band
    assert white[int(400 * 0.3):int(400 * 0.55), 150:1050].mean() > white.mean()


def test_grass_and_pad():
    g = textures.grass_image(256)
    assert g.shape == (256, 256, 3) and g.std() > 3
    p = textures.pad_image(128)
    assert p.shape == (128, 128, 3) and (p == 255).any()
    assert np.array_equal(textures.solid_image((1, 2, 3), 4)[0, 0], [1, 2, 3])
