# gtk_editor_widget - Metadata editor widget for GTK
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import sys
from gi.repository import Gtk

from . import model


class MetadataEditor(object):
    def __init__(self, root):
        self.widget = Gtk.Box(
            spacing = 0,
            orientation = Gtk.Orientation.VERTICAL)

        self.root = root

        #
        # Control toolbar
        #
        
        self.toolbar = Gtk.Toolbar()
        self.toolbar.set_style(Gtk.ToolbarStyle.BOTH)

#         self.add_property_toolbtn = Gtk.ToolButton(
#             Gtk.STOCK_ADD, label = 'Add property')
#         self.add_property_toolbtn.connect('clicked', self._on_add_clicked)
#         self.toolbar.insert(self.add_property_toolbtn, -1)
# 
        self.print_xml_toolbtn = Gtk.ToolButton(
            None, label = 'Print XML')
        self.print_xml_toolbtn.connect('clicked', self._on_print_xml_clicked)
        self.toolbar.insert(self.print_xml_toolbtn, -1)

        self.widget.pack_start(self.toolbar, False, False, 0)

        #
        # The tree view is the main part of the GUI
        #

        # Tree store columns:
        # 0: model.RDFNode object
        # 1: property
        # 2: value
        # 3: row type
        self.tree_store = Gtk.TreeStore(object, str, str, str)

        # Always start with the default resource, if it exists
        res = root.get("")
        if res:
            self._add_resource_to_tree(res)

        # Add the rest
        for res in root.itervalues():
            if res.uri != "":
                self._add_resource_to_tree(res)


        # Set up display of the tree
        self.tree_view = Gtk.TreeView(self.tree_store)

        render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Property", render, text = 1)
        column.set_sort_column_id(1)
        self.tree_view.append_column(column)

        render = Gtk.CellRendererText(editable = True)
        render.connect('edited', self._on_value_edited)
        column = Gtk.TreeViewColumn("Value", render, text = 2)
        self.tree_view.append_column(column)

        render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Type", render, text = 3)
        self.tree_view.append_column(column)

        self.tree_view.expand_all()
        
        self.widget.pack_start(self.tree_view, True, True, 0)


    def _add_resource_to_tree(self, res):
        if res.uri:
            label = res.uri
        else:
            label = '(default)'

        res_iter = self.tree_store.append(None, [res, label, '', 'Resource'])

        # Add the predicates and their target objects
        for pred in res:
            if isinstance(pred.object, model.LiteralNode):
                i = self.tree_store.append(
                    res_iter,
                    [pred, pred.uri, pred.object.value, 'Literal'])

            elif isinstance(pred.object, model.ResourceNode):
                i = self.tree_store.append(
                    res_iter,
                    [pred, pred.uri, pred.object.uri, 'Resource ref'])
        
    def _on_add_clicked(self, btn):
        pass

        
    def _on_print_xml_clicked(self, btn):
        self.root.element.writexml(sys.stdout)


    def _on_value_edited(self, render, path, text):
        i = self.tree_store.get_iter(path)
        obj = self.tree_store[i][0]

        if isinstance(obj, model.Predicate):
            obj.set_value(text)

        # TODO: this should be changed on callbacks from the domrepr layer
        self.tree_store[i][2] = text

