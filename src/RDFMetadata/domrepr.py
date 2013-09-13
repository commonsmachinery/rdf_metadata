# domrepr - Link from RDF model objects to underlying DOM representation
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import sys
import xml.dom

from . import model, namespaces, observer
from . import domwrapper

RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class UnsupportedFunctionError(Exception):
    def __init__(self, func, obj):
        super(Exception, self).__init__('{0} unsupported on {1}'.format(func, obj))

        
class Root(observer.Subject, object):
    """Representation for the root RDF element.
    """

    def __init__(self, doc, element):
        super(Root, self).__init__()
        
        self.doc = doc
        self.element = domwrapper.Element(element)
        self.namespaces = namespaces.Namespaces(None, element)

        self.element.register_observer(self._on_dom_update)

        # Necessary to know when adding top-level resources
        self.root_element_is_rdf = is_rdf_element(element, 'RDF')

        # Some circular dependencies between models.  Might resolve
        # that later, but I'm wary about adding too much stuff into
        # these classes and this module
        from . import parser
        self.parser = parser.RDFXMLParser(self)

    def parse_into_model(self, strict = True):
        """Return a new model.Root object that contains all
        nodes and predicates under this DOM root node.
        """

        # Create the model, which will add an observer that reacts
        # to parse events 
        model_root = model.Root(self)

        # Only do strict parsing on original document, and be forgiving
        # on later DOM updates
        self.parser.strict = strict
        self.parser.parse_node_element_list(self, self.element, True)
        self.parser.strict = False

        return model_root

    def get_child_ns(self, element):
        return namespaces.Namespaces(self.namespaces, element)

    def get_ns_prefix(self, uri, preferred_prefix):
        return self.repr.namespaces.get_prefix(uri, preferred_prefix)

    def dump(self):
        self.element.writexml(sys.stderr)

    def is_event_source(self, event):
        return event.repr is self

    def _on_dom_update(self, event):
        pass


class Repr(observer.Subject, object):
    """Intermediate object for the representation of a node.

    This is needed since operations that change data may also change
    the type of the representation.
    """

    def __init__(self, repr):
        super(Repr, self).__init__()
        self.repr = None
        self._set_repr(repr)

        # It helps having the root here too, and that one won't change
        self.root = repr.root

    def get_child_ns(self, element):
        return self.repr.get_child_ns(element)

    def get_ns_prefix(self, uri, preferred_prefix):
        return self.repr.get_ns_prefix(uri, preferred_prefix)

    def get_rdf_ns_prefix(self):
        return self.repr.get_rdf_ns_prefix()

    def is_event_source(self, event):
        return event.repr is self.repr

    def set_literal_value(self, text):
        self._set_repr(self.repr.set_literal_value(text))

    def set_datatype(self, type_uri):
        self._set_repr(self.repr.set_datatype(type_uri))

    def add_literal_node(self, node, qname, value, type_uri):
        self._set_repr(self.repr.add_literal_node(node, qname, value, type_uri))

    def dump(self):
        self.repr.element.writexml(sys.stderr)

    def _set_repr(self, repr):
        if repr is self.repr:
            return

        if self.repr:
            self.repr.unregister_observer(self._on_repr_update)

        self.repr = repr

        if self.repr:
            self.repr.register_observer(self._on_repr_update)

    def _on_repr_update(self, event):
        # Just pass on the event
        self.notify_observers(event)
        
            

class TypedRepr(observer.Subject, object):
    def __init__(self, root, element, namespaces):
        super(TypedRepr, self).__init__()
        
        self.root = root
        self.element = domwrapper.Element(element)
        self.namespaces = namespaces

        self.element.register_observer(self._on_dom_update)

    def to(self, cls):
        return cls(self.root, self.element, self.namespaces)

    def set_literal_value(self, text):
        raise UnsupportedFunctionError('set_literal_value', self)

    def set_datatype(self, type_uri):
        raise UnsupportedFunctionError('set_datatype', self)

    def add_literal_node(self, node, qname, value, type_uri):
        raise UnsupportedFunctionError('add_literal_node', self)

    def get_rdf_ns_prefix(self):
        return self.namespaces.get_prefix(RDF_NS, 'rdf')

    def get_child_ns(self, element):
        return namespaces.Namespaces(self.namespaces, element)

    def add_namespace(self, qname):
        prefix = self.namespaces.get_prefix(qname.ns_uri, qname.ns_prefix)
        if prefix == qname.ns_prefix:
            return qname
        else:
            return model.QName(qname.ns_uri, prefix, qname.local_name)

    def _on_dom_update(self, event):
        pass


