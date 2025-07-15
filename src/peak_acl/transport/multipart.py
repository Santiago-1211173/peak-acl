from __future__ import annotations
from typing import Tuple
from datetime import datetime, timezone
import uuid

from ..serialize import dumps
from ..message.aid import AgentIdentifier
from ..message.envelope import Envelope
from ..message.acl import AclMessage

CRLF = "\r\n"


def build_multipart(
    to_ai: AgentIdentifier,
    from_ai: AgentIdentifier,
    msg: AclMessage,
) -> Tuple[bytes, str]:
    """
    Constrói o corpo multipart/mixed (bytes) e devolve
    também o valor correcto do cabeçalho Content-Type.
    """
    acl_str = dumps(msg)
    env_xml = Envelope(
        to_=to_ai,
        from_=from_ai,
        date=datetime.now(timezone.utc),
        payload_length=len(acl_str.encode()),
    ).to_xml()

    boundary = f"BOUNDARY-{uuid.uuid4().hex[:12]}"

    parts = [
        "--" + boundary,
        "Content-Type: application/xml",
        "",
        "",
        env_xml,
        "--" + boundary,
        "Content-Type: text/plain",
        "",
        "",
        acl_str,
        f"--{boundary}--",
        "",
    ]
    body = CRLF.join(parts).encode("utf-8")
    ctype = f'multipart/mixed; boundary="{boundary}"'
    return body, ctype
