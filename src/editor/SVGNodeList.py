# MetadataEditor - Metadata editor widget for GTK
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

from gi.repository import Gtk
from . MetadataEditor import MetadataEditor

class SVGNodeList(object):
    def __init__(self, model_root_list, main_pane, app):
        self.widget = Gtk.Box(
            spacing = 0,
            orientation = Gtk.Orientation.HORIZONTAL)

        self.paned = main_pane
        self.app = app
        self.metadata_editor_list = []

        # Liststore columns:
        # 0: MetadataEditor object
        # 1: Name to be displayed
        # 2: Tooltip string
        self.liststore = Gtk.ListStore(object, str, str)

        i = 0 # Just for differentiating values now. Can be removed one proper name is displayed
        for model_root in model_root_list:
            i = i + 1
            metadata_editor = MetadataEditor(model_root, app)
            self.liststore.append([metadata_editor, "SVG Node " + str(i), "tooltip" + str(i)])
            self.metadata_editor_list.append(metadata_editor)

        self.treeview = Gtk.TreeView(self.liststore)
        self.treeview.set_tooltip_column(2)

        render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("SVG Nodes", render, text = 1)
        column.set_sort_column_id(1)
        self.treeview.append_column(column)

        sw = Gtk.ScrolledWindow()
        sw.add(self.treeview)
        sw.set_shadow_type(Gtk.ShadowType.IN)

        self.widget.pack_start(sw, True, True, 0)

        # Populate the main paned window
        self.paned.add1(self.widget)

        # Connect events
        self.treeview.get_selection().connect(
            'changed', self._on_svg_node_list_changed)


    def _on_svg_node_list_changed(self, selection):
        tree_model, tree_iter = selection.get_selected()
        if tree_iter:
            selected_metadata_editor = tree_model[tree_iter][0]
        else:
            selected_metadata_editor = None

        if self.paned.get_child2() != None:
            self.paned.remove(self.paned.get_child2())

        for metadata_editor in self.metadata_editor_list:
            if metadata_editor == selected_metadata_editor:
                self.paned.add2(metadata_editor.widget)
                self.paned.show_all()
