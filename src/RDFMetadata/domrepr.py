# domrepr - Link from RDF model objects to underlying DOM representation
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import sys
import xml.dom

from . import model, namespaces


RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class UnsupportedFunctionError(Exception):
    def __init__(self, func, obj):
        super(Exception, self).__init__('{0} unsupported on {1}'.format(func, obj))

        
class Root(object):
    """Representation for the root RDF element.
    """

    def __init__(self, doc, element, namespaces, root_element_is_rdf):
        super(Root, self).__init__()
        
        self.doc = doc
        self.element = element
        self.namespaces = namespaces

        # Necessary to know when adding top-level resources
        self.root_element_is_rdf = root_element_is_rdf

    def get_ns_prefix(self, uri, preferred_prefix):
        return self.repr.namespaces.get_prefix(uri, preferred_prefix)

    def dump(self):
        self.element.writexml(sys.stderr)


class Repr(object):
    """Intermediate object for the representation of a node.

    This is needed since operations that change data may also change
    the type of the representation.
    """

    def __init__(self, repr):
        super(Repr, self).__init__()
        self.repr = repr

    def get_ns_prefix(self, uri, preferred_prefix):
        return self.repr.get_ns_prefix(uri, preferred_prefix)

    def get_rdf_ns_prefix(self):
        return self.repr.get_rdf_ns_prefix()

    def set_literal_value(self, text):
        self.repr = self.repr.set_literal_value(text)

    def set_datatype(self, type_uri):
        self.repr = self.repr.set_datatype(type_uri)

    def add_literal_node(self, node, qname, value, type_uri):
        self.repr = self.repr.add_literal_node(node, qname, value, type_uri)

    def dump(self):
        self.repr.element.writexml(sys.stderr)


class TypedRepr(object):
    def __init__(self, doc, element, namespaces):
        super(TypedRepr, self).__init__()
        
        self.doc = doc
        self.element = element
        self.namespaces = namespaces

    def to(self, cls):
        return cls(self.doc, self.element, self.namespaces)

    def set_literal_value(self, text):
        raise UnsupportedFunctionError('set_literal_value', self)

    def set_datatype(self, type_uri):
        raise UnsupportedFunctionError('set_datatype', self)

    def add_literal_node(self, node, qname, value, type_uri):
        raise UnsupportedFunctionError('add_literal_node', self)

    def get_rdf_ns_prefix(self):
        return self.namespaces.get_prefix(RDF_NS, 'rdf')

    def add_namespace(self, qname):
        prefix = self.namespaces.get_prefix(qname.ns_uri, qname.ns_prefix)
        if prefix == qname.ns_prefix:
            return qname
        else:
            return model.QName(qname.ns_uri, prefix, qname.local_name)


class ElementNode(TypedRepr):
    """http://www.w3.org/TR/rdf-syntax-grammar/#nodeElement

    Not instantiated directly.
    """
    
    def add_literal_node(self, node, qname, value, type_uri):
        assert isinstance(node, model.SubjectNode)
        
        # Build XML:
        # <ns:name rdf:datatype="type_uri">value</ns:name>

        qname = self.add_namespace(qname)
        element = self.doc.createElementNS(qname.ns_uri, qname.tag_name)

        if type_uri:
            element.setAttributeNS(
                RDF_NS, self.get_rdf_ns_prefix() + ':datatype',
                type_uri)

        if value:
            element.appendChild(self.doc.createTextNode(value))
            repr_cls = LiteralProperty
        else:
            repr_cls = EmptyProperty

        self.element.appendChild(element)

        repr = Repr(repr_cls(self.doc, element,
                             namespaces.Namespaces(self.namespaces, element)))

        # Create predicate and add to node
        lit_node = model.LiteralNode(node.root, repr, value, type_uri)
        pred = model.PredicateLiteral(node.root, repr, qname, lit_node)
        node.add_predicate(pred)

        return self


class DescriptionNode(ElementNode):
    """http://www.w3.org/TR/rdf-syntax-grammar/#nodeElement
    (when the name is rdf:Description)

    Represents:

      - ResourceNode (without rdf:nodeID)
      - BlankNode (with rdf:nodeID)
    """
    pass


class TypedNode(ElementNode):
    """http://www.w3.org/TR/rdf-syntax-grammar/#nodeElement
    (when the name is NOT rdf:Description)

    Represents:

      - ResourceNode (without rdf:nodeID)
      - BlankNode (with rdf:nodeID)
      - Predicate (for the generated rdf:type predicate)
      - ResourceNode (for the generated rdf:type object)
    """
    pass


class ResourceProperty(TypedRepr):
    """http://www.w3.org/TR/rdf-syntax-grammar/#resourcePropertyElt

    Represents:

      - Predicate
    """
    pass


class LiteralProperty(TypedRepr):
    """http://www.w3.org/TR/rdf-syntax-grammar/#literalPropertyElt

    Represents:

      - Predicate (always)
      - LiteralNode (always)
    """

    def set_datatype(self, type_uri):
        # Remove old first, then add new if still set
        try:
            self.element.removeAttributeNS(RDF_NS, 'datatype')
        except xml.dom.NotFoundErr:
            pass

        if type_uri:
            self.element.setAttributeNS(
                RDF_NS, self.get_rdf_ns_prefix() + ':datatype',
                type_uri)

        return self


    def set_literal_value(self, text):
        # Drop old content first
        while True:
            n = self.element.firstChild
            if n is None:
                break
            self.element.removeChild(n)

        if text:
            # Set new
            self.element.appendChild(self.doc.createTextNode(text))
            return self
        else:
            # No more content
            return self.to(EmptyProperty)


class EmptyProperty(TypedRepr):
    """http://www.w3.org/TR/rdf-syntax-grammar/#emptyPropertyElt

    Represents:

      - Predicate (always)
      - ResourceNode (with rdf:resource)
      - BlankNode (with rdf:nodeID)
      - LiteralNode (without either)
    """
    def set_literal_value(self, text):
        if text:
            # Since it will no longer be empty, change to a LiteralProperty instead

            # TODO: check that that is possible

            new = self.to(LiteralProperty)
            new.set_literal_value(text)
            return new
        else:
            return self

    def set_datatype(self, type_uri):
        if type_uri:
            # TODO: check that this is allowed
            pass
        
        # Remove old first, then add new if still set
        try:
            self.element.removeAttributeNS(RDF_NS, 'datatype')
        except xml.dom.NotFoundErr:
            pass

        if type_uri:
            self.element.setAttributeNS(
                RDF_NS, self.get_rdf_ns_prefix() + ':datatype',
                type_uri)

        return self
