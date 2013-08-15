# parser - parse RDF/XML into model objects
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import xml.dom

from . import model, domrepr

RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

class RDFXMLError(Exception):
    def __init__(self, msg, element = None):
        if element:
            msg += '\nElement: {0}'.format(element)

        self.element = element
        super(RDFXMLError, self).__init__(msg)


def parse_RDFXML(doc, root_element, strict = True):
    p = RDFXMLParser(doc, root_element, strict = strict)
    return p.root



class RDFXMLParser(object):
    """Parse RDFXML into model object directly.  This class is allowed
    to modify the internal member variables of the model objects.
    """

    def __init__(self, doc, root_element, strict = True):
        self.strict = strict

        self.doc = doc
        self.root_element = root_element

        ns_root = Namespaces(None, root_element)
        
        root_repr = domrepr.Root(doc, root_element, ns_root,
                                 is_rdf_element(root_element, 'RDF'))

        self.root = model.Root(root_repr)

        self.parse_node_element_list(ns_root, root_element, top_level = True)
        
    
    def parse_node_element_list(self, ns, element, top_level = False):
        """7.2.10: http://www.w3.org/TR/rdf-syntax-grammar/#nodeElementList

        nodeElementList: ws* (nodeElement ws* )*
        """

        for el in iter_subelements(element):
            if is_rdf_element(el, 'Description'):
                self.parse_node_element(ns, el, top_level)
            else:
                # Only use typed nodes when in rdf:RDF or deeper
                if not top_level or self.root.repr.root_element_is_rdf:
                    self.parse_node_element(ns, el, top_level)


    def parse_node_element(self, ns, element, top_level = False):
        """7.2.11: http://www.w3.org/TR/rdf-syntax-grammar/#nodeElement

        nodeElement:
          start-element(URI == nodeElementURIs
              attributes == set((idAttr | nodeIdAttr | aboutAttr )?, propertyAttr*))
          propertyEltList
          end-element()
        """
        
        ns = Namespaces(ns, element)

        if is_rdf_element(element, 'Description'):
            typed_node = False
            repr = domrepr.Repr(domrepr.DescriptionNode(self.doc, element, ns))
        else:
            typed_node = True
            repr = domrepr.Repr(domrepr.TypedNode(self.doc, element, ns))

        # Check what kind of node this is by presence of rdf:ID,
        # rdf:nodeID or rdf:about

        fragment_id = element.getAttributeNS(RDF_NS, 'ID')
        node_id = element.getAttributeNS(RDF_NS, 'nodeID')
        about = element.getAttributeNS(RDF_NS, 'about')

        if fragment_id:
            # TODO: turn ID into an about
            assert False, 'not implemented yet'

        if node_id:
            if self.strict and about:
                raise RDFXMLError('specifying rdf:nodeID on a non-blank node', element)

            node = self.root.get_blank_node(model.NodeID(node_id))

        elif about:
            node = self.root.get_resource_node(about)

        else:
            if top_level:
                # treat this as an empty rdf:about
                node = self.root.get_resource_node("")
            else:
                # internally generated node ID
                node = self.root.get_blank_node(model.NodeID(None))

        node.reprs.append(repr)

        if typed_node:
            # Generate the equivalent of a <rdf:type rdf:resource="..." /> predicate

            type_resource = self.root.get_resource_node(get_element_uri(element))
            type_resource.reprs.append(repr)
            
            
            predicate = model.PredicateEmpty(
                self.root, repr,
                model.QName(RDF_NS, repr.get_rdf_ns_prefix(), 'type'),
                type_resource)

            node.predicates.append(predicate)
            

        # TODO: parse property attributes
        
        self.parse_property_element_list(ns, node, element)

        return node

        
    def parse_property_element_list(self, ns, node, element):
        """7.2.13: http://www.w3.org/TR/rdf-syntax-grammar/#propertyEltList

        propertyEltList: ws* (propertyElt ws* ) *
        """
        
        for el in iter_subelements(element):
            # TODO: filter out all rdf: elements?

            predicate = self.parse_property_element(ns, el)
            if predicate is not None:
                node.predicates.append(predicate)
            

            
    def parse_property_element(self, ns, element):
        """7.2.14: http://www.w3.org/TR/rdf-syntax-grammar/#propertyElt

        propertyElt:
           resourcePropertyElt |
           literalPropertyElt |
           parseTypeLiteralPropertyElt |
           parseTypeResourcePropertyElt |
           parseTypeCollectionPropertyElt |
           parseTypeOtherPropertyElt |
           emptyPropertyElt

        This code does not handle reification.
        """


        # Figure out what kind of object this predicate point to.
        # Three alternatives, which can be detected in this order:

        # RDFLiteraLXMLNode: value is the entire XML substructure 
        # RDFSubjectNode: value is... many things.
        # RDFLiteralNode: value is the element text contents

        # TODO: Step 1: check parseType

        # Step 2: no parseType, so check what child nodes there are

        element_nodes = [n for n in element.childNodes if n.nodeType == n.ELEMENT_NODE]
        
        if element_nodes:
            return self.parse_resource_property_element(ns, element, element_nodes)
            
        # Step 3: literal value, or empty.  Normalize into one node or none
        element.normalize()
        text_nodes = [n for n in element.childNodes if n.nodeType == n.TEXT_NODE]
        assert len(text_nodes) < 2
        
        if text_nodes:
            text = text_nodes[0].data
            return self.parse_literal_property_element(ns, element, text)
        else:
            return self.parse_empty_property_element(ns, element)


    def parse_resource_property_element(self, ns, element, subelements):
        """7.2.15: http://www.w3.org/TR/rdf-syntax-grammar/#resourcePropertyElt

        resourcePropertyElt:
 	    start-element(URI == propertyElementURIs ), attributes == set(idAttr?))
            ws* nodeElement ws*
            end-element()
        """
        
        ns = Namespaces(ns, element)

        if self.strict and len(subelements) > 1:
            raise RDFError('more than one sub-element in a predicate',
                           self.element)

        node = self.parse_node_element(ns, subelements[0])
        repr = domrepr.Repr(domrepr.ResourceProperty(self.doc, element, ns))
        return model.PredicateResource(
            self.root, repr, get_element_uri(element), node)
        

    def parse_literal_property_element(self, ns, element, text):
        """7.2.16: http://www.w3.org/TR/rdf-syntax-grammar/#literalPropertyElt

        literalPropertyElt:
 	    start-element(URI == propertyElementURIs ),
                attributes == set(idAttr?, datatypeAttr?))
            text()
            end-element()
        """

        ns = Namespaces(ns, element)

        type_uri = element.getAttributeNS(RDF_NS, 'datatype')
        if not type_uri:
            type_uri = None
            
        # TODO: xml:lang

        repr = domrepr.Repr(domrepr.LiteralProperty(self.doc, element, ns))
        node = model.LiteralNode(self.root, repr, text, type_uri)

        return model.PredicateLiteral(
            self.root, repr, get_element_uri(element), node)
        

    def parse_empty_property_element(self, ns, element):
        """7.2.21: http://www.w3.org/TR/rdf-syntax-grammar/#emptyPropertyElt

        emptyPropertyElt:
 	    start-element(URI == propertyElementURIs ),
                attributes == set(idAttr?, ( resourceAttr | nodeIdAttr )?, propertyAttr*))
            end-element()
        """

        ns = Namespaces(ns, element)

        resource_uri = element.getAttributeNS(RDF_NS, 'resource')
        node_id = element.getAttributeNS(RDF_NS, 'nodeID')

        if resource_uri and node_id:
            if self.strict:
                raise RDFError('both rdf:resource and rdf:nodeID attributes',
                               element)

        if resource_uri:
            node = self.root.get_resource_node(resource_uri)
        elif node_id:
            node = self.root.get_blank_node(model.NodeID(node_id))
        else:
            node = None

        # TODO: parse propertyAttr

        repr = domrepr.Repr(domrepr.EmptyProperty(self.doc, element, ns))

        if node is not None:
            node.reprs.append(repr)

            return model.PredicateEmpty(
                self.root, repr, get_element_uri(element), node)
        else:
            node = model.LiteralNode(self.root, repr, "", None)

            return model.PredicateLiteral(
                self.root, repr, get_element_uri(element), node)
            

