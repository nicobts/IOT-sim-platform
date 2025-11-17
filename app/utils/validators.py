"""
Custom validators for data validation.
"""

import re
from typing import Optional


def validate_iccid(iccid: str) -> bool:
    """
    Validate ICCID format.

    ICCID format: 19-20 digits
    Example: 8944501234567890123

    Args:
        iccid: ICCID to validate

    Returns:
        True if valid, False otherwise
    """
    if not iccid:
        return False

    # Remove spaces and dashes
    iccid = iccid.replace(" ", "").replace("-", "")

    # Check length and digits only
    if not (19 <= len(iccid) <= 20) or not iccid.isdigit():
        return False

    return True


def validate_imsi(imsi: str) -> bool:
    """
    Validate IMSI format.

    IMSI format: 14-15 digits
    Example: 123456789012345

    Args:
        imsi: IMSI to validate

    Returns:
        True if valid, False otherwise
    """
    if not imsi:
        return False

    # Check length and digits only
    if not (14 <= len(imsi) <= 15) or not imsi.isdigit():
        return False

    return True


def validate_msisdn(msisdn: str) -> bool:
    """
    Validate MSISDN (phone number) format.

    Accepts various formats:
    - +1234567890
    - 1234567890
    - +1 234 567 890

    Args:
        msisdn: MSISDN to validate

    Returns:
        True if valid, False otherwise
    """
    if not msisdn:
        return False

    # Remove spaces, dashes, and parentheses
    cleaned = re.sub(r"[\s\-\(\)]", "", msisdn)

    # Check if it starts with + (optional) and contains only digits
    pattern = r"^\+?\d{7,15}$"
    return bool(re.match(pattern, cleaned))


def validate_imei(imei: str) -> bool:
    """
    Validate IMEI format using Luhn algorithm.

    IMEI format: 15 digits

    Args:
        imei: IMEI to validate

    Returns:
        True if valid, False otherwise
    """
    if not imei or not imei.isdigit() or len(imei) != 15:
        return False

    # Luhn algorithm validation
    def luhn_checksum(number: str) -> bool:
        digits = [int(d) for d in number]
        checksum = 0

        # Process digits from right to left
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:  # Every second digit from the right
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit

        return checksum % 10 == 0

    return luhn_checksum(imei)


def validate_ip_address(ip: str) -> bool:
    """
    Validate IPv4 or IPv6 address.

    Args:
        ip: IP address to validate

    Returns:
        True if valid, False otherwise
    """
    if not ip:
        return False

    # IPv4 pattern
    ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"

    # IPv6 pattern (simplified)
    ipv6_pattern = r"^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4})$"

    return bool(re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip))


def sanitize_label(label: str, max_length: int = 255) -> str:
    """
    Sanitize label string.

    Args:
        label: Label to sanitize
        max_length: Maximum length

    Returns:
        Sanitized label
    """
    if not label:
        return ""

    # Remove leading/trailing whitespace
    label = label.strip()

    # Remove multiple consecutive spaces
    label = re.sub(r"\s+", " ", label)

    # Truncate to max length
    if len(label) > max_length:
        label = label[:max_length]

    return label


def parse_page_params(
    page: Optional[int] = None, page_size: Optional[int] = None
) -> tuple[int, int]:
    """
    Parse and validate pagination parameters.

    Args:
        page: Page number (1-indexed)
        page_size: Items per page

    Returns:
        Tuple of (page, page_size) with validated values
    """
    # Default values
    default_page = 1
    default_page_size = 100
    max_page_size = 1000

    # Validate page
    if page is None or page < 1:
        page = default_page

    # Validate page_size
    if page_size is None or page_size < 1:
        page_size = default_page_size
    elif page_size > max_page_size:
        page_size = max_page_size

    return page, page_size
