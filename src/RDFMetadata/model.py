# model - RDF model objects
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

"""Model RDF graphs in a way suitable for inline editing of the
underlying RDF/XML.

The naming convention is that XML objects ("nodes") are called
elements, while the subjects or objects of RDF triples are called
nodes.
"""

import collections
import xml.dom

RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

class RDFRoot(collections.Mapping):
    def __init__(self, doc, root_element):
        super(RDFRoot, self).__init__()
        
        self.doc = doc
        self.root_element = root_element
        
        self.resource_nodes = {}

        # Determine if we're starting with is rdf:RDF or some other element
        self.root_element_is_rdf = is_rdf_element(root_element, 'RDF')

        # This is ugly: I can't find a way to ask the DOM tree for the
        # prefix associated with a namespace, so just grab it when we
        # see it in an RDF element...
        self.rdf_prefix = None
        if root_element.namespaceURI == RDF_NS:
            self.rdf_prefix = root_element.prefix
        
        self._parse()

    #
    # Support read-only Mapping interface to access the top subjects
    #
        
    def __getitem__(self, key):
        return self.resource_nodes[key]

    def __iter__(self):
        return iter(self.resource_nodes)

    def __len__(self):
        return len(self.resource_nodes)
    

    #
    # Internal methods
    #
    
    def _parse(self):
        """Parse the provided root element to extract all information in it."""

        # Look for rdf:Descriptions
        # TODO: also look for types nodes in rdf:RDF

        for el in iter_subelements(self.root_element):
            if is_rdf_element(el, 'Description'):

                # Ugly hack as above: grab prefix if possible
                if self.rdf_prefix is None:
                    self.rdf_prefix = el.prefix

                self._parse_resource(el)


    def _parse_resource(self, el):
        # Missing about attribute is equal to empty string
        about = el.getAttributeNS(RDF_NS, 'about')

        try:
            res = self.resource_nodes[about]
        except KeyError:
            res = RDFResourceNode(self, about)
            self.resource_nodes[about] = res

        res._parse_element(el)
            
                


class RDFNode(object):
    def __init__(self, root):
        self.root = root


class RDFSubjectNode(RDFNode, collections.Sequence):

    def __init__(self, root):
        super(RDFSubjectNode, self).__init__(root)

        self.description_nodes = []
        self.predicates = []

    def set_type(self, type_uri):
        pass

    #
    # Support read-only sequence interface to access the predicates
    #
        
    def __getitem__(self, item):
        return self.predicates[item]

    def __iter__(self):
        return iter(self.predicates)

    def __len__(self):
        return len(self.predicates)


    def _parse_element(self, el):
        self.description_nodes.append(el)

        for subel in iter_subelements(el):
            # TODO: filter out all rdf: elements?

            uri = subel.namespaceURI + subel.localName
            pred = RDFPredicate(self.root, uri)
            pred._parse_element(subel)
            self.predicates.append(pred)
            

class RDFResourceNode(RDFSubjectNode):
    def __init__(self, root, uri):
        super(RDFResourceNode, self).__init__(root)

        self.uri = uri
        
    def set_uri(self, uri):
        # TODO
        pass
    

class RDFBlankNode(RDFSubjectNode):
    def __init__(self, root):
        super(RDFBlankNode, self).__init__(root)

        self.node_id = None


class RDFLiteralNode(RDFNode):
    def __init__(self, root, predicate, value, type_uri = None):
        super(RDFLiteralNode, self).__init__(root)
        self.predicate = predicate

        self.value = value
        self.type_uri = type_uri

    def set_value(self, value):
        self.value = value

        # Update XML. Drop old value first, then add new if still set
        while True:
            n = self.predicate.element.firstChild
            if n is None:
                break
            self.predicate.element.removeChild(n)

        if self.value:
            self.predicate.element.appendChild(self.root.doc.createTextNode(value))


    def set_type(self, type_uri):
        self.type_uri = type_uri

        # Remove old first, then add new if still set
        try:
            self.predicate.element.removeAttributeNS(RDF_NS, 'datatype')
        except xml.dom.NotFoundErr:
            pass

        if type_uri:
            # Ugly DOM - have to build the qname ourselves
            assert self.root.rdf_prefix is not None
            self.predicate.element.setAttributeNS(
                RDF_NS, self.root.rdf_prefix + ':datatype', type_uri)


class RDFPredicate(object):
    def __init__(self, root, uri):
        self.root = root
        self.element = None
        self.uri = uri
        self.object = None
        
    def set_value(self, value):
        if self.object:
            self.object.set_value(value)

    def set_type(self, type_uri):
        if self.object:
            self.object.set_type(type_uri)

    def _parse_element(self, el):
        # TODO: first check for sub-elements or attributes
        self.element = el

        type_uri = el.getAttributeNS(RDF_NS, 'datatype')
        if not type_uri:
            type_uri = None
            
        el.normalize()
        for n in el.childNodes:
            if n.nodeType == n.TEXT_NODE:
                self.object = RDFLiteralNode(self.root, self, n.data, type_uri)
                break
        else:
            self.object = RDFLiteralNode(self.root, self, "", type_uri)
            


def iter_subelements(element):
    """Return an iterator over all child nodes that are elements"""

    for n in element.childNodes:
        if n.nodeType == n.ELEMENT_NODE:
            yield n
        
def is_rdf_element(element, name):
    """Return TRUE if this is an RDF element with the local NAME."""
    return (element.namespaceURI == RDF_NS
            and element.localName == name)
