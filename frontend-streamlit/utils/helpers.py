import streamlit as st
from typing import Optional


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable format"""
    if bytes_value == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    value = float(bytes_value)

    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1

    return f"{value:.2f} {units[unit_index]}"


def show_success(message: str):
    """Show success message"""
    st.success(f"✅ {message}")


def show_error(message: str):
    """Show error message"""
    st.error(f"❌ {message}")


def show_warning(message: str):
    """Show warning message"""
    st.warning(f"⚠️ {message}")


def show_info(message: str):
    """Show info message"""
    st.info(f"ℹ️ {message}")


def require_auth(func):
    """Decorator to require authentication"""
    def wrapper(*args, **kwargs):
        if "authenticated" not in st.session_state or not st.session_state.authenticated:
            st.warning("Please login first")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def get_status_color(status: str) -> str:
    """Get color for status badge"""
    status_colors = {
        "ACTIVATED": "green",
        "ENABLED": "green",
        "ACTIVE": "green",
        "DISABLED": "red",
        "SUSPENDED": "orange",
        "DEACTIVATED": "red",
        "TERMINATED": "gray",
    }
    return status_colors.get(status.upper(), "blue")


def format_status_badge(status: str) -> str:
    """Format status as colored badge"""
    color = get_status_color(status)
    return f":{color}[{status}]"
