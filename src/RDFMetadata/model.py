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
import uuid

class Root(collections.Mapping):
    def __init__(self, repr):
        super(Root, self).__init__()

        self.repr = repr

        # There is exactly one instance for each URI or nodeID
        self.resource_nodes = {}
        self.blank_nodes = {}


    def get_resource_node(self, uri):
        """Return a ResourceNode for uri, creating one if it doesn't exist.
        """

        try:
            node = self.resource_nodes[uri]
        except KeyError:
            node = ResourceNode(self, uri)
            self.resource_nodes[uri] = node

        return node


    def get_blank_node(self, uri):
        """Return a BlankNode for uri, creating one if it doesn't exist.
        """

        try:
            node = self.blank_nodes[uri]
        except KeyError:
            node = BlankNode(self, uri)
            self.blank_nodes[uri] = node

        return node


    def __str__(self):
        s = '\n'.join(map(str, self.resource_nodes.itervalues()))
        s += '\n'.join(map(str, self.blank_nodes.itervalues()))
        return s

    #
    # Support read-only Mapping interface to access the top subjects
    #
        
    def __getitem__(self, key):
        return self.resource_nodes[key]

    def __iter__(self):
        return iter(self.resource_nodes)

    def __len__(self):
        return len(self.resource_nodes)
    

class URI(object):
    """Base class for representing different kinds of URIs.

    Must be immutable (TODO: figure out decorators for that.)
    """

    def __init__(self, uri):
        self.uri = uri

    def __cmp__(self, other):
        return cmp(self.uri, str(other))

    def __hash__(self):
        return hash(self.uri)
    
    def __str__(self):
        return self.uri
    

class QName(URI):
    """A fully qualified name, used mainly by predicates.

    Keeps track of all the components of the name, but behaves like an
    URI string otherwise.

    """

    def __init__(self, ns_uri, ns_prefix, local_name):
        self.ns_uri = ns_uri
        self.ns_prefix = ns_prefix
        self.local_name = local_name
        super(QName, self).__init__(ns_uri + local_name)


class NodeID(URI):
    """Used for the ID of a blank node.
    """
    def __init__(self, node_id):
        if node_id:
            self.node_id = node_id
            self.external = True
        else:
            self.node_id = str(uuid.uuid1())
            self.external = False

        super(NodeID, self).__init__('_:' + self.node_id)
        

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
        self.repr.set_literal_value(value)

        # TODO: perhaps this should be triggered by XML notifications?
        self.value = value


    def set_type_uri(self, type_uri):
        self.type_uri = type_uri

        self.repr.set_datatype(type_uri)
        

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


class PredicateResource(Predicate):
    pass

class PredicateLiteral(Predicate):
    pass

class PredicateEmpty(Predicate):
    pass
