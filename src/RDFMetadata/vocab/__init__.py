# vocab - definitions and human-readable names for metadata terms
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Artem Popov <artfwo@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import sys

class Term(object):
	def __init__(self, uri, label=None, desc=None):
		self.uri = uri
		self.label = label
		self.desc = desc

vocabularies = {}

import cc
import dc

for module in [cc, dc]:
	vocabularies[module.NS_URI] = module

#sys.exit(1)
def get_term(ns_uri, localname):
	ns_dic = vocabularies[ns_uri].__dict__
	if localname.has_key(ns_dic) and isinstance(ns_dic[localname], Term):
		return ns_dic[localname]
	else:
		raise LookupError("Wrong type for term %s" % localname)
