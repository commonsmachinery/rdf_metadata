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
from RDFMetadata import model

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
    <menu action='EditMenu'>
      <menuitem action='AddProperty'/>
    </menu>
  </menubar>
  <toolbar name='Toolbar'>
    <toolitem action='ExpandAll'/>
    <toolitem action='CollapseAll'/>
    <toolitem action='PrintXml'/>
    <toolitem action='AddProperty'/>
  </toolbar>
</ui>'''

class MainWindow(Gtk.Window):
    __gtype_name__ = "MainWindow"

    def __init__(self, model_root_list):
        super(MainWindow, self).__init__(title = 'RDF Metadata Editor')

        action_entries = [
            ("FileMenu", None, "_File" ),
            ("EditMenu", None, "_Edit" ),
            ("Quit", Gtk.STOCK_QUIT,
             "_Quit", "<control>Q",
             "Quit",
             self.on_quit),
            ("ExpandAll", Gtk.STOCK_ZOOM_IN,
             "_Expand all", None,
             "Expand All",
             self.on_expand_all),
            ("CollapseAll", Gtk.STOCK_ZOOM_OUT,
             "_Collapse All", None,
             "Collapse All",
             self.on_collapse_all),
            ("PrintXml", Gtk.STOCK_PRINT,
             "_Print XML", None,
             "Print XML",
             self.on_print_xml),
            ("AddProperty", Gtk.STOCK_ADD,
             "_Add Property", None,
             "Add Property",
             self.on_add_property),
        ]

        self.actions = Gtk.ActionGroup("Actions")
        self.actions.add_actions(action_entries)
        
        menu_manager = Gtk.UIManager()
        menu_manager.insert_action_group(self.actions)
        self.add_accel_group(menu_manager.get_accel_group())
        menu_manager.add_ui_from_string(ui_info)

        vbox = Gtk.VBox()
        self.add(vbox)

        menubar = menu_manager.get_widget("/MenuBar")
        vbox.pack_start(menubar, False, False, 0)

        toolbar = menu_manager.get_widget("/Toolbar")
        vbox.pack_start(toolbar, False, False, 0)

        self.paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        
        vbox.add(self.paned)

        self.editor = MetadataEditor(model_root_list[0], self)
        # Pass the self.paned object along to SVGNodeList to let it
        # keep track of which metadata_editor to show.
        self.svglist = SVGNodeList(model_root_list, self.paned, self)

        vbox.show_all()
        self.set_default_size(600, 600)
        self.paned.set_position(200)
    
    # temporary method until we restructure the UI to use notebook, if decided
    def _get_active_editor(self):
        tree_model, tree_iter = self.svglist.treeview.get_selection().get_selected()
        if tree_iter:
            return tree_model[tree_iter][0]
        return None

    def on_expand_all(self, action):
        editor = self._get_active_editor()
        if editor:
            editor.tree_view.expand_all()

    def on_collapse_all(self, action):
        editor = self._get_active_editor()
        if editor:
            editor.tree_view.collapse_all()

    def on_print_xml(self, action):
        editor = self._get_active_editor()
        if editor:
            editor.root.repr.element.writexml(sys.stdout)

    def on_add_property(self, action):
        editor = self._get_active_editor()
        if editor is None:
            return

        tree_model, tree_iter = editor.tree_view.get_selection().get_selected()
        assert tree_iter is not None

        obj = editor.tree_store[tree_iter][0]

        if isinstance(obj, model.SubjectNode):
            pass
        elif (isinstance(obj, model.Predicate)
              and isinstance(obj.object, model.SubjectNode)):
            obj = obj.object
        else:
            assert False, 'attempting to add property to a non-SubjectNode'

        # Make sure the row is expanded
        path = editor.tree_store.get_path(tree_iter)
        editor.tree_view.expand_row(path, False)

        obj.add_literal_node(
            model.QName('http://test/', 'test', 'Test'),
            'new value', 'http://test/type')

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
