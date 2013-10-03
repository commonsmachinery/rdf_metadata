# parser - parse RDF/XML into model objects
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.


import unittest
from xml.dom import minidom

# https://pypi.python.org/pypi/py-dom-xpath
import xpath

from .. import parser, model, domrepr
from .. import observer


def get_root(xml):
    """Test helper function: parse XML and return a model.Root from the
    XML root element.
    """
    doc = minidom.parseString(xml)
    return parser.parse_RDFXML(doc = doc, root_element = doc.documentElement)


class CommonTest(unittest.TestCase):
    def assertPredicate(self, pred, uri, object_class, repr_class):
        self.assertIsInstance(pred, model.Predicate)
        self.assertEqual(pred.uri, uri)
        self.assertIsInstance(pred.object, object_class)
        self.assertRepr(pred, repr_class)

    def assertRepr(self, obj, repr_class):
        self.assertIsInstance(obj.repr.repr, repr_class)


class XPathAsserts(object):
    def __init__(self, test, node):
        self.test = test
        self.node = node
        self.ctx = xpath.XPathContext(node)

    def assertNodeCount(self, count, path, node = None):
        if node is None:
            node = self.node

        r = self.ctx.find(path, node)
        self.test.assertIsInstance(r, list, "path didn't return list of nodes")
        self.test.assertEqual(len(r), count)


    def assertValue(self, expected, path, node = None):
        if node is None:
            node = self.node

        r = self.ctx.findvalues(path, node)
        self.test.assertIsInstance(r, list)
        self.test.assertEqual(len(r), 1, "path didn't return exactly one value")
        self.test.assertEqual(r[0], expected)



