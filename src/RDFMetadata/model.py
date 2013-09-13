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

from . import observer

#
# Events sent to observers of the model when it updates
#

class PredicateAdded(observer.Event): pass
class PredicateObjectChanged(observer.Event): pass


#
# Events that are sent to the model to update it when the underlying representation changes
#

class ResourceNodeReprAdded(observer.Event): pass
class BlankNodeReprAdded(observer.Event): pass
class PredicateNodeReprAdded(observer.Event): pass
class PredicateLiteralReprAdded(observer.Event): pass
class PredicateLiteralReprValueChanged(observer.Event): pass
class PredicateLiteralReprTypeChanged(observer.Event): pass

class Root(observer.Subject, collections.Mapping):
    def __init__(self, repr):
        super(Root, self).__init__()

        self.repr = repr
        self.repr.register_observer(self._on_repr_update)
        
        # There is exactly one instance for each URI or nodeID
        self.resource_nodes = {}
        self.blank_nodes = {}


    def _on_repr_update(self, event):
        if isinstance(event, ResourceNodeReprAdded):
            node = self._get_resource_node(event.uri)
        
        elif isinstance(event, BlankNodeReprAdded):
            node = self._get_blank_node(event.id)

        else:
            return

        node._add_repr(event.repr)
        

    def _on_node_update(self, event):
        # Just pass on the event to allow model users to choose
        # whether to listen to root updates or node updates
        self.notify_observers(event)


    def _get_resource_node(self, uri):
        """Return a ResourceNode for uri, creating one if it doesn't exist.
        """

        try:
            node = self.resource_nodes[uri]
        except KeyError:
            node = ResourceNode(self, uri)
            self.resource_nodes[uri] = node
            node.register_observer(self._on_node_update)

        return node


    def _get_blank_node(self, id):
        """Return a BlankNode for id, creating one if it doesn't exist.
        """

        try:
            node = self.blank_nodes[id]
        except KeyError:
            node = BlankNode(self, id)
            self.blank_nodes[id] = node
            node.register_observer(self._on_node_update)

        return node


    def _get_node(self, uri):
        """Return either a blank node or a resource node, depending on the type of URI.
        """
        
        if isinstance(uri, NodeID):
            return self._get_blank_node(uri)
        else:
            return self._get_resource_node(uri)


    def __str__(self):
        s = '\n'.join(map(str, self.resource_nodes.itervalues()))
        s += '\n'
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
        if ns_prefix:
            self.tag_name = ns_prefix + ':' + local_name
        else:
            self.tag_name = local_name
        super(QName, self).__init__(ns_uri + local_name)

    def __repr__(self):
        return '{0.__class__.__name__}("{0.ns_uri}", "{0.ns_prefix}", "{0.local_name}")'.format(self)


class NodeID(URI):
    """Used for the ID of a blank node.

    This isn't really an URI, but it's easier on users of the model if
    they can easily refer to it as that.
    """
    def __init__(self, node_id):
        if node_id:
            self.node_id = node_id
            self.external = True
        else:
            self.node_id = str(uuid.uuid1())
            self.external = False

        super(NodeID, self).__init__('_:' + self.node_id)
        
    def __repr__(self):
        if self.external:
            return '{0.__class__.__name__}("{0.node_id}")'.format(self)
        else:
            return '{0.__class__.__name__}(None)'.format(self)


class Node(observer.Subject, object):
    def __init__(self, root):
        super(Node, self).__init__()
        self.root = root


class SubjectNode(Node, collections.Sequence):

    def __init__(self, root, uri):
        super(SubjectNode, self).__init__(root)

        self.uri = uri
        self.reprs = []
        self.predicates = []
        
    def _add_repr(self, repr):
        assert repr not in self.reprs
        self.reprs.append(repr)
        repr.register_observer(self._on_repr_update)


    def _on_repr_update(self, event):
        if isinstance(event, PredicateNodeReprAdded):
            node = self.root._get_node(event.object_uri)
            self._add_predicate(event.repr, event.predicate_uri, node)

        elif isinstance(event, PredicateLiteralReprAdded):
            node = LiteralNode(self.root, event.repr, event.value, event.type_uri)
            self._add_predicate(event.repr, event.predicate_uri, node)


    def _add_predicate(self, repr, uri, object):
        pred = Predicate(self.root, repr, uri, object)
        
        self.predicates.append(pred)
        self.notify_observers(PredicateAdded(node = self, predicate = pred))

        # Listen on predicate model updates
        # TODO: remember to unregister when removing the predicate
        pred.register_observer(self._on_predicate_update)


    def _on_predicate_update(self, event):
        # Just pass on the event to allow model users to choose
        # whether to listen to node updates or predicate updates
        self.notify_observers(event)


    def add_literal_node(self, qname, value = '', type_uri = None):
        # This must be true, right?
        assert self.reprs

        self.reprs[0].add_literal_node(self, qname, value, type_uri)


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
    def __str__(self):
        s = '# ResourceNode({0})\n'.format(self.uri)

        for pred in self.predicates:
            s += '<{0}>\t{1} .\n'.format(self.uri, pred)

        return s


class BlankNode(SubjectNode):
    def __str__(self):
        s = '# BlankNode({0})\n'.format(self.uri)

        for pred in self.predicates:
            s += '{0}\t{1} .\n'.format(self.uri, pred)

        return s


class LiteralNode(Node):
    def __init__(self, root, repr, value, type_uri = None):
        super(LiteralNode, self).__init__(root)
        self.repr = repr
        self.value = value
        self.type_uri = type_uri

        repr.register_observer(self._on_repr_update)

    def set_value(self, value):
        self.repr.set_literal_value(value)


    def set_type_uri(self, type_uri):
        self.repr.set_datatype(type_uri)

        
    def _on_repr_update(self, event):
        if isinstance(event, PredicateLiteralReprValueChanged):
            assert self.repr.is_event_source(event)
            self.value = event.value

        elif isinstance(event, PredicateLiteralReprTypeChanged):
            assert self.repr.is_event_source(event)
            self.type_uri = event.type_uri
            

class Predicate(observer.Subject, object):
    def __init__(self, root, repr, uri, object):
        super(Predicate, self).__init__()

        self.root = root
        self.repr = repr
        self.uri = uri
        self.object = object

        repr.register_observer(self._on_repr_update)

        # As a special case, also listen on updates to literal nodes
        # so we can propagate changes in its value to model observers
        if isinstance(object, LiteralNode):
            object.repr.register_observer(self._on_object_repr_update)

        # TODO: remember to unregister from the object.repr when
        # object is changed later
        
    def _on_repr_update(self, event):
        pass
    
    def _on_object_repr_update(self, event):
        if (isinstance(event, PredicateLiteralReprValueChanged)
            or isinstance(event, PredicateLiteralReprTypeChanged)):
            assert self.object.repr.is_event_source(event)
            self.notify_observers(
                PredicateObjectChanged(
                    predicate = self, object = self.object))


    def __str__(self):
        if isinstance(self.object, LiteralNode):
            if self.object.type_uri:
                return '<{0}>\t"{1}"^^<{2}>'.format(
                    self.uri, self.object.value, self.object.type_uri)
            else:
                return '<{0}>\t"{1}"'.format(self.uri, self.object.value)
        elif isinstance(self.object, ResourceNode):
            return '<{0}>\t<{1}>'.format(self.uri, self.object.uri)
        elif isinstance(self.object, BlankNode):
            return '<{0}>\t{1}'.format(self.uri, self.object.uri)
        else:
            return '<{0}>\t""'.format(self.uri)

