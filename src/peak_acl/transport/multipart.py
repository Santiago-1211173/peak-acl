from __future__ import annotations
from typing import Tuple
from aiohttp import MultipartWriter, hdrs
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
    """Corpo multipart já pronto + boundary usado."""
    acl_str = dumps(msg)
    env = Envelope(
        to_=to_ai,
        from_=from_ai,
        date=datetime.now(timezone.utc),
        payload_length=len(acl_str.encode()),
    )

    boundary = f"BOUNDARY-{uuid.uuid4().hex[:12]}"
    parts = [
        f"--{boundary}",
        "Content-Type: application/xml",
        "",
        env.to_xml(),
        f"--{boundary}",
        "Content-Type: text/plain",
        "",
        acl_str,
        f"--{boundary}--",
        "",
    ]
    body = CRLF.join(parts).encode("utf-8")

    header = f'multipart/mixed; boundary="{boundary}"'
    return body, header
