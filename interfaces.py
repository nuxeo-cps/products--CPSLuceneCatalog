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
# $Id$
"""CPS Lucene Catalog interface
"""

import zope.interface
import zope.schema

from zope.app.i18n import ZopeMessageFactory as _

from Products.CMFCore.interfaces import ICatalogTool

class ICPSLuceneCatalogTool(ICatalogTool):
    """CPS Lucene catalog Tool
    """

    server_url = zope.schema.TextLine(
        title=_(u"Server URL"),
        description=_(u"XML-RPC server URL"),
        required=True,
        default=u'http://localhost',
        )

    server_port = zope.schema.Int(
        title=_(u"Server port"),
        description=_(u"XML-RPC server port"),
        required=True,
        default=9180,
        )

class IZCatalogQuery(zope.interface.Interface):
    """ZCatalog Query
    """

    def getLuceneQuery():
        """Returns a native lucene query
        """
