# peak_acl/util/net.py
from __future__ import annotations
import socket

__all__ = ["discover_ip"]

def discover_ip() -> str:
    """IP local roteável (hack de UDP a 8.8.8.8)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()
