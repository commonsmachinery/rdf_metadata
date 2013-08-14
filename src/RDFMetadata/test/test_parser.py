# test_parser - Test parsing RDF/XML into model objects
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import unittest
from xml.dom import minidom

from .. import model, domrepr

def get_root(xml):
    """Test helper function: parse XML and return an RDFRoot from the
    XML root element.
    """
    doc = minidom.parseString(xml)
    return model.Root(doc = doc, root_element = doc.documentElement)


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
        self.assertEqual(len(res.reprs), 1)
        self.assertIsInstance(res.reprs[0].repr, domrepr.DescriptionNode)


    def test_multiple_empty_descriptions(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about="http://example.org/test">
  </rdf:Description>

  <rdf:Description rdf:about="http://example.org/test">
  </rdf:Description>
</rdf:RDF>
''')
        # They will get merged into one resource
        self.assertEqual(len(r), 1)

        self.assertTrue("http://example.org/test" in r)
        res = r["http://example.org/test"]
        self.assertEqual(res.uri, "http://example.org/test")
        self.assertEqual(len(res), 0)
        self.assertEqual(len(res.reprs), 2)
        self.assertIsInstance(res.reprs[0].repr, domrepr.DescriptionNode)
        self.assertIsInstance(res.reprs[1].repr, domrepr.DescriptionNode)


    def test_multiple_subjects(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about="">
  </rdf:Description>

  <rdf:Description rdf:about="http://example.org/test">
  </rdf:Description>
</rdf:RDF>
''')
        self.assertEqual(len(r), 2)

        self.assertTrue("" in r)
        res = r[""]
        self.assertEqual(res.uri, "")
        self.assertEqual(len(res), 0)
        self.assertEqual(len(res.reprs), 1)

        self.assertTrue("http://example.org/test" in r)
        res = r["http://example.org/test"]
        self.assertEqual(res.uri, "http://example.org/test")
        self.assertEqual(len(res), 0)
        self.assertEqual(len(res.reprs), 1)


class TestLiteralNodes(unittest.TestCase):
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
        self.assertIsInstance(pred.repr.repr, domrepr.LiteralProperty)

        obj = pred.object
        self.assertIsInstance(obj, model.LiteralNode)
        self.assertEqual(obj.value, ' Test title ')
        self.assertIsNone(obj.type_uri)
        self.assertIs(pred.repr, obj.repr)

        pred = res[1]
        self.assertEqual(pred.uri, "http://purl.org/dc/elements/1.1/creator")
        self.assertIsInstance(pred.repr.repr, domrepr.EmptyProperty)

        obj = pred.object
        self.assertIsInstance(obj, model.LiteralNode)
        self.assertEqual(obj.value, '')
        self.assertIsNone(obj.type_uri)
        self.assertIs(pred.repr, obj.repr)


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
        self.assertIsInstance(obj, model.LiteralNode)
        self.assertEqual(obj.value, ' Test title ')
        self.assertIsNone(obj.type_uri)
        

        pred = res[1]
        self.assertEqual(pred.uri, "http://purl.org/dc/elements/1.1/creator")

        obj = pred.object
        self.assertIsInstance(obj, model.LiteralNode)
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
        self.assertIsInstance(obj, model.LiteralNode)
        self.assertEqual(obj.value, '2013-08-13')
        self.assertEqual(obj.type_uri, "http://www.w3.org/2001/XMLSchema#date")
        

