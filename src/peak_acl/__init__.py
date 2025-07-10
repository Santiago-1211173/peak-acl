"""
peak_acl · FIPA-ACL parser and transport helpers for the PEAK framework.
"""

from importlib.metadata import version as _version, PackageNotFoundError

# ─────────────────────────── API pública ────────────────────────────

from .parse import parse
from .message.acl import AclMessage  # <- cria esta classe em message/acl.py
from .serialize import dumps


__all__: list[str] = [
    "parse",
    "AclMessage",
    "__version__",
]

__all__.append("dumps")

# ─────────────────────────── Metadados ───────────────────────────────

try:
    # Versão lida a partir do pacote instalado (funciona após build/instalação)
    __version__: str = _version("peak-acl")
except PackageNotFoundError:
    # Durante o desenvolvimento (pip install -e .) o wheel ainda não existe
    __version__ = "0.0.0"
