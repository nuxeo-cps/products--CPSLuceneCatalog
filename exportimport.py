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
"""CPS Lucene Catalog export import
"""

from Products.GenericSetup.utils import importObjects
from Products.GenericSetup.utils import exportObjects

from Products.CMFCore.utils import getToolByName

from Products.CPSLuceneCatalog.catalog import CPSLuceneCatalogTool

TOOL = 'portal_catalog'
NAME = 'CPS Lucene Catalog'

def exportCPSLuceneCatalog(context):

    site = context.getSite()
    tool = getToolByName(site, TOOL, None)
    if tool is None:
        logger = context.getLogger(NAME)
        logger.info("Nothing to export.")
        return
    exportObjects(tool, '', context)

def importCPSLuceneCatalog(context):

    site = context.getSite()
    tool = getToolByName(site, TOOL, None)

    # XXX Why do I need to do this here ? 
    if tool is None or tool.meta_type != 'CPS Lucene Catalog Tool':
        # XXX Probably a migration is needed here
        if tool is not None:
            site.manage_delObjects(['portal_catalog'])
        site._setObject(TOOL, CPSLuceneCatalogTool())

    tool = getToolByName(site, TOOL)
    importObjects(tool, '', context)
