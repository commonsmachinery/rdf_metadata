# domwrapper - Wrapper classes around the DOM that notifies observers on changes
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

from xml.dom import minidom

from . import observer

#
# DOM Events
#

class ChildAdded(observer.Event):
    """Event when a child has been added to a node.

    Parameters:

    - parent: the parent Node 
    - child: the added child Node
    - after: the child was added after this Node, or None
    """
    pass

class ChildRemoved(observer.Event):
    """Event when a child has been removed from a node.

    Parameters:

    - parent: the parent Node
    - child: the removed child Node
    """
    pass


class AttributeSet(observer.Event):
    """Event when an attribute is set (or changed, if already set).

    Parameters:

    - element: the parent Element
    - attr: the new or updated Attr 
    """
    pass

class AttributeRemoved(observer.Event): 
    """Event when an attribute is removed.

    Parameters:

    - element: the parent Element
    - attr: the removed Attr
    """
    pass

#
# DOM wrappers
#

class Node(observer.Subject):
    """General Node wrapper.  Generates the following events:

    ChildAdded
    ChildRemoved
    """

    def __init__(self, node):
        super(Node, self).__init__()
        self._real_node = node

    # Generic passthrough
    def __getattr__(self, attr):
        return getattr(self._real_node, attr)

    def insertBefore(self, newChild, refChild):
        after = refChild.previousSibling
        self._real_node.insertBefore(newChild, refChild)
        self.notify_observers(
            ChildAdded(parent = self,
                       child = newChild,
                       after = after))
            
    def appendChild(self, node):
        after = self._real_node.lastChild
        self._real_node.appendChild(node)
        self.notify_observers(
            ChildAdded(parent = self,
                       child = node,
                       after = after))
        
    def replaceChild(self, newChild, oldChild):
        after = oldChild.previousSibling
        self._real_node.replaceChild(newChild, oldChild)
        self.notify_observers(
            ChildRemoved(parent = self,
                         child = oldChild))
        self.notify_observers(
            ChildAdded(parent = self,
                       child = newChild,
                       after = after))

    def removeChild(self, oldChild):
        self._real_node.removeChild(oldChild)
        self.notify_observers(
            ChildRemoved(parent = self,
                         child = oldChild))
     

class Element(Node):
    """Element wrapper.

    ChildAdded
    ChildRemoved
    AttributeSet
    AttributeRemoved
    """

    def setAttribute(self, attname, value):
        self._real_node.setAttribute(attname, value)
        self.notify_observers(
            AttributeSet(element = self,
                         attr = self.getAttributeNode(attname)))


    def setAttributeNS(self, namespaceURI, qualifiedName, value):
        self._real_node.setAttributeNS(namespaceURI, qualifiedName, value)
        attr = self.getAttributeNodeNS(namespaceURI,
                                       minidom._nssplit(qualifiedName)[1])
        self.notify_observers(
            AttributeSet(element = self, attr = attr))


    def setAttributeNode(self, attr):
        self._real_node.setAttributeNode(attr)
        self.notify_observers(
            AttributeSet(element = self, attr = attr))


    def removeAttribute(self, name):
        attr = self.getAttributeNode(name)
        if attr:
            self._real_node.removeAttribute(name)
            self.notify_observers(AttributeRemoved(element = self, attr = attr))

        
    def removeAttributeNS(self, namespaceURI, localName):
        attr = self.getAttributeNodeNS(namespaceURI, localName)
        if attr:
            self._real_node.removeAttributeNS(namespaceURI, localName)
            self.notify_observers(AttributeRemoved(element = self, attr = attr))
        
    def removeAttributeNode(self, node):
        self._real_node.removeAttributeNode(node)
        self.notify_observers(AttributeRemoved(element = self, attr = node))

    removeAttributeNodeNS = removeAttributeNode


class Text(Node):
    """Element wrapper.  Generates the following events
    in addition to the Node events:

    TODO: list events
    """

    def __setattr__(self, name, value):
        if name == "data" or name == "nodeValue":
            self.__dict__['data'] = self.__dict__['nodeValue'] = value
        else:
            self.__dict__[name] = value
    
