#!/usr/bin/python

# gtk_editor_widget - Metadata editor widget for GTK
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.


import sys
from gi.repository import Gtk

from RDFMetadata import parser, gtk_editor_widget

# Temporary: move into proper file loaders
from xml.dom import minidom

class MainWindow(Gtk.Window):
    def __init__(self, root):
        super(MainWindow, self).__init__(title = 'RDF Metadata Editor')

        self.editor = gtk_editor_widget.MetadataEditor(root)
        self.add(self.editor.widget)
        
def main():
    doc = minidom.parse(sys.stdin)

    # Use whatever rdf:RDF elements there is
    rdfs = doc.getElementsByTagNameNS("http://www.w3.org/1999/02/22-rdf-syntax-ns#", 'RDF')

    if not rdfs:
        sys.exit('no RDF found')
    
    # For now just use the first one
    root = parser.parse_RDFXML(doc = doc, root_element = rdfs[0])

    win = MainWindow(root)
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()
    
