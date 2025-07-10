# src/peak_acl/message/envelope.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from .aid import AgentIdentifier


RFC_FMT = "%Y%m%dZ%H%M%S%f"  # JADE usa milisegundos + 'Z'


@dataclass
class Envelope:
    to_: AgentIdentifier
    from_: AgentIdentifier
    date: datetime
    payload_length: int
    acl_rep: str = "fipa.acl.rep.string.std"

    def to_xml(self) -> str:
        env = ET.Element("envelope")
        params = ET.SubElement(env, "params", index="1")

        params.append(self.to_.to_xml_elem("to"))
        params.append(self.from_.to_xml_elem("from"))

        ET.SubElement(params, "acl-representation").text = self.acl_rep
        ET.SubElement(params, "payload-length").text = str(self.payload_length)
        ET.SubElement(params, "date").text = self.date.astimezone(timezone.utc).strftime(RFC_FMT)[:-3]  # trim µs→ms

        # intended-receiver == to
        params.append(self.to_.to_xml_elem("intended-receiver"))

        return ET.tostring(env, encoding="utf-8", xml_declaration=True).decode()

    @classmethod
    def from_xml(cls, xml: str) -> "Envelope":
        root = ET.fromstring(xml)
        params = root.find("./params")
        to_id = AgentIdentifier.from_elem(params.find("to"))
        from_id = AgentIdentifier.from_elem(params.find("from"))
        acl_rep = params.findtext("acl-representation", "")
        payload_length = int(params.findtext("payload-length", "0"))
        date_txt = params.findtext("date", "")
        date = datetime.strptime(date_txt, RFC_FMT).replace(tzinfo=timezone.utc)
        return cls(to_id, from_id, date, payload_length, acl_rep)
