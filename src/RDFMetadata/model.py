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

class RDFRoot(collections.Mapping):
    def __init__(self, doc, root_element):
        super(RDFRoot, self).__init__()
        
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
    



class RDFNode(object):
    def __init__(self, root):
        self.root = root


class RDFSubjectNode(RDFNode, collections.Sequence):

    def __init__(self, root, uri):
        super(RDFSubjectNode, self).__init__(root)

        self.uri = uri
        self.description_nodes = []
        self.predicates = []
        

    def set_type(self, type_uri):
        pass

    def set_uri(self, uri):
        # TODO
        pass

    def __str__(self):
        s = '# {0}({1})\n'.format(self.__class__.__name__, self.uri)

        if self.predicates:
            s += '<{0}>\n    {1}.\n'.format(
                self.uri, ';\n    '.join(map(str, self.predicates)))

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


class RDFResourceNode(RDFSubjectNode):
    pass


class RDFBlankNode(RDFSubjectNode):
    pass


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
        
    def __str__(self):
        if isinstance(self.object, RDFLiteralNode):
            if self.object.type_uri:
                return '<{0}> "{1}"^^<{2}>'.format(
                    self.uri, self.object.value, self.object.type_uri)
            else:
                return '<{0}> "{1}"'.format(self.uri, self.object.value)
        elif isinstance(self.object, RDFSubjectNode):
            return '<{0}> <{1}>'.format(self.uri, self.object.uri)
        else:
            return '<{0}> ""'.format(self.uri)

    def set_value(self, value):
        if self.object:
            self.object.set_value(value)

    def set_type(self, type_uri):
        if self.object:
            self.object.set_type(type_uri)