class ElementNode(TypedRepr):
    """http://www.w3.org/TR/rdf-syntax-grammar/#nodeElement

    Not instantiated directly.
    """
    
    def add_literal_node(self, node, qname, value, type_uri):
        assert isinstance(node, model.SubjectNode)
        
        # Build XML:
        # <ns:name rdf:datatype="type_uri">value</ns:name>

        qname = self.add_namespace(qname)
        element = self.root.doc.createElementNS(qname.ns_uri, qname.tag_name)

        if type_uri:
            element.setAttributeNS(
                RDF_NS, self.get_rdf_ns_prefix() + ':datatype',
                type_uri)

        if value:
            element.appendChild(self.root.doc.createTextNode(value))
            repr_cls = LiteralProperty
        else:
            repr_cls = EmptyPropertyLiteral

        # Add the child, trigger a ChildAdded event
        self.element.appendChild(element)


    def _on_dom_update(self, event):
        if isinstance(event, domwrapper.ChildAdded):
            assert event.parent is self.element
            if event.child.nodeType == event.child.ELEMENT_NODE:
                self._parse_new_element(event.child)


    def _parse_new_element(self, element):
        self.root.parser.parse_property_element(self, element)



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
    """
    pass


class ImpliedTypeProperty(TypedRepr):
    """http://www.w3.org/TR/rdf-syntax-grammar/#nodeElement
    (when the name is NOT rdf:Description)

    Represents:

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
            self.element.appendChild(self.root.doc.createTextNode(text))
            return self
        else:
            # No more content
            return self.to(EmptyPropertyLiteral)


    def _on_dom_update(self, event):
        if isinstance(event, domwrapper.ChildRemoved):
            self._update_text()

        elif isinstance(event, domwrapper.ChildAdded):
            node = event.child
            if node.nodeType == node.TEXT_NODE:
                self._update_text()
            else:
                # This would turn it into a ElementNode!
                assert False, 'not implemented yet'

        elif isinstance(event, domwrapper.AttributeSet):
            if (event.attr.namespaceURI == RDF_NS
                and event.attr._get_localName() == 'datatype'):
                self._update_type(event.attr.value)

        elif isinstance(event, domwrapper.AttributeRemoved):
            if (event.attr.namespaceURI == RDF_NS
                and event.attr._get_localName() == 'datatype'):
                self._update_type(None)


    def _update_text(self):
        self.element.normalize()
        text_nodes = [n for n in self.element.childNodes if n.nodeType == n.TEXT_NODE]
        assert len(text_nodes) <= 1
        
        if text_nodes:
            text = text_nodes[0].data
        else:
            text = ''

        self.notify_observers(
            model.PredicateLiteralReprValueChanged(repr = self, value = text))
        

    def _update_type(self, type_uri):
        self.notify_observers(
            model.PredicateLiteralReprTypeChanged(repr = self, type_uri = type_uri))


class EmptyPropertyLiteral(LiteralProperty):
    """http://www.w3.org/TR/rdf-syntax-grammar/#emptyPropertyElt

    Represents:

      - Predicate (always)
      - LiteralNode (without rdf:resource or rdf:nodeID)
    """
    pass


class EmptyPropertyResource(TypedRepr):
    """http://www.w3.org/TR/rdf-syntax-grammar/#emptyPropertyElt

    Represents:

      - Predicate (always)
      - ResourceNode (with rdf:resource)
    """
    pass


class EmptyPropertyBlankNode(TypedRepr):
    """http://www.w3.org/TR/rdf-syntax-grammar/#emptyPropertyElt

    Represents:

      - Predicate (always)
      - BlankNode (with rdf:nodeID)
    """
    pass


def is_rdf_element(element, name):
    """Return TRUE if this is an RDF element with the local NAME."""
    return (element.namespaceURI == RDF_NS
            and element.localName == name)
        
    
