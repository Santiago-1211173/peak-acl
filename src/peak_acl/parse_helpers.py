# src/peak_acl/parse_helpers.py
"""
Funções auxiliares usadas pelo visitor ANTLR para converter valores
parseados (Atoms, ListValue, NestedMessage) para estruturas FIPA:
AgentIdentifier, listas de AID, datas reply-by, etc.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, List, Optional

from .message.aid import AgentIdentifier
from .message.acl import AclMessage


def _is_list(v: Any) -> bool:
    return isinstance(v, list)


def _is_acl(v: Any) -> bool:
    return isinstance(v, AclMessage)


# --------------------------------------------------------------------------- #
#  AID
# --------------------------------------------------------------------------- #
def to_aid(value: Any) -> AgentIdentifier:
    """
    Converte um valor ANTLR (AclMessage com performative 'agent-identifier')
    num AgentIdentifier. Formatos aceitáveis:

    (agent-identifier :name foo@host:port/JADE
                       :addresses (sequence http://... http://...))
    """
    if not _is_acl(value):
        raise TypeError(f"Esperava message agent-identifier; recebi {type(value)!r}")

    msg: AclMessage = value
    if msg.performative.lower() != "agent-identifier":
        raise ValueError("Nested message não é agent-identifier")

    name = None
    addrs: List[str] = []

    # msg.user_params contém slots; msg.content não usado aqui
    for k, v in msg.user_params.items():
        lk = k.lower()
        if lk == "name":
            # valor é Atom (string)
            name = str(v)
        elif lk == "addresses":
            addrs = _sequence_to_strings(v)
        # resolvers ignorado para já

    if name is None:
        raise ValueError("agent-identifier sem :name")

    return AgentIdentifier(name, addrs)


def _sequence_to_strings(v: Any) -> List[str]:
    """
    Espera formato: ['(', 'sequence', 'http://...', 'http://...', ')'] já
    convertido pelo visitor como ['sequence', 'http://...', ...] ou semelhante.
    Na nossa gramática, (sequence url ...) chega como lista Python onde
    o primeiro elemento é string 'sequence'.
    """
    if not _is_list(v):
        # às vezes JADE envia um único endereço sem (sequence ...)
        return [str(v)]
    if len(v) >= 2 and isinstance(v[0], str) and v[0].lower() == "sequence":
        return [str(x) for x in v[1:]]
    # else: já é lista de urls
    return [str(x) for x in v]


# --------------------------------------------------------------------------- #
#  Lista de AIDs (receiver, reply-to)
# --------------------------------------------------------------------------- #
def to_aid_list(value: Any) -> List[AgentIdentifier]:
    """
    Converte (set <aid> <aid> ...) → [AgentIdentifier,...]
    Aceita também single AID (JADE tolera).
    """
    if _is_acl(value):
        return [to_aid(value)]
    if _is_list(value):
        vals = value
        if vals and isinstance(vals[0], str) and vals[0].lower() == "set":
            vals = vals[1:]
        return [to_aid(v) for v in vals]
    raise TypeError(f"Não consigo converter {value!r} em lista de AIDs")


# --------------------------------------------------------------------------- #
#  reply-by datetime
# --------------------------------------------------------------------------- #
def to_datetime(v: Any) -> Optional[datetime]:
    """
    Aceita string FIPA/ISO e devolve datetime; se parsing falhar devolve None.
    JADE usa ISO8601 (vários formatos), p.ex. 20250715T103845 (ou com Z).
    """
    if v is None:
        return None
    s = str(v).strip().strip('"')
    # formatos comuns
    for fmt in ("%Y%m%dT%H%M%S", "%Y%m%dZ%H%M%S", "%Y-%m-%dT%H:%M:%S", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None
