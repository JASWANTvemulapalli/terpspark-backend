"""
QR Code generation utility for event tickets.
Generates QR codes containing ticket codes for check-in.
"""
import qrcode
import io
import base64
from PIL import Image


def generate_qr_code(ticket_code: str) -> str:
    """
    Generate QR code from ticket code and return as base64 string.

    The QR code will be displayed on the user's ticket and scanned at event check-in.

    Args:
        ticket_code: The unique ticket code to encode (e.g., "TKT-1732635421-abc123")

    Returns:
        str: Base64 encoded QR code image in format "data:image/png;base64,..."

    Example:
        >>> ticket_code = "TKT-1732635421-abc123"
        >>> qr_code = generate_qr_code(ticket_code)
        >>> # Returns: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgA..."
    """
    # Create QR code instance with optimal settings
    qr = qrcode.QRCode(
        version=1,  # Size of QR code (1 is smallest, auto-adjusts if needed)
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # ~7% error correction
        box_size=10,  # Size of each box in pixels
        border=4,  # Border size (minimum is 4)
    )

    # Add ticket code data to QR code
    qr.add_data(ticket_code)
    qr.make(fit=True)  # Auto-adjust size if needed

    # Generate the QR code image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert PIL Image to base64 string
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')

    # Return as data URL (can be used directly in <img> tags)
    return f"data:image/png;base64,{img_base64}"


def generate_ticket_code(timestamp: int, event_id: str) -> str:
    """
    Generate unique ticket code in standardized format.

    Format: TKT-{timestamp}-{first8chars_of_event_id}

    Args:
        timestamp: Unix timestamp (use time.time())
        event_id: Event UUID

    Returns:
        str: Formatted ticket code

    Example:
        >>> import time
        >>> event_id = "abc12345-6789-0123-4567-890123456789"
        >>> code = generate_ticket_code(int(time.time()), event_id)
        >>> print(code)
        TKT-1732635421-abc12345
    """
    # Take first 8 characters of event_id for brevity
    event_short = event_id[:8]
    return f"TKT-{timestamp}-{event_short}"
