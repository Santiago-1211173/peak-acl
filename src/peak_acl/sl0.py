# src/peak_acl/sl0.py
"""
Mini-implementação FIPA-SL0 suficiente para interagir com DF/AMS via JADE.

Suporta parse/serialize de:
    (action <aid> (register|deregister|modify <df-agent-description>))
    (action <aid> (search <df-agent-description> [<max-results>]))
e respostas:
    (done <expr>)
    (failure <expr>)
    (result <expr> <value>)

Também reconhece estruturas df-agent-description e service-description
com campos opcionais (languages, ontologies, protocols, properties, ...).

Nota: usamos parsing leniente; ignoramos slots desconhecidos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, List, Optional, Sequence, Tuple, Union

from .message.aid import AgentIdentifier


# ------------------------------------------------------------------ #
# AST dataclasses
# ------------------------------------------------------------------ #
@dataclass
class ServiceDescription:
    name: Optional[str] = None
    type: Optional[str] = None
    languages: List[str] = field(default_factory=list)
    ontologies: List[str] = field(default_factory=list)
    protocols: List[str] = field(default_factory=list)
    # propriedades DF arbitrárias
    properties: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class DfAgentDescription:
    name: Optional[AgentIdentifier] = None
    services: List[ServiceDescription] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    ontologies: List[str] = field(default_factory=list)
    protocols: List[str] = field(default_factory=list)
    ownership: List[str] = field(default_factory=list)


@dataclass
class Register:
    dfad: DfAgentDescription


@dataclass
class Deregister:
    dfad: DfAgentDescription


@dataclass
class Modify:
    dfad: DfAgentDescription


@dataclass
class Search:
    template: DfAgentDescription
    max_results: Optional[int] = None


@dataclass
class Action:
    actor: AgentIdentifier
    act: Union[Register, Deregister, Modify, Search]


@dataclass
class Done:
    what: Any


@dataclass
class Failure:
    reason: Any


@dataclass
class Result:
    what: Any
    value: Any


# ------------------------------------------------------------------ #
# Public helpers
# ------------------------------------------------------------------ #
def build_register_content(my: AgentIdentifier,
                           services: Sequence[Tuple[str, str]],
                           *,
                           df: AgentIdentifier) -> str:
    sd = [ServiceDescription(name=n, type=t) for n, t in services]
    expr = Action(actor=df, act=Register(DfAgentDescription(name=my, services=sd)))
    return dumps(expr)


def is_done(obj: Any) -> bool:
    return isinstance(obj, Done)


def is_failure(obj: Any) -> bool:
    return isinstance(obj, Failure)


def is_result(obj: Any) -> bool:
    return isinstance(obj, Result)


# ------------------------------------------------------------------ #
# Serializer
# ------------------------------------------------------------------ #
def dumps(obj: Any) -> str:
    return _render(obj)


def _render(obj: Any) -> str:
    if isinstance(obj, Action):
        return f"(action {_render_aid(obj.actor)} {_render(obj.act)})"
    if isinstance(obj, Register):
        return f"(register {_render_dfad(obj.dfad)})"
    if isinstance(obj, Deregister):
        return f"(deregister {_render_dfad(obj.dfad)})"
    if isinstance(obj, Modify):
        return f"(modify {_render_dfad(obj.dfad)})"
    if isinstance(obj, Search):
        tail = f" {_render_dfad(obj.template)}"
        if obj.max_results is not None:
            tail += f" {obj.max_results}"
        return f"(search{tail})"
    if isinstance(obj, Done):
        return f"(done {_render(obj.what)})"
    if isinstance(obj, Failure):
        return f"(failure {_render(obj.reason)})"
    if isinstance(obj, Result):
        return f"(result {_render(obj.what)} {_render(obj.value)})"
    if isinstance(obj, DfAgentDescription):
        return _render_dfad(obj)
    if isinstance(obj, ServiceDescription):
        return _render_sd(obj)
    if isinstance(obj, AgentIdentifier):
        return _render_aid(obj)
    return str(obj)


def _render_aid(aid: AgentIdentifier) -> str:
    if aid.addresses:
        seq = " ".join(aid.addresses)
        return f"(agent-identifier :name {aid.name} :addresses (sequence {seq}))"
    return f"(agent-identifier :name {aid.name} :addresses (sequence))"


def _render_sd(sd: ServiceDescription) -> str:
    parts = ["(service-description"]
    if sd.name is not None:
        parts.append(f" :name {sd.name}")
    if sd.type is not None:
        parts.append(f" :type {sd.type}")
    if sd.languages:
        parts.append(" :languages (set " + " ".join(sd.languages) + ")")
    if sd.ontologies:
        parts.append(" :ontologies (set " + " ".join(sd.ontologies) + ")")
    if sd.protocols:
        parts.append(" :protocols (set " + " ".join(sd.protocols) + ")")
    if sd.properties:
        props = " ".join(
            f"(property :name {n} :value {v})" for (n, v) in sd.properties
        )
        parts.append(f" :properties (set {props})")
    parts.append(")")
    return "".join(parts)


def _render_dfad(dfad: DfAgentDescription) -> str:
    parts = ["(df-agent-description"]
    if dfad.name is not None:
        parts.append(" :name " + _render_aid(dfad.name))
    if dfad.languages:
        parts.append(" :languages (set " + " ".join(dfad.languages) + ")")
    if dfad.ontologies:
        parts.append(" :ontologies (set " + " ".join(dfad.ontologies) + ")")
    if dfad.protocols:
        parts.append(" :protocols (set " + " ".join(dfad.protocols) + ")")
    if dfad.ownership:
        parts.append(" :ownership (set " + " ".join(dfad.ownership) + ")")
    if dfad.services:
        parts.append(" :services (set")
        for sd in dfad.services:
            parts.append(" " + _render_sd(sd))
        parts.append(")")
    parts.append(")")
    return "".join(parts)


# ------------------------------------------------------------------ #
# Parser string → AST
# ------------------------------------------------------------------ #
def loads(src: str) -> Any:
    toks = list(_tokenize(src))
    expr, pos = _parse_expr(toks, 0)
    if pos != len(toks):
        raise ValueError("Tokens sobrando no fim do SL0.")
    return _build_ast(expr)


# --- tokenizer -------------------------------------------------------------
def _tokenize(s: str) -> Iterator[str]:
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1; continue
        if c in "()":
            yield c; i += 1; continue
        if c == '"':
            i += 1; buf = []
            while i < n:
                c = s[i]
                if c == '\\' and i + 1 < n:
                    buf.append(s[i + 1]); i += 2; continue
                if c == '"':
                    i += 1; break
                buf.append(c); i += 1
            yield '"' + "".join(buf) + '"'
            continue
        j = i
        while j < n and not s[j].isspace() and s[j] not in "()":
            j += 1
        yield s[i:j]; i = j


# --- recursive descent to nested Python lists ------------------------------
def _parse_expr(toks: List[str], pos: int):
    if pos >= len(toks):
        raise ValueError("Fim inesperado.")
    t = toks[pos]
    if t == "(":
        lst: List[Any] = []
        pos += 1
        while pos < len(toks) and toks[pos] != ")":
            sub, pos = _parse_expr(toks, pos)
            lst.append(sub)
        if pos >= len(toks):
            raise ValueError("Parêntese não fechado.")
        pos += 1
        return lst, pos
    if t == ")":
        raise ValueError("')' inesperado.")
    if t.startswith('"') and t.endswith('"') and len(t) >= 2:
        return t[1:-1], pos + 1
    return t, pos + 1


# --- AST builder -----------------------------------------------------------
def _build_ast(e: Any) -> Any:
    if not isinstance(e, list) or not e:
        return e
    head = str(e[0]).lower()

    if head == "action" and len(e) >= 3:
        actor = _build_aid(e[1])
        act = _build_ast(e[2])
        return Action(actor=actor, act=act)

    if head == "register" and len(e) >= 2:
        return Register(_build_dfad(e[1]))

    if head == "deregister" and len(e) >= 2:
        return Deregister(_build_dfad(e[1]))

    if head == "modify" and len(e) >= 2:
        return Modify(_build_dfad(e[1]))

    if head == "search" and len(e) >= 2:
        templ = _build_dfad(e[1])
        maxres = None
        if len(e) >= 3:
            try: maxres = int(e[2])
            except Exception: pass
        return Search(template=templ, max_results=maxres)

    if head == "done" and len(e) >= 2:
        return Done(_build_ast(e[1]))

    if head == "failure" and len(e) >= 2:
        return Failure(_build_ast(e[1]))

    if head == "result" and len(e) >= 3:
        return Result(_build_ast(e[1]), _build_ast(e[2]))

    if head == "df-agent-description":
        return _build_dfad(e)

    if head == "service-description":
        return _build_sd(e)

    if head == "agent-identifier":
        return _build_aid(e)

    # fallback genérico
    return [_build_ast(x) for x in e]


def _build_aid(e: Any) -> AgentIdentifier:
    if not isinstance(e, list):
        return AgentIdentifier(str(e), [])
    name = None; addrs: List[str] = []
    i = 1
    while i < len(e):
        tag = e[i]
        if isinstance(tag, str):
            lt = tag.lower()
            if lt == ":name" and i + 1 < len(e):
                name = str(e[i + 1])
                i += 2; continue
            if lt == ":addresses" and i + 1 < len(e):
                addrs = _extract_sequence(e[i + 1])
                i += 2; continue
        i += 1
    if name is None:
        raise ValueError("agent-identifier sem :name")
    return AgentIdentifier(name, addrs)


def _build_sd(e: Any) -> ServiceDescription:
    sd = ServiceDescription()
    i = 1
    while i < len(e):
        tag = e[i]
        if isinstance(tag, str):
            lt = tag.lower()
            if lt == ":name" and i + 1 < len(e):
                sd.name = str(e[i + 1]); i += 2; continue
            if lt == ":type" and i + 1 < len(e):
                sd.type = str(e[i + 1]); i += 2; continue
            if lt == ":languages" and i + 1 < len(e):
                sd.languages = _extract_set(e[i + 1]); i += 2; continue
            if lt == ":ontologies" and i + 1 < len(e):
                sd.ontologies = _extract_set(e[i + 1]); i += 2; continue
            if lt == ":protocols" and i + 1 < len(e):
                sd.protocols = _extract_set(e[i + 1]); i += 2; continue
            if lt == ":properties" and i + 1 < len(e):
                sd.properties = _extract_properties(e[i + 1]); i += 2; continue
        i += 1
    return sd


def _build_dfad(e: Any) -> DfAgentDescription:
    if not isinstance(e, list):
        raise ValueError("df-agent-description malformado")
    dfad = DfAgentDescription()
    i = 1  # skip head
    while i < len(e):
        tag = e[i]
        if isinstance(tag, str):
            lt = tag.lower()
            if lt == ":name" and i + 1 < len(e):
                dfad.name = _build_aid(e[i + 1]); i += 2; continue
            if lt == ":services" and i + 1 < len(e):
                dfad.services = _extract_services(e[i + 1]); i += 2; continue
            if lt == ":languages" and i + 1 < len(e):
                dfad.languages = _extract_set(e[i + 1]); i += 2; continue
            if lt == ":ontologies" and i + 1 < len(e):
                dfad.ontologies = _extract_set(e[i + 1]); i += 2; continue
            if lt == ":protocols" and i + 1 < len(e):
                dfad.protocols = _extract_set(e[i + 1]); i += 2; continue
            if lt == ":ownership" and i + 1 < len(e):
                dfad.ownership = _extract_set(e[i + 1]); i += 2; continue
        i += 1
    return dfad


# --- extractors ------------------------------------------------------------
def _extract_sequence(e: Any) -> List[str]:
    if isinstance(e, list) and e and isinstance(e[0], str) and e[0].lower() == "sequence":
        return [str(x) for x in e[1:]]
    if isinstance(e, list):
        return [str(x) for x in e]
    return [str(e)]


def _extract_set(e: Any) -> List[str]:
    if isinstance(e, list) and e and isinstance(e[0], str) and e[0].lower() == "set":
        return [str(x) for x in e[1:]]
    if isinstance(e, list):
        return [str(x) for x in e]
    return [str(e)]


def _extract_properties(e: Any) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    items = e[1:] if isinstance(e, list) and e and str(e[0]).lower() == "set" else e
    if not isinstance(items, list):
        items = [items]
    for it in items:
        if isinstance(it, list) and it and str(it[0]).lower() == "property":
            name = value = ""
            j = 1
            while j < len(it):
                tag = it[j]
                if isinstance(tag, str):
                    lt = tag.lower()
                    if lt == ":name" and j + 1 < len(it):
                        name = str(it[j + 1]); j += 2; continue
                    if lt == ":value" and j + 1 < len(it):
                        value = str(it[j + 1]); j += 2; continue
                j += 1
            out.append((name, value))
    return out


def _extract_services(e: Any) -> List[ServiceDescription]:
    items = e[1:] if isinstance(e, list) and e and str(e[0]).lower() == "set" else e
    if not isinstance(items, list):
        items = [items]
    return [_build_sd(x) for x in items]
