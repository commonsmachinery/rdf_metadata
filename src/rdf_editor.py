#!/usr/bin/python

# gtk_editor_widget - Metadata editor widget for GTK
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#          Artem Popov <artfwo@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.


import sys, argparse
from gi.repository import Gtk

from RDFMetadata import parser
from RDFMetadata import model

from editor.MetadataEditor import MetadataEditor
from editor.AddPropertyDialog import AddPropertyDialog


# Temporary: move into proper file loaders
from xml.dom import minidom
import xml.parsers.expat

ui_info = \
'''<ui>
  <menubar name='MenuBar'>
    <menu action='FileMenu'>
      <menuitem action='FileOpen'/>
      <menuitem action='FileSave'/>
      <menuitem action='FileSaveAs'/>
      <separator/>
      <menuitem action='Quit'/>
    </menu>
    <menu action='EditMenu'>
      <menuitem action='AddProperty'/>
      <menuitem action='RemoveProperty'/>
    </menu>
  </menubar>
  <toolbar name='Toolbar'>
    <toolitem action='FileOpen'/>
    <toolitem action='FileSave'/>
    <separator/>
    <toolitem action='ExpandAll'/>
    <toolitem action='CollapseAll'/>
    <separator/>
    <toolitem action='AddProperty'/>
    <toolitem action='RemoveProperty'/>
  </toolbar>
</ui>'''

