# MetadataEditor - Metadata editor widget for GTK
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Artem Popov <artfwo@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

from gi.repository import Gtk
from RDFMetadata import model
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
        table.attach(self.property_combo, 1, 2, 1, 2)

        self.ns_combo = Gtk.ComboBox(model=ns_store)
        cell = Gtk.CellRendererText()
        self.ns_combo.pack_start(cell, True)
        self.ns_combo.add_attribute(cell, 'text', 1)
        table.attach(self.ns_combo, 1, 2, 0, 1)

        self.value_entry = Gtk.Entry()
        table.attach(self.value_entry, 1, 2, 2, 3, yoptions=Gtk.AttachOptions.EXPAND)                

        expander = Gtk.Expander(label="Advanced", spacing=12)
        table.attach(expander, 0, 2, 3, 4)                        

        adv_vbox = Gtk.VBox(spacing=12) 
        expander.add(adv_vbox)
        
        adv_vbox.add(Gtk.Label(label="Property Namespace:", xalign=0))
        self.property_ns_entry = Gtk.Entry()
        adv_vbox.add(self.property_ns_entry)
        
        adv_vbox.add(Gtk.Label(label="Property Name:", xalign=0))
        self.property_name_entry = Gtk.Entry()
        adv_vbox.add(self.property_name_entry)

        self.blank_checkbox = Gtk.CheckButton("Blank Node")
        adv_vbox.add(self.blank_checkbox)
        
        self.ns_combo.connect("changed", self.on_ns_combo_changed)
        self.property_combo.connect("changed", self.on_property_combo_changed)
        self.blank_checkbox.connect("toggled", self.on_blank_node_toggled)
        self.ns_combo.set_active(0)
        
        table.show_all()

    def get_ns(self):
        return self.ns_combo.get_model()[self.ns_combo.get_active_iter()][0]

    def get_property(self):
        ns_prefix = vocab.vocabularies[self.property_ns_entry.get_text()].NS_PREFIX
        return model.QName(self.property_ns_entry.get_text(), ns_prefix, self.property_name_entry.get_text())
        #return self.property_ns_entry.get_text()

    def get_value(self):
        return self.value_entry.get_text()

    def get_blank_node(self):
        return self.blank_checkbox.get_active()

    def on_ns_combo_changed(self, combo):
        self.property_store.clear()
        ns = combo.get_model()[combo.get_active_iter()][0]
        terms = vocab.get_terms(ns)
        for term in terms:
            self.property_store.append([term, term.label])
        self.property_combo.set_active(0)

    def on_property_combo_changed(self, combo):
        if combo.get_model() and combo.get_active_iter():
            ns_uri = combo.get_model()[combo.get_active_iter()][0].qname.ns_uri
            self.property_ns_entry.set_text(ns_uri)

            property_name = combo.get_model()[combo.get_active_iter()][0].qname.local_name
            self.property_name_entry.set_text(property_name)

    def on_blank_node_toggled(self, button):
        self.value_entry.set_sensitive(not button.get_active())