class TestResourceNodes(unittest.TestCase):
    def test_empty_description(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <rdf:Description rdf:about="">
    <dc:creator>
      <rdf:Description rdf:about="http://example.org/test">
      </rdf:Description>
    </dc:creator>
  </rdf:Description>
</rdf:RDF>
''')

        # This is the non-abbreviated way have a triplet where the
        # object is another resource. It is usually handled with an
        # rdf:resource attribute instead.

        self.assertEqual(len(r), 2)

        # The main resource

        res = r[""]
        pred = res[0]
        self.assertEqual(pred.uri, "http://purl.org/dc/elements/1.1/creator")
        self.assertIsInstance(pred.repr.repr, domrepr.ResourceProperty)

        obj = pred.object
        self.assertIsInstance(obj, model.ResourceNode)

        # The linked resource should be the same as the one in root
        
        self.assertTrue("http://example.org/test" in r)
        res2 = r["http://example.org/test"]
        self.assertIs(obj, res2)

        self.assertEqual(res2.uri, "http://example.org/test")
        self.assertEqual(len(res2), 0)
        self.assertEqual(len(res2.reprs), 1)
        self.assertIsInstance(res2.reprs[0].repr, domrepr.DescriptionNode)



    def test_description_with_property(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <rdf:Description rdf:about="">
    <dc:creator>
      <rdf:Description rdf:about="http://example.org/test">
        <dc:title>Test</dc:title>
      </rdf:Description>
    </dc:creator>
  </rdf:Description>
</rdf:RDF>
''')

        # The non-abbreviated way allow us to describe properties
        # directly instead of a separate block

        self.assertEqual(len(r), 2)

        # The main resource

        res = r[""]
        pred = res[0]
        self.assertEqual(pred.uri, "http://purl.org/dc/elements/1.1/creator")
        obj = pred.object
        self.assertIsInstance(obj, model.ResourceNode)

        # The linked resource
        
        res2 = r["http://example.org/test"]
        self.assertEqual(len(res2), 1)
        self.assertEqual(len(res2.reprs), 1)

        # The creator should be the resource object
        self.assertIs(obj, res2)

        # And that should have a title predicate
        pred = res2[0]
        self.assertEqual(pred.uri, "http://purl.org/dc/elements/1.1/title")

        obj = pred.object
        self.assertIsInstance(obj, model.LiteralNode)
        self.assertEqual(obj.value, 'Test')
        self.assertIsNone(obj.type_uri)


    def test_resource_attr(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <rdf:Description rdf:about="">
    <dc:creator rdf:resource="http://example.org/test" />
  </rdf:Description>
</rdf:RDF>
''')

        # This is the more common, abbreviated way to link to a
        # resource

        self.assertEqual(len(r), 2)

        # The main resource

        res = r[""]
        pred = res[0]
        self.assertEqual(pred.uri, "http://purl.org/dc/elements/1.1/creator")
        self.assertIsInstance(pred.repr.repr, domrepr.EmptyProperty)

        obj = pred.object
        self.assertIsInstance(obj, model.ResourceNode)

        # The linked resource should be the same as the one in root
        
        self.assertTrue("http://example.org/test" in r)
        res2 = r["http://example.org/test"]
        self.assertIs(obj, res2)

        self.assertEqual(res2.uri, "http://example.org/test")
        self.assertEqual(len(res2), 0)
        self.assertEqual(len(res2.reprs), 1)
        self.assertIsInstance(res2.reprs[0].repr, domrepr.EmptyProperty)


    def test_linked_resource(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <rdf:Description rdf:about="http://example.org/test">
    <dc:title>Test</dc:title>
  </rdf:Description>

  <rdf:Description rdf:about="">
    <dc:creator rdf:resource="http://example.org/test" />
  </rdf:Description>
</rdf:RDF>
''')

        # Link to a resource that is described further previously
        
        self.assertEqual(len(r), 2)

        # The main resource

        res = r[""]
        pred = res[0]
        obj = pred.object
        self.assertIsInstance(obj, model.ResourceNode)

        # The linked resource should be the same as the one in root
        
        self.assertTrue("http://example.org/test" in r)
        res2 = r["http://example.org/test"]
        self.assertIs(obj, res2)

        self.assertEqual(res2.uri, "http://example.org/test")
        self.assertEqual(len(res2), 1)
        self.assertEqual(len(res2.reprs), 2)
        self.assertIsInstance(res2.reprs[0].repr, domrepr.DescriptionNode)
        self.assertIsInstance(res2.reprs[1].repr, domrepr.EmptyProperty)

        
