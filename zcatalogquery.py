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
            # FIXME : Implement this !
            # We don't necessarly need them all.
            del kw['cps_filter_sets']

        self.fields = ()
        self.options = {}

        # Filter out options
        for k, v in kw.items():

            field_conf = {}

            if k not in cat.getCatalog().getFieldNamesFor():
                # CPS BBB : ZCTitle case.
                if k == 'ZCTitle':
                    if 'Title' in cat.getCatalog().getFieldNamesFor():
                        field_conf = {
                            'id'    : 'Title',
                            'value' : v,
                            }
                        self.fields += (field_conf,)
                else:
                    self.options[k] = v
            else:

                field_conf = {
                    'id'    : k,
                    'value' : v,
                    }

                if isinstance(v, DateTime):
                    field_conf['value'] = v.ISO()

                # Date query ranges
                elif isinstance(v, dict):
                    if 'query' in v.keys() and 'range' in v.keys():
                        v1 = v['query']
                        range_ = 'range:' + v['range']
                        if isinstance(v1, DateTime):
                            field_conf['value'] = v1.ISO()
                            field_conf['usage'] = range_
                        elif isinstance(v1, list) or isinstance(v1, tuple):
                            if len(v1) == 2:
                                d1 = v1[0]
                                d2 = v1[1]
                                if (isinstance(d1, DateTime) and
                                    isinstance(d2, DateTime)):
                                    field_conf['value'] =  [d1.ISO(), d2.ISO()]
                                else:
                                    field_conf['value'] =  [d1, d2]
                        field_conf['usage'] = range_
                self.fields += (field_conf,)

##        logger.debug("getFielsdMap() %s" % str(self.fields))
##        logger.debug("getQueryOptions() %s" % str(self.options))

    def getFieldsMap(self):
        return self.fields

    def getQueryOptions(self):
        return self.options
