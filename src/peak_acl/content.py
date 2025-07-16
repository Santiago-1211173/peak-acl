# src/peak_acl/content.py
"""
Helpers para decodificar content consoante language.
"""

from __future__ import annotations
from typing import Any

from .message.acl import AclMessage
from . import sl0

def decode_content(msg: AclMessage):
    """
    Se language começar por 'fipa-sl' e content for string que começa por '(',
    tenta parse SL0; em caso de erro devolve a string original.
    """
    c = msg.content
    if isinstance(c, str) and msg.language and msg.language.lower().startswith("fipa-sl"):
        txt = c.strip()
        if txt.startswith("(") and txt.endswith(")"):
            try:
                return sl0.loads(txt)
            except Exception:
                pass
    return c
