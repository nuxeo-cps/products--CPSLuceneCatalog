# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: Julien Anguenot <ja@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id: interfaces.py 29338 2006-01-24 14:13:39Z janguenot $
"""ZCatalog query
"""

import logging

import zope.interface
from interfaces import IZCatalogQuery

logger = logging.getLogger("CPSLuceneCatalog.zcatalogquery")

class ZCatalogQuery(object):

    zope.interface.implements(IZCatalogQuery)

    def __init__(self, cat, REQUEST, **kw):

        self.REQUEST = REQUEST

        if 'cps_filter_sets' in kw.keys():
            self.cps_filter_sets = kw['cps_filter_sets']
            del kw['cps_filter_sets']

        self.fields = {}
        self.options = {}

        # Filter out options
        for k, v in kw.items():
            if k not in cat._catalog.getFieldNamesFor():
                self.options[k] = v
            else:
                self.fields[k] = v

        logger.debug("getFielsdMap() %s" % str(self.fields))
        logger.debug("getQueryOptions() %s" % str(self.options))

    def getFieldsMap(self):
        return self.fields

    def getQueryOptions(self):
        return self.options
