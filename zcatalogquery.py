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

from DateTime.DateTime import DateTime

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
            value = v
            if k not in cat.getCatalog().getFieldNamesFor():
                # ZCTitle case.
                if k == 'ZCTitle':
                    self.fields['Title'] = value
                else:
                    self.options[k] = value
            else:
                if isinstance(value, DateTime):
                    value = value.ISO()

                # Hack for the range quey
                elif isinstance(value, dict):
                    if 'query' in value.keys() and 'range' in value.keys():
                        v1 = value['query']
                        range_ = value['range']
                        if isinstance(v1, DateTime):
                            self.fields[k] = v1.ISO()
                            self.options[k+'_usage'] = 'range' + ':' + range_
                        else:
                            pass
                else:
                    self.fields[k] = value 
                    
        logger.debug("getFielsdMap() %s" % str(self.fields))
        logger.debug("getQueryOptions() %s" % str(self.options))

    def getFieldsMap(self):
        return self.fields

    def getQueryOptions(self):
        return self.options
