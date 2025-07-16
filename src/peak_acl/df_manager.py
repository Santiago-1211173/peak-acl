# src/peak_acl/df_manager.py
from __future__ import annotations

from typing import Iterable, Optional, Sequence, Tuple, Union, List

from .message.aid import AgentIdentifier
from .message.acl import AclMessage
from .transport.http_client import HttpMtpClient
from .content import decode_content
from . import sl0, fipa_am

__all__ = [
    "register", "deregister", "search_services",
    "decode_df_reply", "is_df_done_msg", "is_df_failure_msg",
    "extract_search_results",
]


# ------------------------------------------------------------------ #
# util
# ------------------------------------------------------------------ #
def _first_url(ai: AgentIdentifier) -> str:
    if not ai.addresses:
        raise ValueError(f"AID sem endereço HTTP: {ai}")
    return ai.addresses[0]


def _coerce_services(
    raw: Iterable[Union[Tuple[str, str], fipa_am.ServiceDescription]],
) -> list[fipa_am.ServiceDescription]:
    out: list[fipa_am.ServiceDescription] = []
    for item in raw:
        if isinstance(item, fipa_am.ServiceDescription):
            out.append(item)
        else:
            n, t = item
            out.append(fipa_am.ServiceDescription(name=n, type=t))
    return out


# ------------------------------------------------------------------ #
# builders + envio
# ------------------------------------------------------------------ #
async def register(
    *,
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    services: Iterable[Union[Tuple[str, str], fipa_am.ServiceDescription]] = (),
    languages: Sequence[str] = (),
    ontologies: Sequence[str] = (),
    protocols: Sequence[str] = (),
    ownership: Sequence[str] = (),
    http_client: HttpMtpClient,
) -> AclMessage:
    svc_objs = _coerce_services(services)
    ad = fipa_am.build_agent_description(
        aid=my_aid,
        services=svc_objs,
        languages=languages,
        ontologies=ontologies,
        protocols=protocols,
        ownership=ownership,
    )
    content = fipa_am.render_register_content(df_aid, ad)
    msg = AclMessage(
        performative="request",
        sender=my_aid,
        receivers=[df_aid],
        content=content,
        language="fipa-sl0",
        ontology="FIPA-Agent-Management",
        protocol="fipa-request",
    )
    await http_client.send(df_aid, my_aid, msg, _first_url(df_aid))
    return msg


async def deregister(
    *,
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    http_client: HttpMtpClient,
) -> AclMessage:
    ad = fipa_am.AgentDescription(name=my_aid)
    inner = sl0.Action(actor=df_aid, act=sl0.Deregister(sl0.DfAgentDescription(name=my_aid)))
    msg = AclMessage(
        performative="request",
        sender=my_aid,
        receivers=[df_aid],
        content=sl0.dumps(inner),
        language="fipa-sl0",
        ontology="FIPA-Agent-Management",
        protocol="fipa-request",
    )
    await http_client.send(df_aid, my_aid, msg, _first_url(df_aid))
    return msg


async def search_services(
    *,
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    service_name: Optional[str] = None,
    service_type: Optional[str] = None,
    max_results: Optional[int] = None,
    http_client: HttpMtpClient,
) -> AclMessage:
    tmpl = sl0.DfAgentDescription(
        name=None,
        services=[
            sl0.ServiceDescription(name=service_name, type=service_type)
        ] if (service_name is not None or service_type is not None) else [],
    )
    inner = sl0.Action(actor=df_aid, act=sl0.Search(tmpl, max_results=max_results))
    msg = AclMessage(
        performative="request",
        sender=my_aid,
        receivers=[df_aid],
        content=sl0.dumps(inner),
        language="fipa-sl0",
        ontology="FIPA-Agent-Management",
        protocol="fipa-request",
    )
    await http_client.send(df_aid, my_aid, msg, _first_url(df_aid))
    return msg


# ------------------------------------------------------------------ #
# Decodificar replies DF
# ------------------------------------------------------------------ #
def decode_df_reply(msg: AclMessage):
    """
    Converte msg.content (string) -> AST SL0 -> objetos ontologia quando aplicável.
    """
    payload = decode_content(msg)  # str -> sl0 AST (ou str se parse falhar)

    # Se parser SL0 falhou ou language != fipa-sl*, devolve raw
    if isinstance(payload, str):
        return payload

    # Se Done/Failure/Result, devolve instâncias fipa_am se possível
    if isinstance(payload, sl0.Done):
        return payload  # Done(Action(...))
    if isinstance(payload, sl0.Failure):
        return payload
    if isinstance(payload, sl0.Result):
        # tentar mapear value -> AgentDescription(s)
        val = payload.value
        ads = extract_search_results_from_value(val)
        if ads is not None:
            # devolve lista de AgentDescription
            return ads
        return payload

    # fallback
    return payload


def extract_search_results(msg: AclMessage) -> List[fipa_am.AgentDescription]:
    """
    Se a mensagem for uma resposta a search, devolve lista de AgentDescription.
    Caso contrário devolve [].
    """
    payload = decode_content(msg)
    if isinstance(payload, sl0.Result):
        ads = extract_search_results_from_value(payload.value)
        return ads or []
    return []


def extract_search_results_from_value(val) -> Optional[List[fipa_am.AgentDescription]]:
    """
    Recebe payload.value dum Result SL0; tenta extrair lista de ADs.
    """
    def _coerce(obj):
        if isinstance(obj, sl0.DfAgentDescription):
            return fipa_am._ad_from_sl0(obj)  # tipo: ignore[attr-defined]
        return None

    items: List[fipa_am.AgentDescription] = []

    # value pode ser list ['set', dfad,...] ou lista de dfad
    if isinstance(val, list):
        if val and isinstance(val[0], str) and val[0].lower() == "set":
            seq = val[1:]
        else:
            seq = val
        for it in seq:
            it2 = _coerce(it if isinstance(it, sl0.DfAgentDescription) else sl0._build_ast(it))  # noqa
            if it2:
                items.append(it2)
    elif isinstance(val, sl0.DfAgentDescription):
        items.append(fipa_am._ad_from_sl0(val))  # noqa
    else:
        return None

    return items
