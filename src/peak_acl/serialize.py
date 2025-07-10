from __future__ import annotations
from .message.acl import AclMessage
from .types import QuotedStr

def dumps(msg: AclMessage) -> str:
    """AclMessage → string ACL (s-expression)."""

    def _fmt(v):
        if isinstance(v, AclMessage):
            return dumps(v)
        if isinstance(v, list):
            return '(' + ' '.join(map(_fmt, v)) + ')'
        if isinstance(v, QuotedStr):
            esc = v.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{esc}"'
        return str(v)

    parts = ['(', msg.performative]
    for k, v in msg.params.items():
        parts.append(f' :{k} {_fmt(v)}')
    parts.append(')')
    return ''.join(parts)
