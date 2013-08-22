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

class SVGNodeList(object):
    def __init__(self, model_root_list, metadata_editor):
        self.widget = Gtk.Box(
            spacing = 0,
            orientation = Gtk.Orientation.HORIZONTAL)

        self.metadata_editor = metadata_editor

        # Tree store columns:
        # 0: model.Root object
        # 1: Name to be displayed
        # 2: Tooltip string
        self.liststore = Gtk.ListStore(object, str, str)
        i = 0 # Just for differentiating values now. Can be removed one proper name is displayed
        for model_root  in model_root_list:
            i = i + 1
            self.liststore.append([model_root, "SVG Node " + str(i), "tooltip" + str(i)])

        self.treeview = Gtk.TreeView(self.liststore)
        self.treeview.set_tooltip_column(2)

        render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("SVG Nodes", render, text = 1)
        column.set_sort_column_id(1)
        self.treeview.append_column(column)

        self.widget.pack_start(self.treeview, True, True, 0)

        # Connect events
        self.treeview.get_selection().connect(
            'changed', self._on_svg_node_list_changed)


    def _on_svg_node_list_changed(self, selection):
        tree_model, tree_iter = selection.get_selected()
        if tree_iter:
            selected_model_root = tree_model[tree_iter][0]
        else:
            selected_model_root = None

        self.metadata_editor.tree_store.clear()
        self.metadata_editor._populate_tree_store(selected_model_root)
        # self.metadata_editor.root = selected_model_root

class MetadataEditor(object):
    def __init__(self, root):
        self.widget = Gtk.Box(
            spacing = 0,
            orientation = Gtk.Orientation.VERTICAL)

        self.root = root

        self.root.register_observer(self._model_observer)

        #
        # Control toolbar
        #

        self.toolbar = Gtk.Toolbar()
        self.toolbar.set_style(Gtk.ToolbarStyle.BOTH)

        self.expand_all_btn = self._add_toolbtn(
            'Expand all', Gtk.STOCK_ZOOM_IN, True, self._on_expand_all)

        self.collapse_all_btn = self._add_toolbtn(
            'Collapse all', Gtk.STOCK_ZOOM_OUT, True, self._on_collapse_all)

        self.print_xml_btn = self._add_toolbtn(
            'Print XML', None, True, self._on_print_xml)

        self.add_property_btn = self._add_toolbtn(
            'Add property', Gtk.STOCK_ADD, False, self._on_add_property)

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

        self.added_to_tree_store = set()

        self._populate_tree_store(root)

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

        self.tree_view.get_selection().connect(
            'changed', self._on_tree_selection_changed)

        self.widget.pack_start(self.tree_view, True, True, 0)

    def _populate_tree_store(self, root):
        # Always start with the default resource, if it exists
        res = root.get("")
        if res:
            self._add_resource_to_tree(res)

        # Add the rest
        for res in root.itervalues():
            if res.uri != "":
                self._add_resource_to_tree(res)

    def _add_toolbtn(self, label, stock, enabled, action):
        btn = Gtk.ToolButton(stock, label = label, sensitive = enabled)
        btn.connect('clicked', action)
        self.toolbar.insert(btn, -1)
        return btn


    def _add_resource_to_tree(self, res, pos = None):
        if res.uri:
            label = str(res.uri)
        else:
            label = '(default)'

        res_iter = self.tree_store.append(None, [res, label, '', 'Resource'])

        # Add the predicates and their target objects
        for pred in res:
            self._add_predicate_to_tree(pred, res_iter)


    def _add_predicate_to_tree(self, pred, parent):
        if isinstance(pred.object, model.LiteralNode):
            i = self.tree_store.append(
                parent,
                [pred, str(pred.uri), str(pred.object.value), 'Literal'])

        elif isinstance(pred.object, model.ResourceNode):
            i = self.tree_store.append(
                parent,
                [pred, str(pred.uri), str(pred.object.uri), 'Resource ref'])

        elif isinstance(pred.object, model.BlankNode):
            node = pred.object

            if node in self.added_to_tree_store:
                # Only external IDs should be possible to add more than once
                assert node.uri.external

                # Just add reference second time around
                i = self.tree_store.append(
                    parent,
                    [pred, str(pred.uri), str(node.uri), 'Blank node ref'])
            else:
                self.added_to_tree_store.add(node)

                if node.uri.external:
                    uri = str(node.uri)
                else:
                    uri = ''

                i = self.tree_store.append(
                    parent,
                    [pred, str(pred.uri), uri, 'Blank node'])

                # Add the predicates and their target objects
                for node_pred in node:
                    self._add_predicate_to_tree(node_pred, i)

        return i


    def _lookup_tree_object(self, obj, start_iter = None):
        if start_iter is None:
            i = self.tree_store.get_iter_first()
        else:
            i = start_iter

        while i is not None:
            o = self.tree_store[i][0]
            if (o is obj or
                (isinstance(o, model.Predicate) and o.object is obj)):
                return i

            if self.tree_store.iter_has_child(i):
                o = self._lookup_tree_object(obj, self.tree_store.iter_children(i))
                if o is not None:
                    return o

            i = self.tree_store.iter_next(i)

        return None


    def _on_tree_selection_changed(self, selection):
        tree_model, tree_iter = selection.get_selected()
        if tree_iter:
            obj = tree_model[tree_iter][0]
        else:
            obj = None

        self.add_property_btn.set_sensitive(
            isinstance(obj, model.SubjectNode) or
            (isinstance(obj, model.Predicate)
             and isinstance(obj.object, model.BlankNode))
            )


    def _on_expand_all(self, btn):
        self.tree_view.expand_all()


    def _on_collapse_all(self, btn):
        self.tree_view.collapse_all()


    def _on_print_xml(self, btn):
        self.root.repr.element.writexml(sys.stdout)


    def _on_add_property(self, btn):
        tree_model, tree_iter = self.tree_view.get_selection().get_selected()
        assert tree_iter is not None

        obj = self.tree_store[tree_iter][0]

        if isinstance(obj, model.SubjectNode):
            pass
        elif (isinstance(obj, model.Predicate)
              and isinstance(obj.object, model.SubjectNode)):
            obj = obj.object
        else:
            assert False, 'attempting to add property to a non-SubjectNode'

        # Make sure the row is expanded
        path = self.tree_store.get_path(tree_iter)
        self.tree_view.expand_row(path, False)

        obj.add_literal_node(
            model.QName('http://test/', 'test', 'Test'),
            'new value', 'http://test/type')


    def _on_value_edited(self, render, path, text):
        i = self.tree_store.get_iter(path)
        node = self.tree_store[i][0]

        if isinstance(node, model.Predicate):
            obj = node.object
            if isinstance(obj, model.LiteralNode):
                obj.set_value(text)

                # TODO: this should be changed on callbacks from the domrepr layer
                self.tree_store[i][2] = text


    def _model_observer(self, event):
        if isinstance(event, model.AddPredicate):
            tree_iter = self._lookup_tree_object(event.node)
            i = self._add_predicate_to_tree(event.predicate, tree_iter)
            self.tree_view.get_selection().select_iter(i)
