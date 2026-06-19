import numpy as np
import pytest

from src.services.cnn_predictor import _he_stain_sanity


def make_colored_image(color_bgr, size=(200, 200)):
    import cv2
    img = np.full((size[1], size[0], 3), color_bgr, dtype=np.uint8)
    success, buffer = cv2.imencode('.jpg', img)
    assert success, 'Failed to encode test image'
    return buffer.tobytes()


def test_he_stain_rejects_non_histology_image():
    image_bytes = make_colored_image((0, 255, 0))
    ok, reason = _he_stain_sanity(image_bytes)
    assert not ok
    assert 'H&E stain' in reason or 'Rejected' in reason


def test_he_stain_accepts_he_like_image():
    import cv2
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    img[:100, :] = (180, 0, 180)  # purple-ish BGR
    img[100:, :] = (220, 130, 180)  # pink-ish BGR
    success, buffer = cv2.imencode('.jpg', img)
    assert success
    ok, reason = _he_stain_sanity(buffer.tobytes())
    assert ok
    assert 'H&E stain' in reason
