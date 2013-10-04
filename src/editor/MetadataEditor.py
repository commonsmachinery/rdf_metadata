# MetadataEditor - Metadata editor widget for GTK
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import sys
from gi.repository import Gtk

from RDFMetadata import model
from RDFMetadata import vocab

def property_name_data_func(column, cell, tree_model, iter, user_data):
    uri = tree_model[iter][0].uri
    if isinstance(uri, model.QName):
        try:
            term = vocab.get_term(uri.ns_uri, uri.local_name)
            prefix = term.qname.ns_prefix
            cell.set_property('text', "{0}:{1}".format(prefix, term.label))
        except LookupError:
            pass

class MetadataEditor(object):
    def __init__(self, root, app):
        self.widget = Gtk.ScrolledWindow(shadow_type = Gtk.ShadowType.IN)

        self.root = root
        self.app = app

        self.root.register_observer(self._model_observer)

        # Tree store columns:
        # 0: model.RDFNode object, 1: property, 2: value, 3: row type
        self.tree_store = Gtk.TreeStore(object, str, str, str)

        self.added_to_tree_store = set()

        self._populate_tree_store(root)

        # Set up display of the tree
        self.tree_view = Gtk.TreeView(self.tree_store)

        render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Property", render, text = 1)
        column.set_sort_column_id(1)
        self.tree_view.append_column(column)
        column.set_cell_data_func(render, property_name_data_func)

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
        
        self.widget.add(self.tree_view)

    # used by app.update_ui()
    def add_enabled(self):
        tree_model, tree_iter = self.tree_view.get_selection().get_selected()
        if tree_iter:
            obj = tree_model[tree_iter][0]
        else:
            obj = None

        return isinstance(obj, model.SubjectNode) or \
               (isinstance(obj, model.Predicate) and \
                isinstance(obj.object, model.BlankNode))

    def remove_enabled(self):
        tree_model, tree_iter = self.tree_view.get_selection().get_selected()
        if tree_iter:
            obj = tree_model[tree_iter][0]
        else:
            obj = None

        return isinstance(obj, model.Predicate) 


    def _populate_tree_store(self, root):
        # Always start with the default resource, if it exists
        res = root.get("")
        if res:
            self._add_resource_to_tree(res)

        # Add the rest
        for res in root.itervalues():
            if res.uri != "":
                self._add_resource_to_tree(res)

    def _add_resource_to_tree(self, res, pos = None):
        if res.uri:
            label = str(res.uri)
        else:
            label = '(default)'

        res_iter = self.tree_store.append(None, [res, label, '', 'Resource'])

        # Add the predicates and their target objects
        for pred in res:
            self._add_predicate_to_tree(pred, res_iter)

        return res_iter
    

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
                (isinstance(o, model.Predicate)
                 and o.object is obj
                 and isinstance(o, model.BlankNode))):
                return i

            if self.tree_store.iter_has_child(i):
                o = self._lookup_tree_object(obj, self.tree_store.iter_children(i))
                if o is not None:
                    return o

            i = self.tree_store.iter_next(i)

        return None


    def _on_tree_selection_changed(self, selection):
        self.app.update_ui()

    def _on_value_edited(self, render, path, text):
        i = self.tree_store.get_iter(path)
        node = self.tree_store[i][0]

        if isinstance(node, model.Predicate):
            obj = node.object
            if isinstance(obj, model.LiteralNode):
                obj.set_value(text)


    def _model_observer(self, event):
        if isinstance(event, model.PredicateAdded):
            tree_iter = self._lookup_tree_object(event.node)
            if tree_iter:
                i = self._add_predicate_to_tree(event.predicate, tree_iter)
                self.tree_view.get_selection().select_iter(i)

        elif isinstance(event, model.PredicateObjectChanged):
            tree_iter = self._lookup_tree_object(event.predicate)
            if tree_iter:
                self._update_predicate(tree_iter, event.predicate)

        elif isinstance(event, model.PredicateRemoved):
            tree_iter = self._lookup_tree_object(event.predicate)
            if tree_iter:
                # TODO: should we check that this row doesn't have
                # subitems?
                self.tree_store.remove(tree_iter)

        elif isinstance(event, model.NodeRemoved):
            tree_iter = self._lookup_tree_object(event.node)
            if tree_iter:
                # TODO: should we check that this row doesn't have
                # subitems?
                self.tree_store.remove(tree_iter)
                
        elif isinstance(event, model.ResourceNodeAdded):
            tree_iter = self._add_resource_to_tree(event.node)

            # Show the new node
            path = self.tree_store.get_path(tree_iter)
            self.tree_view.expand_row(path, True)

        # Blank nodes are added by reference from a predicate


    def _update_predicate(self, tree_iter, predicate):
        if isinstance(predicate.object, model.LiteralNode):
            self.tree_store[tree_iter][2] = predicate.object.value
            self.tree_store[tree_iter][3] = 'Literal'

        elif isinstance(predicate.object, model.ResourceNode):
            self.tree_store[tree_iter][2] = str(predicate.object.uri)
            self.tree_store[tree_iter][3] = 'Resource ref'

        elif isinstance(predicate.object, model.BlankNode):
            node = predicate.object
            if node in self.added_to_tree_store:
                # Only external IDs should be possible to add more than once
                assert node.uri.external

                # Just set a reference
                self.tree_store[tree_iter][2] = str(node.uri)
                self.tree_store[tree_iter][3] = 'k node ref'

            else:
                self.added_to_tree_store.add(node)

                if node.uri.external:
                    uri = str(node.uri)
                else:
                    uri = ''

                self.tree_store[tree_iter][2] = uri
                self.tree_store[tree_iter][3] = 'Blank node'

                # Add the predicates and their target objects
                for node_pred in node:
                    self._add_predicate_to_tree(node_pred, tree_iter)

                # Show the new node
                path = self.tree_store.get_path(tree_iter)
                self.tree_view.expand_row(path, True)
