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

from RDFMetadata import parser

from editor.MetadataEditor import MetadataEditor
from editor.SVGNodeList import SVGNodeList

# Temporary: move into proper file loaders
from xml.dom import minidom

ui_info = \
'''<ui>
  <menubar name='MenuBar'>
    <menu action='FileMenu'>
      <menuitem action='Quit'/>
    </menu>
  </menubar>
</ui>'''

class MainWindow(Gtk.Window):
    __gtype_name__ = "MainWindow"

    def __init__(self, model_root_list):
        super(MainWindow, self).__init__(title = 'RDF Metadata Editor')

        action_entries = [
            ("FileMenu", None, "_File" ),
            ("Quit", Gtk.STOCK_QUIT,
             "_Quit", "<control>Q",
             "Quit",
             self.on_quit),
        ]

        actions = Gtk.ActionGroup("Actions")
        actions.add_actions(action_entries)
        
        menu_manager = Gtk.UIManager()
        menu_manager.insert_action_group(actions)
        self.add_accel_group(menu_manager.get_accel_group())
        menu_manager.add_ui_from_string(ui_info)

        vbox = Gtk.VBox()
        self.add(vbox)

        menubar = menu_manager.get_widget("/MenuBar")
        vbox.pack_start(menubar, False, False, 0)

        self.paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        self.paned.set_position(200)
        vbox.add(self.paned)

        self.editor = MetadataEditor(model_root_list[0])
        # Pass the self.paned object along to SVGNodeList to let it
        # keep track of which metadata_editor to show.
        self.svglist = SVGNodeList(model_root_list, self.paned)

        vbox.show_all()
        self.set_default_size(600, 600)

    def on_quit(self, *args):
        self.destroy()

    def do_destroy(self, *args):
        Gtk.main_quit()

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
    win.show()
    Gtk.main()

if __name__ == '__main__':
    main()
