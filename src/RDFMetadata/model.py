# model - RDF model objects
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

"""Model RDF graphs in a way suitable for inline editing of the
underlying RDF/XML.
"""

import collections

class Root(collections.Mapping):
    def __init__(self, doc, root_element):
        super(Root, self).__init__()

        # FIXME: This XML stuff should go into the domrepr module instead
        self.doc = doc
        self.element = root_element

        # Some RDF/XML house-keeping to simplify modifying the tree
        # later
        self.root_element_is_rdf = None
        self.rdf_prefix = None
        
        self.resource_nodes = {}

        from . import parser
        parser.RDFXML(self)

    def __str__(self):
        return '\n'.join(map(str, self.resource_nodes.itervalues()))


    #
    # Support read-only Mapping interface to access the top subjects
    #
        
    def __getitem__(self, key):
        return self.resource_nodes[key]

    def __iter__(self):
        return iter(self.resource_nodes)

    def __len__(self):
        return len(self.resource_nodes)
    



class Node(object):
    def __init__(self, root):
        self.root = root


class SubjectNode(Node, collections.Sequence):

    def __init__(self, root, uri):
        super(SubjectNode, self).__init__(root)

        self.uri = uri
        self.reprs = []
        self.predicates = []
        

    def set_type(self, type_uri):
        pass

    def set_uri(self, uri):
        # TODO
        pass

    def __str__(self):
        s = '# {0}({1})\n'.format(self.__class__.__name__, self.uri)

        if self.predicates:
            s += '<{0}>\n    {1} .\n'.format(
                self.uri, ' ;\n    '.join(map(str, self.predicates)))

        return s

    #
    # Support read-only sequence interface to access the predicates
    #
        
    def __getitem__(self, item):
        return self.predicates[item]

    def __iter__(self):
        return iter(self.predicates)

    def __len__(self):
        return len(self.predicates)


class ResourceNode(SubjectNode):
    pass


class BlankNode(SubjectNode):
    pass


class LiteralNode(Node):
    def __init__(self, root, repr, value, type_uri = None):
        super(LiteralNode, self).__init__(root)
        self.repr = repr

        self.value = value
        self.type_uri = type_uri

    def set_value(self, value):
        self.value = value
        self.repr.change_content(value)

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


class Predicate(object):
    def __init__(self, root, repr, uri, object):
        self.root = root
        self.repr = repr
        self.uri = uri
        self.object = object
        
    def __str__(self):
        if isinstance(self.object, LiteralNode):
            if self.object.type_uri:
                return '<{0}> "{1}"^^<{2}>'.format(
                    self.uri, self.object.value, self.object.type_uri)
            else:
                return '<{0}> "{1}"'.format(self.uri, self.object.value)
        elif isinstance(self.object, SubjectNode):
            return '<{0}> <{1}>'.format(self.uri, self.object.uri)
        else:
            return '<{0}> ""'.format(self.uri)

    def set_value(self, value):
        if self.object:
            self.object.set_value(value)

    def set_type(self, type_uri):
        if self.object:
            self.object.set_type(type_uri)

class PredicateResource(Predicate):
    pass

class PredicateLiteral(Predicate):
    pass

class PredicateEmpty(Predicate):
    pass
