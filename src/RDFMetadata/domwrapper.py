# domwrapper - Wrapper classes around the DOM that notifies observers on changes
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

from . import observer

#
# DOM Events
#

class ChildAdded(observer.Event): pass
class ChildRemoved(observer.Event): pass


#
# DOM wrappers
#

class Node(observer.Subject):
    """General Node wrapper.  Generates the following events:

    - ChildAdded: parent, child, after
    - ChildRemoved: parent, child
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
    """Element wrapper.  Generates the following events
    in addition to the Node events:

    TODO: list events
    """

    # def setAttribute(self, attname, value):
    # def setAttributeNS(self, namespaceURI, qualifiedName, value):
    # def setAttributeNode(self, attr):
    # def removeAttribute(self, name):
    # def removeAttributeNS(self, namespaceURI, localName):
    # def removeAttributeNode(self, node):
    # removeAttributeNodeNS = removeAttributeNode


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
    
