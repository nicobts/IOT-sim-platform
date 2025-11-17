"""
Unit tests for validation utilities.
"""

import pytest

from app.utils.validators import (
    parse_page_params,
    validate_iccid,
    validate_imei,
    validate_imsi,
    validate_ip_address,
)


class TestICCIDValidation:
    """Tests for ICCID validation."""

    def test_validate_iccid_valid(self):
        """Test ICCID validation with valid ICCID."""
        valid_iccids = [
            "8991101200003204514",
            "89148000000060671234",
            "8901260222102053049",
        ]

        for iccid in valid_iccids:
            assert validate_iccid(iccid) is True

    def test_validate_iccid_invalid_length(self):
        """Test ICCID validation with invalid length."""
        invalid_iccids = [
            "123",  # Too short
            "12345678901234567890123",  # Too long
        ]

        for iccid in invalid_iccids:
            assert validate_iccid(iccid) is False

    def test_validate_iccid_non_numeric(self):
        """Test ICCID validation with non-numeric characters."""
        assert validate_iccid("ABC1234567890123456") is False

    def test_validate_iccid_empty(self):
        """Test ICCID validation with empty string."""
        assert validate_iccid("") is False


class TestIMSIValidation:
    """Tests for IMSI validation."""

    def test_validate_imsi_valid(self):
        """Test IMSI validation with valid IMSI."""
        valid_imsis = [
            "310150123456789",  # US AT&T
            "262011234567890",  # Germany T-Mobile
            "234101234567890",  # UK O2
        ]

        for imsi in valid_imsis:
            assert validate_imsi(imsi) is True

    def test_validate_imsi_invalid_length(self):
        """Test IMSI validation with invalid length."""
        invalid_imsis = [
            "12345",  # Too short
            "12345678901234567",  # Too long
        ]

        for imsi in invalid_imsis:
            assert validate_imsi(imsi) is False

    def test_validate_imsi_non_numeric(self):
        """Test IMSI validation with non-numeric characters."""
        assert validate_imsi("ABC123456789012") is False


class TestIMEIValidation:
    """Tests for IMEI validation."""

    def test_validate_imei_valid(self):
        """Test IMEI validation with valid IMEI."""
        valid_imeis = [
            "490154203237518",  # Valid IMEI (Luhn checksum valid)
            "352099001761481",  # Valid IMEI
        ]

        for imei in valid_imeis:
            assert validate_imei(imei) is True

    def test_validate_imei_invalid_length(self):
        """Test IMEI validation with invalid length."""
        invalid_imeis = [
            "123456",  # Too short
            "12345678901234567",  # Too long
        ]

        for imei in invalid_imeis:
            assert validate_imei(imei) is False

    def test_validate_imei_non_numeric(self):
        """Test IMEI validation with non-numeric characters."""
        assert validate_imei("ABC12345678901") is False

    def test_validate_imei_invalid_checksum(self):
        """Test IMEI validation with invalid Luhn checksum."""
        # Valid format but invalid checksum
        assert validate_imei("490154203237519") is False


class TestIPAddressValidation:
    """Tests for IP address validation."""

    def test_validate_ipv4_valid(self):
        """Test IPv4 validation with valid addresses."""
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "8.8.8.8",
        ]

        for ip in valid_ips:
            assert validate_ip_address(ip) is True

    def test_validate_ipv6_valid(self):
        """Test IPv6 validation with valid addresses."""
        valid_ips = [
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "2001:db8::1",
            "::1",
            "fe80::1",
        ]

        for ip in valid_ips:
            assert validate_ip_address(ip) is True

    def test_validate_ip_invalid(self):
        """Test IP validation with invalid addresses."""
        invalid_ips = [
            "256.1.1.1",  # Invalid octet
            "192.168.1",  # Missing octet
            "192.168.1.1.1",  # Too many octets
            "invalid",  # Not an IP
            "",  # Empty
        ]

        for ip in invalid_ips:
            assert validate_ip_address(ip) is False


class TestPaginationHelpers:
    """Tests for pagination helper functions."""

    def test_parse_page_params_default(self):
        """Test parsing page parameters with defaults."""
        page, page_size = parse_page_params(1, 100)

        assert page == 1
        assert page_size == 100

    def test_parse_page_params_custom(self):
        """Test parsing page parameters with custom values."""
        page, page_size = parse_page_params(5, 50)

        assert page == 5
        assert page_size == 50

    def test_parse_page_params_min_values(self):
        """Test parsing page parameters enforces minimum values."""
        page, page_size = parse_page_params(0, 0)

        assert page == 1  # Min page is 1
        assert page_size == 1  # Min page_size is 1

    def test_parse_page_params_max_values(self):
        """Test parsing page parameters enforces maximum values."""
        page, page_size = parse_page_params(999999, 999999)

        assert page == 999999  # No max on page
        assert page_size == 1000  # Max page_size is 1000
