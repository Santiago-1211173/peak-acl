from __future__ import annotations
from typing import Tuple
from aiohttp import MultipartWriter, hdrs
from datetime import datetime, timezone
import uuid

from ..serialize import dumps
from ..message.aid import AgentIdentifier
from ..message.envelope import Envelope
from ..message.acl import AclMessage


def build_multipart(
    to_ai: AgentIdentifier,
    from_ai: AgentIdentifier,
    msg: AclMessage,
) -> Tuple[MultipartWriter, str]:
    """Devolve (writer, boundary) com o Content-Type já correcto."""
    acl_str = dumps(msg)

    env = Envelope(
        to_=to_ai,
        from_=from_ai,
        date=datetime.now(timezone.utc),
        payload_length=len(acl_str.encode()),
    )

    # -------- boundary explícito  -----------------------------------
    boundary = f"BOUNDARY-{uuid.uuid4().hex[:16]}"
    writer = MultipartWriter("mixed", boundary=boundary)

    # part 1: envelope XML
    writer.append(
        env.to_xml(),
        headers={
            "Content-Type": "application/xml",
            "Content-Disposition": 'attachment; name="envelope"; filename="envelope.xml"',
        },
    )

    # part 2: ACL string
    writer.append(
        acl_str,
        headers={
            "Content-Type": "text/plain",
            "Content-Disposition": 'attachment; name="acl-message"; filename="acl.txt"',
        },
    )

    # -------- header Content-Type COM aspas --------------------------
    writer.headers[hdrs.CONTENT_TYPE] = (
        f'multipart/mixed; boundary="{boundary}"'
    )

    return writer, boundary
