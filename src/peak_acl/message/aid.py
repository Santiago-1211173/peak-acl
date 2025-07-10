# src/peak_acl/message/aid.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import xml.etree.ElementTree as ET


@dataclass
class AgentIdentifier:
    name: str
    addresses: List[str] = field(default_factory=list)

    def to_xml_elem(self, tag: str) -> ET.Element:
        root = ET.Element(tag)
        ai = ET.SubElement(root, "agent-identifier")
        ET.SubElement(ai, "name").text = self.name
        addrs = ET.SubElement(ai, "addresses")
        for url in self.addresses:
            ET.SubElement(addrs, "url").text = url
        return root

    @classmethod
    def from_elem(cls, elem: ET.Element) -> "AgentIdentifier":
        name = elem.findtext("./agent-identifier/name", "")
        urls = [u.text for u in elem.findall(".//url")]
        return cls(name, urls)
