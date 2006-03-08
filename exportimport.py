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

import zope.component

from Products.GenericSetup.utils import importObjects
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import ObjectManagerHelpers
from Products.GenericSetup.utils import PropertyManagerHelpers
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron

from Products.CMFCore.utils import getToolByName

from Products.CPSLuceneCatalog.catalog import CPSLuceneCatalogTool
from Products.CPSLuceneCatalog.interfaces import ICPSLuceneCatalogTool

TOOL = 'portal_catalog'
NAME = 'lucenecatalog'

def exportCPSLuceneCatalog(context):

    site = context.getSite()
    tool = getToolByName(site, TOOL, None)
    if tool is None:
        logger = context.getLogger(NAME)
        logger.info("Nothing to export.")
        return
    try:
        exportObjects(tool, '', context)
    except:
        # XXX  : BadRequest.
        # What the fuck ? 
        pass

def importCPSLuceneCatalog(context):

    site = context.getSite()
    tool = getToolByName(site, TOOL, None)

    # XXX current limitation of the GenericSetup using Extension profiles.
    if tool is None or tool.meta_type != 'CPS Lucene Catalog Tool':
        # XXX Probably a migration is needed here
        if tool is not None:
            site.manage_delObjects(['portal_catalog'])
        site._setObject(TOOL, CPSLuceneCatalogTool())

    tool = getToolByName(site, TOOL)
    importObjects(tool, '', context)

class LuceneCatalogToolXMLAdapter(XMLAdapterBase, ObjectManagerHelpers,
                                  PropertyManagerHelpers):
    """XML importer and exporter for the CPS Lucene Catalog
    """

    zope.component.adapts(ICPSLuceneCatalogTool, ISetupEnviron)
    zope.interface.implements(IBody)
     
    _LOGGER_ID = NAME
    name = NAME

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())
        node.appendChild(self._extractObjects())
        # XXX here specifics.
        self._logger.info("CPS Lucene Catalog Tool has been exported.")
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """

        self.context._p_changed = 1

        if self.environ.shouldPurge():
            self._purgeProperties()
            self._purgeObjects()
            # XXX purge specifics.

        self._initProperties(node)
        self._initObjects(node)
        self._importColumns(node)
        self._importFields(node)

        self._logger.info("CPS Lucene Catalog tool has been imported.")

    def _importColumns(self, node):
        """Import the columns names
        """
        for child in node.childNodes:
            if child.nodeName == 'column':
                cvalue = str(child.getAttribute('value'))
                self.context.addColumn(cvalue)
                self._logger.info("Add a column with value %s" % cvalue)
    
    def _importFields(self, node):
        """Import the Fields.
        """
        for child in node.childNodes:
            if child.nodeName == 'field':
                # XXX Deal with deftault values.
                name = str(child.getAttribute('name'))
                attr = str(child.getAttribute('attr'))
                type = str(child.getAttribute('type'))
                analyzer = str(child.getAttribute('analyzer'))
                index = str(child.getAttribute('index'))
                store = str(child.getAttribute('store'))
                vector = str(child.getAttribute('vector'))
                self.context.addField(
                    name, attr, type, analyzer, index, store, vector)
                self._logger.info("Add field %s" % name)
