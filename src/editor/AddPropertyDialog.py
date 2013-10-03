# MetadataEditor - Metadata editor widget for GTK
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Artem Popov <artfwo@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

from gi.repository import Gtk
from RDFMetadata import vocab

class AddPropertyDialog(Gtk.Dialog):
    __gtype_name__ = 'AddPropertyDialog'

    def __init__(self, parent):
        super(AddPropertyDialog, self).__init__(title='Add Property', parent=parent,
            flags=Gtk.DialogFlags.MODAL,
            buttons=(Gtk.STOCK_ADD, Gtk.ResponseType.OK,
                     Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

        table = Gtk.Table(row_spacing=12, column_spacing=12, border_width=12)
        self.get_content_area().add(table)

        table.attach(Gtk.Label(label="Namespace:", xalign=0), 0, 1, 0, 1)
        table.attach(Gtk.Label(label="Property:", xalign=0), 0, 1, 1, 2)
        table.attach(Gtk.Label(label="Value:", xalign=0), 0, 1, 2, 3)

        ns_store = Gtk.ListStore(str, str)
        ns_store.append(['common_terms', 'Common Terms'])
        ns_store.append([vocab.dc.NS_URI, 'Dublin Core'])
        ns_store.append([vocab.cc.NS_URI, 'Creative Commons'])

        self.property_store = Gtk.ListStore(object, str)

        self.property_combo = Gtk.ComboBox(model=self.property_store)
        cell = Gtk.CellRendererText()
        self.property_combo.pack_start(cell, True)
        self.property_combo.add_attribute(cell, 'text', 1)
        #self.property_combo.connect("changed", self.on_property_combo_changed)
        #self.property_combo.set_active(0)
        table.attach(self.property_combo, 1, 2, 1, 2)

        self.ns_combo = Gtk.ComboBox(model=ns_store)
        cell = Gtk.CellRendererText()
        self.ns_combo.pack_start(cell, True)
        self.ns_combo.add_attribute(cell, 'text', 1)
        self.ns_combo.connect("changed", self.on_ns_combo_changed)
        self.ns_combo.set_active(0)
        table.attach(self.ns_combo, 1, 2, 0, 1)

        self.value_entry = Gtk.Entry()
        table.attach(self.value_entry, 1, 2, 2, 3, yoptions=Gtk.AttachOptions.EXPAND)                

        table.show_all()

    def get_ns(self):
        return self.ns_combo.get_model()[self.ns_combo.get_active_iter()][0]

    def get_property(self):
        return self.property_combo.get_model()[self.property_combo.get_active_iter()][0]

    def get_value(self):
        return self.value_entry.get_text()

    def on_ns_combo_changed(self, combo):
        self.property_store.clear()
        ns = combo.get_model()[combo.get_active_iter()][0]
        terms = vocab.get_terms(ns)
        for term in terms:
            self.property_store.append([term, term.label])
        self.property_combo.set_active(0)