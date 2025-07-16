# src/peak_acl/fipa_am.py
"""
Objetos Python que representam a Ontologia FIPA-Agent-Management
e helpers para serializar/deserializar entre estas estruturas e o
subconjunto SL0 suportado (peak_acl.sl0).

Camada de conveniência acima do módulo sl0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from .message.aid import AgentIdentifier
from . import sl0


# ------------------------------------------------------------------ #
# Dataclasses de alto nível (API externa)
# ------------------------------------------------------------------ #
@dataclass
class Property:
    name: str
    value: str

@dataclass
class ServiceDescription:
    name: Optional[str] = None
    type: Optional[str] = None
    languages: List[str] = field(default_factory=list)
    ontologies: List[str] = field(default_factory=list)
    protocols: List[str] = field(default_factory=list)
    properties: List[Property] = field(default_factory=list)

@dataclass
class AgentDescription:
    name: Optional[AgentIdentifier] = None
    languages: List[str] = field(default_factory=list)
    ontologies: List[str] = field(default_factory=list)
    protocols: List[str] = field(default_factory=list)
    ownership: List[str] = field(default_factory=list)
    services: List[ServiceDescription] = field(default_factory=list)


# ------------------------------------------------------------------ #
# Construtores convenientes
# ------------------------------------------------------------------ #
def build_agent_description(
    *,
    aid: AgentIdentifier,
    services: Sequence[ServiceDescription] = (),
    languages: Sequence[str] = (),
    ontologies: Sequence[str] = (),
    protocols: Sequence[str] = (),
    ownership: Sequence[str] = (),
) -> AgentDescription:
    return AgentDescription(
        name=aid,
        services=list(services),
        languages=list(languages),
        ontologies=list(ontologies),
        protocols=list(protocols),
        ownership=list(ownership),
    )


# ------------------------------------------------------------------ #
# Conversão ALTO->SL0
# ------------------------------------------------------------------ #
def _svc_to_sl0(sd: ServiceDescription) -> sl0.ServiceDescription:
    return sl0.ServiceDescription(
        name=sd.name,
        type=sd.type,
        languages=list(sd.languages),
        ontologies=list(sd.ontologies),
        protocols=list(sd.protocols),
        properties=[(p.name, p.value) for p in sd.properties],
    )

def _ad_to_sl0(ad: AgentDescription) -> sl0.DfAgentDescription:
    return sl0.DfAgentDescription(
        name=ad.name,
        services=[_svc_to_sl0(s) for s in ad.services],
        languages=list(ad.languages),
        ontologies=list(ad.ontologies),
        protocols=list(ad.protocols),
        ownership=list(ad.ownership),
    )


def render_register_content(
    df_aid: AgentIdentifier,
    agent_desc: AgentDescription,
) -> str:
    """
    Constrói string SL0 *sem aspas* e *sem parênteses exteriores*;
    o serializer ACL encarrega-se de embrulhar em ContentElementList.
    """
    inner = sl0.Action(actor=df_aid, act=sl0.Register(_ad_to_sl0(agent_desc)))
    return sl0.dumps(inner)


# ------------------------------------------------------------------ #
# Conversão SL0->ALTO
# ------------------------------------------------------------------ #
def _svc_from_sl0(sd: sl0.ServiceDescription) -> ServiceDescription:
    return ServiceDescription(
        name=sd.name,
        type=sd.type,
        languages=list(sd.languages),
        ontologies=list(sd.ontologies),
        protocols=list(sd.protocols),
        properties=[Property(n, v) for (n, v) in sd.properties],
    )

def _ad_from_sl0(ad: sl0.DfAgentDescription) -> AgentDescription:
    return AgentDescription(
        name=ad.name,
        services=[_svc_from_sl0(s) for s in ad.services],
        languages=list(ad.languages),
        ontologies=list(ad.ontologies),
        protocols=list(ad.protocols),
        ownership=list(ad.ownership),
    )


def from_sl0(obj):
    """
    Converte um AST SL0 (DfAgentDescription, Result, etc.) para
    objetos AgentDescription/ServiceDescription quando aplicável.
    """
    if isinstance(obj, sl0.DfAgentDescription):
        return _ad_from_sl0(obj)
    if isinstance(obj, sl0.ServiceDescription):
        return _svc_from_sl0(obj)
    if isinstance(obj, sl0.Result):
        # DF search normalmente devolve Result(_, value=(set ...dfads...))
        value = obj.value
        if isinstance(value, list):
            # flatten
            ads = []
            for v in value:
                v = from_sl0(v)
                if isinstance(v, AgentDescription):
                    ads.append(v)
            return ads
        v2 = from_sl0(value)
        return [v2] if isinstance(v2, AgentDescription) else v2
    return obj
