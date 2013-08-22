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
    def __init__(self, model_root_list):
        super(MainWindow, self).__init__(title = 'RDF Metadata Editor')

        self.editor = gtk_editor_widget.MetadataEditor(model_root_list[0])
        self.svglist = gtk_editor_widget.SVGNodeList(model_root_list, self.editor)

        self.paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        self.paned.set_position(200)
        self.paned.add1(self.svglist.widget)
        self.paned.add2(self.editor.widget)
        self.add(self.paned)
        # self.add(self.editor.widget)

def main():
    doc = minidom.parse(sys.stdin)

    # Use whatever rdf:RDF elements there is
    rdfs = doc.getElementsByTagNameNS("http://www.w3.org/1999/02/22-rdf-syntax-ns#", 'RDF')

    if not rdfs:
        sys.exit('no RDF found')

    # Parse all RDF nodes available
    model_root_list = []
    for rdf in rdfs:
        model_root_list.append(parser.parse_RDFXML(doc = doc, root_element = rdf))

    win = MainWindow(model_root_list)
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()