class Namespaces(object):
    """Keep track of namespaces scope for each element
    and update it as necessary.
    """

    def __init__(self, parent, element):
        attrs = element.attributes
        assert attrs is not None, 'trying to track namespaces for non-element node'

        self.parent = parent
        self.element = element
        self.uri_prefix_map = {}

        if parent is None:
            # Grab everything up to root
            self._populate(element, None)
        else:
            # Grab everything up to parent element
            self._populate(element, parent.element)


    def _populate(self, element, stop_element):
        # Passed the root?
        if element.nodeType == element.DOCUMENT_NODE:
            return

        # Reach the parent?
        if element is stop_element:
            return
        
        # Recurse first, so that we overwrite anything added further below
        self._populate(element.parentNode, stop_element)

        attrs = element.attributes
        if attrs is None:
            return

        # Add all attributes
        for (name, value) in attrs.items():
            if name.startswith('xmlns:'):
                self.uri_prefix_map[value] = name[6:]
            elif name == 'xmlns':
                self.uri_prefix_map[value] = None
                
                
    def get_prefix(self, uri, preferred_prefix):
        """Return a prefix for URI in the current scope.

        If the URI is not known, it is added, using preferred_prefix
        if available.

        If None is returned, the URI is the default.
        """
        
        assert preferred_prefix, 'prefix must be non-empty'

        try:
            return self.uri_prefix_map[uri]
        except KeyError:
            pass


        # Recurse if we have a parent
        if self.parent:
            prefix = self.parent.get_prefix(uri, preferred_prefix)

            # If this prefix already in use for something else in this
            # scope, we must redefine the namespace here

            new_prefix = self._check_prefix(prefix)
            if new_prefix != prefix:
                prefix = new_prefix
                self.uri_prefix_map[uri] = prefix
                self.element.setAttribute('xmlns:' + prefix, uri)
            
            return prefix

        else:
            # Reached root, so add namespace to this scope and element
            prefix = self._check_prefix(preferred_prefix)
            self.uri_prefix_map[uri] = prefix
            self.element.setAttribute('xmlns:' + prefix, uri)
            return prefix


    def _check_prefix(self, preferred_prefix):
        prefix = preferred_prefix
        c = 1
        while prefix in self.uri_prefix_map.itervalues():
            c += 1
            prefix = preferred_prefix + str(c)

        return prefix
            


def iter_subelements(element):
    """Return an iterator over all child nodes that are elements"""

    for n in element.childNodes:
        if n.nodeType == n.ELEMENT_NODE:
            yield n
        
def is_rdf_element(element, name):
    """Return TRUE if this is an RDF element with the local NAME."""
    return (element.namespaceURI == RDF_NS
            and element.localName == name)
        
def get_element_uri(element):
    return model.QName(element.namespaceURI, element.prefix, element.localName)

    
