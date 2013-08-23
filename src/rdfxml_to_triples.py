#!/usr/bin/python

# rdfxml_to_triples - Parse RDF/XML on stdin and output N-Triples
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import sys
from RDFMetadata import parser

#from RDFMetadata import observer
#observer.global_observer = observer.log_observer

from xml.dom import minidom

def main():
    doc = minidom.parse(sys.stdin)

    # Use whatever rdf:RDF elements there is
    rdfs = doc.getElementsByTagNameNS("http://www.w3.org/1999/02/22-rdf-syntax-ns#", 'RDF')

    if not rdfs:
        sys.exit('no RDF found')

    for rdf in rdfs:
        sys.stdout.write('### {0}\n\n'.format(get_element_path(rdf)))
        root = parser.parse_RDFXML(doc = doc, root_element = rdf)

        sys.stdout.write(str(root))
        sys.stdout.write('\n')


def get_element_path(element):
    if element.nodeType != element.ELEMENT_NODE:
        return ''
    else:
        return '{0}/{1}'.format(get_element_path(element.parentNode), element.tagName)


if __name__ == '__main__':
    main()

    