class TestLiteralNode(CommonTest):
    def test_change_value(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <rdf:Description rdf:about="">
    <dc:title>Test title</dc:title>
  </rdf:Description>
</rdf:RDF>
''')
        
        xp = XPathAsserts(self, r.repr.element)

        pred = r[''][0]
        self.assertPredicate(pred, "http://purl.org/dc/elements/1.1/title",
                             model.LiteralNode, domrepr.LiteralProperty)
        obj = pred.object
        
        self.assertEqual(obj.value, 'Test title')
        self.assertIsNone(obj.type_uri)

        #
        # Change value
        #

        # Two events, unfortunately, since the content is first dropped,
        # then a new text node is set.
        with observer.AssertEvent(self, r,
                                  model.PredicateObjectChanged,
                                  model.PredicateObjectChanged):
            obj.set_value('new value')
        self.assertIsNone(obj.type_uri)

        # Same repr, new value
        self.assertRepr(obj, domrepr.LiteralProperty)
        xp.assertNodeCount(1, "/rdf:RDF/rdf:Description/dc:title")
        xp.assertValue("new value", "/rdf:RDF/rdf:Description/dc:title")
        xp.assertNodeCount(0, "/rdf:RDF/rdf:Description/dc:title/@rdf:datatype")

        #
        # Set type_uri
        #

        with observer.AssertEvent(self, r, model.PredicateObjectChanged):
            obj.set_type_uri('test:type')
        self.assertEqual(obj.type_uri, 'test:type')

        # Same repr, added attribute
        self.assertRepr(obj, domrepr.LiteralProperty)
        xp.assertValue("test:type", "/rdf:RDF/rdf:Description/dc:title/@rdf:datatype")

        #
        # Drop value
        #

        with observer.AssertEvent(self, r, model.PredicateObjectChanged):
            obj.set_value('')
        self.assertEqual(obj.type_uri, 'test:type')

        # New repr, no value
        self.assertRepr(obj, domrepr.EmptyPropertyLiteral)
        xp.assertValue("", "/rdf:RDF/rdf:Description/dc:title")
        xp.assertValue("test:type", "/rdf:RDF/rdf:Description/dc:title/@rdf:datatype")

        #
        # Set value again
        #

        with observer.AssertEvent(self, r, model.PredicateObjectChanged):
            obj.set_value('set again')
        self.assertEqual(obj.type_uri, 'test:type')

        # New repr, new value
        self.assertRepr(obj, domrepr.LiteralProperty)
        xp.assertValue("set again", "/rdf:RDF/rdf:Description/dc:title")
        xp.assertValue("test:type", "/rdf:RDF/rdf:Description/dc:title/@rdf:datatype")

        #
        # Drop type
        #

        with observer.AssertEvent(self, r, model.PredicateObjectChanged):
            obj.set_type_uri(None)
        self.assertIsNone(obj.type_uri)

        # Same repr, no attr
        self.assertRepr(obj, domrepr.LiteralProperty)
        xp.assertValue("set again", "/rdf:RDF/rdf:Description/dc:title")
        xp.assertNodeCount(0, "/rdf:RDF/rdf:Description/dc:title/@rdf:datatype")
        

class TestElementNode(CommonTest):
    def test_add_empty_literal_node(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <rdf:Description rdf:about="">
  </rdf:Description>
</rdf:RDF>
''')
        
        xp = XPathAsserts(self, r.repr.element)

        res = r['']
        self.assertEqual(len(res), 0)

        with observer.AssertEvent(self, r, model.PredicateAdded):
            res.add_literal_node(
                model.QName("http://purl.org/dc/elements/1.1/", "dc", "title"))

        # Check that model updated
        self.assertEqual(len(res), 1)
        pred = res[0]
        self.assertPredicate(pred, "http://purl.org/dc/elements/1.1/title",
                             model.LiteralNode, domrepr.EmptyPropertyLiteral)
        obj = pred.object
        
        self.assertEqual(obj.value, '')
        self.assertIsNone(obj.type_uri)

        # Check that XML updated
        xp.assertNodeCount(1, "/rdf:RDF/rdf:Description/dc:title")
        xp.assertValue('', "/rdf:RDF/rdf:Description/dc:title")
        xp.assertNodeCount(0, "/rdf:RDF/rdf:Description/dc:title/@rdf:datatype")
        

    def test_add_non_empty_literal_node(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <rdf:Description rdf:about="">
  </rdf:Description>
</rdf:RDF>
''')
        
        res = r['']
        self.assertEqual(len(res), 0)

        with observer.AssertEvent(self, r, model.PredicateAdded):
            res.add_literal_node(
                model.QName("http://purl.org/dc/elements/1.1/", "dc", "title"),
                "value", "test:type")

        # Check that model updated
        self.assertEqual(len(res), 1)
        pred = res[0]
        self.assertPredicate(pred, "http://purl.org/dc/elements/1.1/title",
                             model.LiteralNode, domrepr.LiteralProperty)
        obj = pred.object
        
        self.assertEqual(obj.value, 'value')
        self.assertEqual(obj.type_uri, 'test:type')

        # Check that XML updated
        xp = XPathAsserts(self, r.repr.element)
        xp.assertNodeCount(1, "/rdf:RDF/rdf:Description/dc:title")
        xp.assertValue('value', "/rdf:RDF/rdf:Description/dc:title")
        xp.assertNodeCount(1, "/rdf:RDF/rdf:Description/dc:title/@rdf:datatype")
        xp.assertValue('test:type', "/rdf:RDF/rdf:Description/dc:title/@rdf:datatype")
        
        
    # @observer.log_function_events
    def test_remove_literal_property(self):
        r = get_root('''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <rdf:Description rdf:about="">
    <dc:title>Test</dc:title>
  </rdf:Description>
</rdf:RDF>
''')
        
        xp = XPathAsserts(self, r.repr.element)

        res = r['']
        self.assertEqual(len(res), 1)
        p = res[0]
        
        with observer.AssertEvent(self, r, model.PredicateRemoved):
            p.remove()
            
        # Check that model updated
        self.assertEqual(len(res), 0)

        # Check that XML updated
        xp.assertNodeCount(0, "/rdf:RDF/rdf:Description/dc:title")

