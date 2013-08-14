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


class RDFXML(object):
    """Parse RDFXML into model object directly.  This class is allowed
    to modify the internal member variables of the model objects.
    """

    def __init__(self, root, strict = True):
        self.root = root
        self.strict = True

        # Determine if we're starting with is rdf:RDF or some other element
        self.root.root_element_is_rdf = is_rdf_element(self.root.element, 'RDF')

        # This is ugly: I can't find an easy way to ask the DOM tree
        # for the prefix associated with a namespace, so just grab it
        # when we see it in an RDF element...
        if self.root.element.namespaceURI == RDF_NS:
            self.root.rdf_prefix = self.root.element.prefix

        self.parse_node_element_list(self.root.element, top_level = True)
        
    
    def parse_node_element_list(self, element, top_level = False):
        """7.2.10: http://www.w3.org/TR/rdf-syntax-grammar/#nodeElementList

        nodeElementList: ws* (nodeElement ws* )*
        """

        # Look for rdf:Descriptions
        # TODO: also look for types nodes in rdf:RDF

        for el in iter_subelements(element):
            if is_rdf_element(el, 'Description'):

                # Ugly hack as above: grab prefix if possible
                if self.root.rdf_prefix is None:
                    self.root.rdf_prefix = el.prefix

                self.parse_node_element(el, top_level)


    def parse_node_element(self, element, top_level = False):
        """7.2.11: http://www.w3.org/TR/rdf-syntax-grammar/#nodeElement

        nodeElement:
          start-element(URI == nodeElementURIs
              attributes == set((idAttr | nodeIdAttr | aboutAttr )?, propertyAttr*))
          propertyEltList
          end-element()
        """
        
        repr = domrepr.Repr(domrepr.DescriptionNode(self.root.doc, element))

        # Check what kind of node this is by presence of rdf:ID,
        # rdf:nodeID or rdf:about

        ID = element.getAttributeNS(RDF_NS, 'ID')
        nodeID = element.getAttributeNS(RDF_NS, 'nodeID')
        about = element.getAttributeNS(RDF_NS, 'about')


        # What if none are provided?
        if not ID and not nodeID and not about:
            if not top_level:
                # Generate a nodeID
                nodeID = uuid.uuid1()

        if ID and not nodeID and not about:
            # TODO
            assert False, 'not implemented yet'

        elif nodeID and not ID and not about:
            # TODO
            assert False, 'not implemented yet'

        elif not ID and not nodeID:
            # about can be "" here, but then we must be on the top level
            if not about:
                assert top_level

            try:
                node = self.root[about]
            except KeyError:
                node = model.ResourceNode(self, about)
                self.root.resource_nodes[about] = node

        node.reprs.append(repr)

        # TODO: parse property attributes

        self.parse_property_element_list(node, element)

        return node

        
    def parse_property_element_list(self, node, element):
        """7.2.13: http://www.w3.org/TR/rdf-syntax-grammar/#propertyEltList

        propertyEltList: ws* (propertyElt ws* ) *
        """
        
        for el in iter_subelements(element):
            # TODO: filter out all rdf: elements?

            predicate = self.parse_property_element(el)
            if predicate is not None:
                node.predicates.append(predicate)
            

            
    def parse_property_element(self, element):
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
            return self.parse_resource_property_element(element, element_nodes)
            
        # Step 3: literal value, or empty.  Normalize into one node or none
        element.normalize()
        text_nodes = [n for n in element.childNodes if n.nodeType == n.TEXT_NODE]
        assert len(text_nodes) < 2
        
        if text_nodes:
            text = text_nodes[0].data
            return self.parse_literal_property_element(element, text)
        else:
            return self.parse_empty_property_element(element)


    def parse_resource_property_element(self, element, subelements):
        """7.2.15: http://www.w3.org/TR/rdf-syntax-grammar/#resourcePropertyElt

        resourcePropertyElt:
 	    start-element(URI == propertyElementURIs ), attributes == set(idAttr?))
            ws* nodeElement ws*
            end-element()
        """
        
        if self.strict and len(subelements) > 1:
            raise RDFError('more than one sub-element in a predicate',
                           self.element)

        node = self.parse_node_element(subelements[0])
        repr = domrepr.Repr(domrepr.ResourceProperty(self.root.doc, element))
        return model.PredicateResource(
            self.root, repr, get_element_uri(element), node)
        

    def parse_literal_property_element(self, element, text):
        """7.2.16: http://www.w3.org/TR/rdf-syntax-grammar/#literalPropertyElt

        literalPropertyElt:
 	    start-element(URI == propertyElementURIs ),
                attributes == set(idAttr?, datatypeAttr?))
            text()
            end-element()
        """

        type_uri = element.getAttributeNS(RDF_NS, 'datatype')
        if not type_uri:
            type_uri = None
            
        # TODO: xml:lang

        repr = domrepr.Repr(domrepr.LiteralProperty(self.root.doc, element))
        node = model.LiteralNode(self.root, repr, text, type_uri)

        return model.PredicateLiteral(
            self.root, repr, get_element_uri(element), node)
        

    def parse_empty_property_element(self, element):
        """7.2.21: http://www.w3.org/TR/rdf-syntax-grammar/#emptyPropertyElt

        emptyPropertyElt:
 	    start-element(URI == propertyElementURIs ),
                attributes == set(idAttr?, ( resourceAttr | nodeIdAttr )?, propertyAttr*))
            end-element()
        """

        resource_uri = element.getAttributeNS(RDF_NS, 'resource')
        node_id = element.getAttributeNS(RDF_NS, 'nodeID')

        if resource_uri and node_id:
            if self.strict:
                raise RDFError('both rdf:resource and rdf:nodeID attributes',
                               element)

        repr = domrepr.Repr(domrepr.EmptyProperty(self.root.doc, element))

        if resource_uri:
            try:
                node = self.root[resource_uri]
            except KeyError:
                node = model.ResourceNode(self, resource_uri)
                self.root.resource_nodes[resource_uri] = node

            node.reprs.append(repr)

            return model.PredicateEmpty(
                self.root, repr, get_element_uri(element), node)

        elif node_id:
            assert False, 'not implemented yet'

        else:
            node = model.LiteralNode(self.root, repr, "", None)

            return model.PredicateLiteral(
                self.root, repr, get_element_uri(element), node)
            

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
    return element.namespaceURI + element.localName

    
