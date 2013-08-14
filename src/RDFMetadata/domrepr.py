# domrepr - Link from RDF model objects to underlying DOM representation
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.


class Repr(object):
    """Intermediate object for the representation of a node.

    This is needed since operations that change data may also change
    the type of the representation.
    """

    def __init__(self, repr):
        self.repr = repr

    def change_content(self, text):
        self.repr = self.repr.change_content(text)


class TypedRepr(object):
    def __init__(self, doc, element):
        self.doc = doc
        self.element = element

    def to(self, cls):
        return cls(self.doc, self.element)

class DescriptionNode(TypedRepr):
    pass

class TypedNode(TypedRepr):
    pass

class ResourceProperty(TypedRepr):
    pass

class LiteralProperty(TypedRepr):
    def change_content(self, text):
        # Drop old content first
        while True:
            n = self.element.firstChild
            if n is None:
                break
            self.element.removeChild(n)

        if text:
            # Set new
            self.element.appendChild(self.doc.createTextNode(text))
            return self
        else:
            # No more content
            return self.to(EmptyProperty)


class EmptyProperty(TypedRepr):
    def change_content(self, text):
        if text:
            # Since it will no longer be empty, change to a LiteralProperty instead

            # TODO: check that that is possible

            new = self.to(LiteralProperty)
            new.change_content(text)
            return new
        else:
            return self
