from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator

@dataclass
class AclMessage:
    """Representa uma mensagem FIPA-ACL já parseada."""
    performative: str
    params: Dict[str, Any] = field(default_factory=dict)

    # acesso directo tipo dicionário
    def __getitem__(self, key: str) -> Any:            # msg["sender"]
        return self.params[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.params[key] = value

    def __iter__(self) -> Iterator[str]:
        return iter(self.params)

    # representação legível (override de dataclass gera automática mas afinamos)
    def __repr__(self) -> str:
        return f"AclMessage({self.performative!r}, {self.params})"
