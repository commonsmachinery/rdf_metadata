rdf_metadata
============

Code for manipulating metadata in RDF/XML format. Right now
experimental, might turn into a proper editor later.


Background (or, why not use Redland?)
-------------------------------------

The purpose of this library was originally to prototype how to
implement an RDF graph with a backing DOM, where all changes to the
graph should update the DOM, and changes to the DOM trigger updates in
the graph.  The eventual target implementation was a library that
could fit in Inkscape, which maintain such a link between the DOM and
the visual presentation at all times.

A secondary purpose is to be as non-destructive as possible when
updating the graph, to improve interoperability with other metadata
implementations (e.g. Inkscape currently has a very fixed idea about
what the XML must look like to "parse" the RDF metadata).

This is different from most other RDF libraries, which parse the
RDF/XML into a graph, and later can re-serialise back to RDF/XML.


License
-------

Copyright 2013 Commons Machinery http://commonsmachinery.se/

Distributed under an GPLv2 license, please see LICENSE in the top dir.

Contact: Peter Liljenberg <peter@commonsmachinery.se>

