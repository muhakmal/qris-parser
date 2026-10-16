"""Unit tests for QR image generation and error handling."""

import importlib.util
import os

from qris_parser.core import QRIS
from qris_parser.image import generate_qr_image
from tests.test_mpm import make_sample_qris


def test_generate_image_or_clean_importerror():
    sample = make_sample_qris()
    has_qrcode = importlib.util.find_spec("qrcode") is not None

    if has_qrcode:
        out_path = "tests/test_output.png"
        try:
            res = generate_qr_image(sample, out_path)
            assert res == out_path
            assert os.path.exists(out_path)
            assert os.path.getsize(out_path) > 0
        finally:
            if os.path.exists(out_path):
                os.remove(out_path)
    else:
        try:
            generate_qr_image(sample, "dummy.png")
            assert False, "Should have raised ImportError"
        except ImportError as e:
            assert "pip install" in str(e)


def test_qris_save_image_method():
    sample = make_sample_qris()
    qris = QRIS.parse(sample)
    has_qrcode = importlib.util.find_spec("qrcode") is not None

    if has_qrcode:
        out_path = "tests/test_qris_obj.png"
        try:
            res = qris.save_image(out_path)
            assert res == out_path
            assert os.path.exists(out_path)
        finally:
            if os.path.exists(out_path):
                os.remove(out_path)
    else:
        try:
            qris.save_image("dummy.png")
            assert False, "Should have raised ImportError"
        except ImportError as e:
            assert "pip install" in str(e)