class MainWindow(Gtk.Window):
    __gtype_name__ = "MainWindow"

    def __init__(self):
        super(MainWindow, self).__init__(title = 'RDF Metadata Editor')

        action_entries = [
            ("FileMenu", None, "_File" ),
            ("EditMenu", None, "_Edit" ),
            ("FileOpen", Gtk.STOCK_OPEN,
             "_Open", "<control>O",
             "Open",
             self.on_file_open),
            ("FileSave", Gtk.STOCK_SAVE,
             "_Save", "<control>S",
             "Save",
             self.on_file_save),
            ("FileSaveAs", Gtk.STOCK_SAVE_AS,
             "_Save As...", "<control><shift>S",
             "Save As",
             self.on_file_save_as),
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
            ("AddProperty", Gtk.STOCK_ADD,
             "_Add Property", None,
             "Add Property",
             self.on_add_property),
            ("RemoveProperty", Gtk.STOCK_REMOVE,
             "_Remove Property", None,
             "Remove Property",
             self.on_remove_property),
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

        # Liststore columns: editor, page, Name to be displayed, Tooltip string
        self.node_store = Gtk.ListStore(object, int, str)
        self.node_view = Gtk.TreeView(model=self.node_store)

        column = Gtk.TreeViewColumn("SVG Nodes", Gtk.CellRendererText(), text=2)
        self.node_view.append_column(column)
        self.node_view.get_selection().connect('changed', self._on_node_view_selection_changed)

        sw = Gtk.ScrolledWindow(shadow_type=Gtk.ShadowType.IN)
        sw.add(self.node_view)
        self.paned.add1(sw)

        self.notebook = Gtk.Notebook(show_tabs=False)
        self.paned.add2(self.notebook)

        vbox.show_all()
        self.set_default_size(800, 600)
        self.paned.set_position(200)

        self.filename = None
        self.doc = None
        self.update_ui()
    
    # hacked to return self.node_view selection in the process of moving to Gtk.Notebook
    # TODO: when (if) a widget-centric MetadataEditor lands, remove it in favour of notebook.current_page
    def _get_active_editor(self):
        tree_model, tree_iter = self.node_view.get_selection().get_selected()
        if tree_iter:
            return tree_model[tree_iter][0]
        return None

    # enable/disable certain actions depending on the document state
    def update_ui(self):
        self.actions.get_action("AddProperty").set_sensitive(self.doc is not None)
        self.actions.get_action("FileSaveAs").set_sensitive(self.doc is not None)
        self.actions.get_action("FileSave").set_sensitive(self.filename is not None)

        editor = self._get_active_editor()
        if editor:
            self.actions.get_action("AddProperty").set_sensitive(editor.add_enabled())
            self.actions.get_action("RemoveProperty").set_sensitive(editor.remove_enabled())
        else:
            self.actions.get_action("AddProperty").set_sensitive(False)
            self.actions.get_action("RemoveProperty").set_sensitive(False)

            
    def load_file(self, filename):
        try:
            doc = minidom.parse(filename)
            # Use whatever rdf:RDF elements there is
            rdfs = doc.getElementsByTagNameNS("http://www.w3.org/1999/02/22-rdf-syntax-ns#", 'RDF')
        except xml.parsers.expat.ExpatError, e:
            dialog = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK, "Error")
            dialog.format_secondary_text(str(e))
            dialog.run()
            dialog.destroy()
            return

        if not rdfs:
            dialog = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK, "Error")
            dialog.format_secondary_text("No RDFs found.")
            dialog.run()
            dialog.destroy()
            return

        self.node_store.clear()
        for i in range(self.notebook.get_n_pages()):
            self.notebook.remove_page(i)

        self.doc = doc
        self.filename = filename
        for i, rdf in enumerate(rdfs):
            model_root = parser.parse_RDFXML(doc=doc, root_element=rdf)
            metadata_editor = MetadataEditor(model_root, self)
            page = self.notebook.append_page(metadata_editor.widget, tab_label=None)

            # get parentNode twice as rdfs are found under the /object/metadata/rdf path
            actual_node = rdf.parentNode.parentNode
            actual_id = actual_node.getAttribute('id')
            self.node_store.append([metadata_editor, page,
                "{1} ({0})".format(actual_node.localName, actual_id)])
            metadata_editor.widget.show_all()

        # select first item, for _get_active_editor
        self.node_view.get_selection().select_iter(self.node_store.get_iter_first())
        self.update_ui()

    def _on_node_view_selection_changed(self, selection):
        tree_model, tree_iter = selection.get_selected()
        if tree_iter:
            page = tree_model[tree_iter][1]
            self.notebook.set_current_page(page)


    def on_file_open(self, action):
        dialog = Gtk.FileChooserDialog(title="Open File",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                     Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = dialog.run()
        #filename = dialog.get_filename()
        if response == Gtk.ResponseType.OK:
            self.load_file(dialog.get_filename())
        dialog.destroy()

    def on_file_save(self, action):
        f = open(self.filename,"wb")
        self.doc.writexml(f)
        f.close()

    def on_file_save_as(self, action):
        dialog = Gtk.FileChooserDialog(title="Save File",
            parent=self,
            action=Gtk.FileChooserAction.SAVE,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                     Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        response = dialog.run()
        #filename = dialog.get_filename()
        if response == Gtk.ResponseType.OK:
            f = open(dialog.get_filename(),"wb")
            self.doc.writexml(f)
            f.close()
            self.filename = dialog.get_filename()
        dialog.destroy()

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
        dialog = AddPropertyDialog(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            editor = self._get_active_editor()
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

            if dialog.get_blank_node():
                obj.add_predicate_blank(dialog.get_property())
            else:
                obj.add_predicate_literal(dialog.get_property(), dialog.get_value(), None)
        dialog.destroy()
            

    def on_remove_property(self, action):
        editor = self._get_active_editor()
        if editor is None:
            return

        tree_model, tree_iter = editor.tree_view.get_selection().get_selected()
        assert tree_iter is not None

        obj = editor.tree_store[tree_iter][0]
        obj.remove()
        

    def on_quit(self, action):
        self.destroy()

    def do_destroy(self, *args):
        Gtk.main_quit()

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('input_file', nargs='?')
    args = argparser.parse_args()

    win = MainWindow()
    win.show()

    if args.input_file:
        win.load_file(args.input_file)

    Gtk.main()
