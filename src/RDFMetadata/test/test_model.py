# test_model - Test RDF model objects
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import unittest
from xml.dom import minidom

from .. import model

def get_root(xml):
    """Test helper function: parse XML and return an RDFRoot from the
    XML root element.
    """
    doc = minidom.parseString(xml)
    return model.RDFRoot(doc = doc, root_element = doc.documentElement)


class TestEmptyRDF(unittest.TestCase):
    def test_rdf_element(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
</rdf:RDF>
''')
        self.assertTrue(r.root_element_is_rdf)
        self.assertEqual(len(r), 0)

        # The ugly RDF prefix hack
        self.assertEqual(r.rdf_prefix, 'rdf')

    def test_meta_element(self):
        r = get_root('''<?xml version="1.0"?>
<meta>
</meta>
''')
        self.assertFalse(r.root_element_is_rdf)
        self.assertEqual(len(r), 0)

        
class TestTopLevelResource(unittest.TestCase):
    def test_empty_description(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about="http://example.org/test">
  </rdf:Description>
</rdf:RDF>
''')
        self.assertEqual(len(r), 1)

        self.assertTrue("http://example.org/test" in r)
        res = r["http://example.org/test"]
        self.assertEqual(res.uri, "http://example.org/test")
        self.assertEqual(len(res), 0)
        self.assertEqual(len(res.description_nodes), 1)


    def test_literal_values(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <rdf:Description rdf:about="http://example.org/test">
    <dc:title> Test title </dc:title>
    <dc:creator></dc:creator>
  </rdf:Description>
</rdf:RDF>
''')
        res = r["http://example.org/test"]
        self.assertEqual(len(res), 2)

        pred = res[0]
        self.assertEqual(pred.uri, "http://purl.org/dc/elements/1.1/title")

        obj = pred.object
        self.assertIsInstance(obj, model.RDFLiteralNode)
        self.assertEqual(obj.value, ' Test title ')
        self.assertIsNone(obj.type_uri)
        

        pred = res[1]
        self.assertEqual(pred.uri, "http://purl.org/dc/elements/1.1/creator")

        obj = pred.object
        self.assertIsInstance(obj, model.RDFLiteralNode)
        self.assertEqual(obj.value, '')
        self.assertIsNone(obj.type_uri)


    def test_multiple_descriptions(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <rdf:Description rdf:about="http://example.org/test">
    <dc:title> Test title </dc:title>
  </rdf:Description>

  <rdf:Description rdf:about="http://example.org/test">
    <dc:creator></dc:creator>
  </rdf:Description>
</rdf:RDF>
''')
        res = r["http://example.org/test"]
        self.assertEqual(len(res), 2)

        pred = res[0]
        self.assertEqual(pred.uri, "http://purl.org/dc/elements/1.1/title")

        obj = pred.object
        self.assertIsInstance(obj, model.RDFLiteralNode)
        self.assertEqual(obj.value, ' Test title ')
        self.assertIsNone(obj.type_uri)
        

        pred = res[1]
        self.assertEqual(pred.uri, "http://purl.org/dc/elements/1.1/creator")

        obj = pred.object
        self.assertIsInstance(obj, model.RDFLiteralNode)
        self.assertEqual(obj.value, '')
        self.assertIsNone(obj.type_uri)


    def test_typed_values(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <rdf:Description rdf:about="http://example.org/test">
    <dc:date rdf:datatype="http://www.w3.org/2001/XMLSchema#date">2013-08-13</dc:date>
  </rdf:Description>
</rdf:RDF>
''')
        res = r["http://example.org/test"]
        self.assertEqual(len(res), 1)

        pred = res[0]
        self.assertEqual(pred.uri, "http://purl.org/dc/elements/1.1/date")

        obj = pred.object
        self.assertIsInstance(obj, model.RDFLiteralNode)
        self.assertEqual(obj.value, '2013-08-13')
        self.assertEqual(obj.type_uri, "http://www.w3.org/2001/XMLSchema#date")
        
