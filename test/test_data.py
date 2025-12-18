import unittest
from pathlib import Path

from ubercode.utils.data import JsonData
from ubercode.utils.data import XmlData


class TestJsonData(unittest.TestCase):

    # -------- common usages ----------
    def test_JSON(self):
        # calculate the filename for our test.xml file from this file (much like settings does)
        file_path = Path(__file__).resolve().parent / 'test.json'

        json_string = """
{
  "people" : [
    {
       "firstName": "Joe",
       "lastName": "Jackson",
       "gender": "male",
       "age": 28,
       "number": "7349282382",
       "groups": [
            "members",
            "student"
       ]
    },
    {
       "firstName": "James",
       "lastName": "Smith",
       "gender": "male",
       "age": 32,
       "number": "5678568567",
       "groups": [
            "members",
            "professional"
       ]
    },
    {
       "firstName": "Emily",
       "lastName": "Jones",
       "gender": "female",
       "age": 24,
       "number": "456754675"
    }
  ]
}
"""
        # test we can construct from a json string
        json = JsonData(json_string=json_string)
        self.assertEqual(len(json.data['people']), 3)
        # test we can construct by chaining and reading file
        json2 = JsonData().from_json_file(str(file_path))
        self.assertEqual(json.data, json2.data)
        # test encoding
        json_string = """
{
  "people" : [
    {
       "firstName": "Joe & Baker",
       "lastName": "Jackson",
       "gender": "male",
       "age": 28,
       "number": "7349282382",
       "groups": [
            "members",
            "student"
       ]
    },
    {
       "firstName": "James &amp;",
       "lastName": "Smith",
       "gender": "male",
       "age": 32,
       "number": "5678568567",
       "groups": [
            "members",
            "professional"
       ]
    },
    {
       "firstName": "Emily",
       "lastName": "Jones",
       "gender": "female",
       "age": 24,
       "number": "456754675"
    }
  ]
}
"""
        json = JsonData(json_string=json_string, encode_ampersands=True)
        self.assertEqual(len(json.data['people']), 3)
        first_name = json.data['people'][0]['firstName']
        self.assertEqual(first_name, "Joe &amp; Baker")
        #  make sure the second name isn't double encoded
        second_name = json.data['people'][1]['firstName']
        self.assertEqual(second_name, "James &amp;")
        # test the str function
        result = "{'people': [{'firstName': 'Joe &amp; Baker', 'lastName': 'Jackson', 'gender': 'male', 'age': 28, 'number': '7349282382', 'groups': ['members', 'student']}, {'firstName': 'James &amp;', 'lastName': 'Smith', 'gender': 'male', 'age': 32, 'number': '5678568567', 'groups': ['members', 'professional']}, {'firstName': 'Emily', 'lastName': 'Jones', 'gender': 'female', 'age': 24, 'number': '456754675'}]}"
        self.assertEqual(str(json), result)


class TestXmlData(unittest.TestCase):

    # -------- common usages ----------
    def test_XML(self):
        # calculate the filename for our test.xml file from this file (much like settings does)
        file_path = Path(__file__).resolve().parent / 'test.xml'
        xml_string = """
<contacts>
    <contact>
        <name>Steve Stacha</name>
    </contact>
    <contact>
        <name>Buggs Bunny</name>
    </contact>
    <contact>
        <name>Daffy Duck</name>
    </contact>
</contacts>
"""
        # test we can construct from an xml string
        xml = XmlData(xml_string=xml_string)
        # NOTE: because we used a multiline string we need to strip the extra newlines before and after <contacts>
        self.assertEqual(str(xml), xml_string.strip())
        # normal string doesn't need stripping
        xml_compact_string = "<contacts><contact><name>Buggs Bunny</name></contact><contact><name>Daffy Duck</name></contact></contacts>"
        xml2 = XmlData(xml_compact_string)
        self.assertEqual(str(xml2), xml_compact_string)
        # test we can create using the from_xml_string() method chaining
        xml3 = XmlData().from_xml_string(xml_compact_string)
        self.assertEqual(str(xml2), str(xml3))
        # test that method chaining after constructor overrides the value in place
        self.assertNotEqual(str(xml), str(xml2))
        xml.from_xml_string(xml_compact_string)
        self.assertEqual(str(xml), str(xml2))
        # test that we can read from file
        xml.from_xml_file(str(file_path))
        # we should be back to before
        self.assertEqual(str(xml), xml_string.strip())
        # test an attribute
        xml_string = """
<contacts>
    <contact attr="1">
        <name>Steve Stacha</name>
    </contact>
    <contact>
        <name>Buggs & Bunny</name>
    </contact>
    <contact>
        <name>Daffy Duck</name>
    </contact>
</contacts>
"""
        xml = XmlData(xml_string=xml_string, encode_ampersands=True)
        xml_dict = xml.to_dict()
        self.assertEqual(xml_dict['contacts']['contact'][0]['@attr'], '1')


