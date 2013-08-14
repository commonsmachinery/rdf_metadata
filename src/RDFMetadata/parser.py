# parser - parse RDF/XML into model objects
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import xml.dom

from . import model

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
        """

        # Look for rdf:Descriptions
        # TODO: also look for types nodes in rdf:RDF

        for el in iter_subelements(element):
            if is_rdf_element(el, 'Description'):

                # Ugly hack as above: grab prefix if possible
                if self.root.rdf_prefix is None:
                    self.root.rdf_prefix = el.prefix

                self.parse_node_element(None, el)


    def parse_node_element(self, predicate, element):
        """7.2.11: http://www.w3.org/TR/rdf-syntax-grammar/#nodeElement
        """
        
        # Check what kind of node this is by presence of rdf:ID,
        # rdf:nodeID or rdf:about

        ID = element.getAttributeNS(RDF_NS, 'ID')
        nodeID = element.getAttributeNS(RDF_NS, 'nodeID')
        about = element.getAttributeNS(RDF_NS, 'about')
        
        # What if none are provided?
        if not ID and not nodeID and not about:
            if predicate is not None:
                # If not top-level, then we generate a nodeID
                nodeID = uuid.uuid1()
            # Else on top-level this means an rdf:about=""

        if ID and not nodeID and not about:
            # TODO
            assert False, 'not implemented yet'

        elif nodeID and not ID and not about:
            # TODO
            assert False, 'not implemented yet'

        elif not ID and not nodeID:
            # about can be "" here, but then we must be on the top level
            if not about:
                assert predicate is None

            try:
                node = self.root[about]
            except KeyError:
                node = model.RDFResourceNode(self, about)
                self.root.resource_nodes[about] = node

        node.description_nodes.append(element)

        if predicate is not None:
            predicate.object = node

        # TODO: parse property attributes

        self.parse_property_element_list(node, element)

        
    def parse_property_element_list(self, node, element):
        """7.2.13: http://www.w3.org/TR/rdf-syntax-grammar/#propertyEltList
        """
        
        for el in iter_subelements(element):
            # TODO: filter out all rdf: elements?

            uri = el.namespaceURI + el.localName
            predicate = model.RDFPredicate(self.root, uri)
            predicate.element = el
            node.predicates.append(predicate)

            self.parse_property_element(predicate, el)

            
    def parse_property_element(self, predicate, element):
        """7.2.14: http://www.w3.org/TR/rdf-syntax-grammar/#propertyElt

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
            self.parse_resource_property_element(predicate, element_nodes)
            return
            
        # Step 3: literal value, or empty.  Normalize into one node or none
        element.normalize()
        text_nodes = [n for n in element.childNodes if n.nodeType == n.TEXT_NODE]
        assert len(text_nodes) < 2
        
        if len(text_nodes) == 0:
            text = ''
        else:
            text = text_nodes[0].data
            
        self.parse_literal_property_element(predicate, element, text)


    def parse_literal_property_element(self, predicate, element, text):
        """7.2.16: http://www.w3.org/TR/rdf-syntax-grammar/#literalPropertyElt
        """

        type_uri = element.getAttributeNS(RDF_NS, 'datatype')
        if not type_uri:
            type_uri = None
            
        # TODO: xml:lang
        predicate.object = model.RDFLiteralNode(self.root, predicate, text, type_uri)
        

    def parse_resource_property_element(self, predicate, element_nodes):
        """7.2.15: http://www.w3.org/TR/rdf-syntax-grammar/#resourcePropertyElt
        """
        
        if self.strict and len(element_nodes) > 1:
            raise RDFError('more than one sub-element in a predicate',
                           self.element)

        self.parse_node_element(predicate, element_nodes[0])
        

def iter_subelements(element):
    """Return an iterator over all child nodes that are elements"""

    for n in element.childNodes:
        if n.nodeType == n.ELEMENT_NODE:
            yield n
        
def is_rdf_element(element, name):
    """Return TRUE if this is an RDF element with the local NAME."""
    return (element.namespaceURI == RDF_NS
            and element.localName == name)
        
