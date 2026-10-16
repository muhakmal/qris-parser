"""QR Code image generation utilities for QRIS payloads."""



def generate_qr_image(payload: str, output_path: str, box_size: int = 10, border: int = 4) -> str:
    """Generate a PNG image file for a given QRIS payload.

    Requires the optional 'qrcode[pil]' package.
    Install with:
        pip install "qris-parser[image]"

    Args:
        payload: QRIS raw string.
        output_path: Path where the generated image will be saved (e.g. 'qris.png').
        box_size: Number of pixels per QR code module (default: 10).
        border: Border margin in modules (default: 4).

    Returns:
        The output_path of the saved image.
    """
    try:
        import qrcode
    except ImportError:
        raise ImportError(
            "The 'qrcode[pil]' package is required to render QR code images. "
            "Install it using: pip install 'qris-parser[image]'"
        )

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)
    return output_path
