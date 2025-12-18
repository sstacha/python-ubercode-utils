"""
A collection of basic json/xml conversion helper utilities.
"""
import json
import re
# from typing import Self (Not available until 3.9; omitting for now)
import xml.etree.ElementTree as Etree
# from typing import Self (Not available until 3.9; omitting for now)
from collections import defaultdict


class JsonData:
    """ simple json class to encapsulate basic json operations """
    def __init__(self, json_string: str or None = None, encode_ampersands: bool = False):
        # data is core python objects (list, dict, object, etc) from the core python JSON.loads
        self.data = None
        self.encode_ampersands = encode_ampersands
        self.from_json_string(json_string)

    def from_json_string(self, json_string: str):
        """
        read in from json_string
        :param json_string:
        :return: self
        """
        if json_string:
            if self.encode_ampersands:
                regex = re.compile(r"&(?!amp;|lt;|gt;)")
                json_string = regex.sub("&amp;", json_string)
            self.data = json.loads(json_string)
        return self

    def from_json_file(self, json_file_path: str):
        """
        read in from json_file
        :param json_file_path: string to file
        :return: self
        """
        with open(json_file_path, encoding='utf-8-sig') as json_file:
            json_string = json_file.read()
        if json_string:
            if self.encode_ampersands:
                regex = re.compile(r"&(?!amp;|lt;|gt;)")
                json_string = regex.sub("&amp;", json_string)
            self.data = json.loads(json_string)
        return self

    def __str__(self):
        return str(self.data)


class XmlData:
    """ simple xml class to encapsulate basic xml operations using build in python ETree """
    def __init__(self, xml_string: str or None = None, encode_ampersands: bool = False):
        # data is core python ElementTree object
        self.data = None
        self.encode_ampersands = encode_ampersands
        self.from_xml_string(xml_string)

    def from_xml_string(self, xml_string: str):
        """
        read in from xml_string
        :param xml_string:
        :return: self
        """
        if xml_string:
            if self.encode_ampersands:
                regex = re.compile(r"&(?!amp;|lt;|gt;)")
                xml_string = regex.sub("&amp;", xml_string)
            self.data = Etree.fromstring(xml_string)
        return self

    def from_xml_file(self, xml_file_path: str):
        """
        read in from xml_file
        :param xml_file_path:
        :return: self
        """
        # if we need to encode load the file replace and then load the etree from string
        if self.encode_ampersands:
            # note: encoding was utf-8-sig
            with open(xml_file_path, encoding='utf-8') as xml_file:
                xml_string = xml_file.read()
                regex = re.compile(r"&(?!amp;|lt;|gt;)")
                xml_string = regex.sub("&amp;", xml_string)
                tree = Etree.fromstring(xml_string)
        else:
            tree = Etree.parse(xml_file_path)
            tree = tree.getroot()
        self.data = tree
        return self

    def to_dict(self) -> dict:
        """
        output to dict
        :return: dict
        """
        return XmlData.tree_to_dict(self.data)

    @staticmethod
    def tree_to_dict(t: Etree) -> dict:
        """
        Convert an etree structure to a dictionary of values
        :param t: etree instance
        :return: dictionary of values
        """
        d = {t.tag: {} if t.attrib else None}
        children = list(t)
        if children:
            dd = defaultdict(list)
            for dc in map(XmlData.tree_to_dict, children):
                for k, v in dc.items():
                    dd[k].append(v)
            d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
        if t.attrib:
            d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
        if t.text:
            text = t.text.strip()
            if children or t.attrib:
                if text:
                    d[t.tag]['#text'] = text
            else:
                d[t.tag] = text
        return d

    def __str__(self):
        if self.data:
            return Etree.tostring(self.data, encoding='unicode')
        return ""
