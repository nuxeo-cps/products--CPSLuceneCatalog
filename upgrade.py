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
# $Id: exportimport.py 29880 2006-02-07 12:43:09Z janguenot $
"""CPS Lucene Catalog export import
"""

from Products.CMFCore.utils import getToolByName

from Products.CPSLuceneCatalog.catalog import CPSLuceneCatalogTool

#
# Update from CMF Catalog to CPS Lucene Catalog
#

def check_upgrade_340_350_cmf_catalog(context):
    ctool = getToolByName(context, CPSLuceneCatalogTool.id, None)
    upgrade = 0
    if (ctool is None or
        ctool.meta_type != CPSLuceneCatalogTool.meta_type):
        upgrade = 1
    return upgrade


def upgrade_340_350_cmf_catalog(context):
    ctool_id = CPSLuceneCatalogTool.id
    ctool_mt = CPSLuceneCatalogTool.meta_type
    ctool = getToolByName(context, ctool_id, None)
    utool = getToolByName(context, 'portal_url')
    portal = utool.getPortalObject()
    add_it = 0
    if ctool is None:
        add_it = 1
    elif ctool.meta_type != ctool_mt:
        add_it = 1
        portal.manage_delObjects([ctool_id])
    if add_it:
        portal.manage_addProduct['CPSLuceneCatalog'].manage_addTool(ctool_mt)
        log = "CPS Lucene Catalog Tool migration done"
    else:
        log = "CPS Lucene Catalog Tool already installed"
    return log
