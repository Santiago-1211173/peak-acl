from __future__ import annotations

from typing import Tuple
from aiohttp import MultipartWriter
from datetime import datetime
from ..message.aid import AgentIdentifier
from ..message.envelope import Envelope

from ..serialize import dumps
from ..message.envelope import Envelope
from ..message.acl import AclMessage

def build_multipart(to_ai: AgentIdentifier,
                    from_ai: AgentIdentifier,
                    msg: AclMessage) -> Tuple[MultipartWriter, str]:
    acl_str = dumps(msg)
    env = Envelope(
        to_=to_ai,
        from_=from_ai,
        date=datetime.utcnow(),
        payload_length=len(acl_str.encode()),
    )
    writer = MultipartWriter("mixed")
    ...
    writer.append(env.to_xml(),
                  headers={"Content-Type": "application/xml",
                           "Content-Disposition": 'attachment; name="envelope"; filename="envelope.xml"'})
    writer.append(acl_str,
                  headers={"Content-Type": "text/plain",
                           "Content-Disposition": 'attachment; name="acl-message"; filename="acl.txt"'})
    return writer, writer.boundary
