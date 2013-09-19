# vocab - definitions and human-readable names for metadata terms
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Artem Popov <artfwo@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import sys
from . import Term

NS_URI = "http://purl.org/dc/elements/1.1/"

contributor = Term(
    uri=NS_URI + "contributor",
    label="Contributor",
    desc="An entity responsible for making contributions to the resource."
)

coverage = Term(
    uri=NS_URI + "coverage",
    label="Coverage",
    desc="The spatial or temporal topic of the resource, the spatial applicability of the resource, or the jurisdiction under which the resource is relevant."
)

creator = Term(
    uri=NS_URI + "creator",
    label="Creator",
    desc="An entity primarily responsible for making the resource."
)

date = Term(
    uri=NS_URI + "date",
    label="Date",
    desc="A point or period of time associated with an event in the lifecycle of the resource."
)

description = Term(
    uri=NS_URI + "description",
    label="Description",
    desc="An account of the resource."
)

format = Term(
    uri=NS_URI + "format",
    label="Format",
    desc="The file format, physical medium, or dimensions of the resource."
)

identifier = Term(
    uri=NS_URI + "identifier",
    label="Identifier",
    desc="An unambiguous reference to the resource within a given context."
)

language = Term(
    uri=NS_URI + "language",
    label="Language",
    desc="A language of the resource."
)

publisher = Term(
    uri=NS_URI + "publisher",
    label="Publisher",
    desc="An entity responsible for making the resource available."
)

relation = Term(
    uri=NS_URI + "relation",
    label="Relation",
    desc="A related resource."
)

rights = Term(
    uri=NS_URI + "rights",
    label="Rights",
    desc="Information about rights held in and over the resource."
)

source = Term(
    uri=NS_URI + "source",
    label="Source",
    desc="A related resource from which the described resource is derived."
)

subject = Term(
    uri=NS_URI + "subject",
    label="Subject",
    desc="The topic of the resource."
)

title = Term(
    uri=NS_URI + "title",
    label="Title",
    desc="A name given to the resource."
)

type = Term(
    uri=NS_URI + "type",
    label="Type",
    desc="The nature or genre of the resource."
)
