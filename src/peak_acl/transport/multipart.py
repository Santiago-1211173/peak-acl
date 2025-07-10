from __future__ import annotations
from typing import Tuple
from aiohttp import MultipartWriter, hdrs
from datetime import datetime, timezone
import uuid

from ..serialize import dumps
from ..message.aid import AgentIdentifier
from ..message.envelope import Envelope
from ..message.acl import AclMessage


def build_multipart(to_ai: AgentIdentifier,
                    from_ai: AgentIdentifier,
                    msg: AclMessage) -> Tuple[MultipartWriter, str]:
    acl_str = dumps(msg)
    env = Envelope(...)

    boundary = f"BOUNDARY-{uuid.uuid4().hex[:16]}"
    writer   = MultipartWriter("mixed", boundary=boundary)

    writer.append(env.to_xml(),
                  headers={"Content-Type": "application/xml",
                           "Content-Disposition": 'attachment; name="envelope"'})
    writer.append(acl_str,
                  headers={"Content-Type": "text/plain",
                           "Content-Disposition": 'attachment; name="acl-message"'})

    # -- remove o header default e coloca a versão com ASPAS
    del writer.headers[hdrs.CONTENT_TYPE]
    writer.headers[hdrs.CONTENT_TYPE] = f'multipart/mixed; boundary="{boundary}"'

    return writer, boundary
