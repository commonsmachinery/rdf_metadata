# vocab - definitions and human-readable names for metadata terms
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Artem Popov <artfwo@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.
import sys
from . import Term

NS_URI = "http://creativecommons.org/ns#"
terms = {}

Work = Term(
    uri=NS_URI + "Work",
    label="Work",
    desc="a potentially copyrightable work"
)

License = Term(
    uri=NS_URI + "License",
    label="License",
    desc="a set of requests/permissions to users of a Work, e.g. a copyright license, the public domain, information for distributors"
)

Jurisdiction = Term(
    uri=NS_URI + "Jurisdiction",
    label="Jurisdiction",
    desc="the legal jurisdiction of a license"
)

Permission = Term(
    uri=NS_URI + "Permission",
    label="Permission",
    desc="an action that may or may not be allowed or desired"
)

Requirement = Term(
    uri=NS_URI + "Requirement",
    label="Requirement",
    desc="an action that may or may not be requested of you"
)

Prohibition = Term(
    uri=NS_URI + "Prohibition",
    label="Prohibition",
    desc="something you may be asked not to do"
)

Reproduction = Term(
    uri=NS_URI + "Reproduction",
    label="Reproduction",
    desc="making multiple copies"
)

Distribution = Term(
    uri=NS_URI + "Distribution",
    label="Distribution",
    desc="distribution, public display, and publicly performance"
)

DerivativeWorks = Term(
    uri=NS_URI + "DerivativeWorks",
    label="Derivative Works",
    desc="distribution of derivative works"
)

Sharing = Term(
    uri=NS_URI + "Sharing",
    label="Sharing",
    desc="permits commercial derivatives, but only non-commercial distribution"
)

Notice = Term(
    uri=NS_URI + "Notice",
    label="Notice",
    desc="copyright and license notices be kept intact"
)

Attribution = Term(
    uri=NS_URI + "Attribution",
    label="Attribution",
    desc="credit be given to copyright holder and/or author"
)

ShareAlike = Term(
    uri=NS_URI + "ShareAlike",
    label="Share Alike",
    desc="derivative works be licensed under the same terms or compatible terms as the original work"
)

SourceCode = Term(
    uri=NS_URI + "SourceCode",
    label="Source Code",
    desc="source code (the preferred form for making modifications) must be provided when exercising some rights granted by the license."
)

Copyleft = Term(
    uri=NS_URI + "Copyleft",
    label="Copyleft",
    desc="derivative and combined works must be licensed under specified terms, similar to those on the original work"
)

LesserCopyleft = Term(
    uri=NS_URI + "LesserCopyleft",
    label="Lesser Copyleft",
    desc="derivative works must be licensed under specified terms, with at least the same conditions as the original work; combinations with the work may be licensed under different terms"
)

CommercialUse = Term(
    uri=NS_URI + "CommercialUse",
    label="Commercial Use",
    desc="exercising rights for commercial purposes"
)

HighIncomeNationUse = Term(
    uri=NS_URI + "HighIncomeNationUse",
    label="High Income Nation Use",
    desc="use in a non-developing country"
)

permits = Term(
    uri=NS_URI + "permits",
    label="permits",
    desc=""
)

requires = Term(
    uri=NS_URI + "requires",
    label="requires",
    desc=""
)

prohibits = Term(
    uri=NS_URI + "prohibits",
    label="prohibits",
    desc=""
)

jurisdiction = Term(
    uri=NS_URI + "jurisdiction",
    label="jurisdiction",
    desc=""
)

deprecatedOn = Term(
    uri=NS_URI + "deprecatedOn",
    label="deprecated on",
    desc=""
)

license = Term(
    uri=NS_URI + "license",
    label="has license",
    desc=""
)

attributionURL = Term(
    uri=NS_URI + "attributionURL",
    label="Attribution URL",
    desc=""
)

attributionName = Term(
    uri=NS_URI + "attributionName",
    label="Attribution Name",
    desc=""
)
