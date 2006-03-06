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

#
# Update from CMF Catalog to CPS Lucene Catalog
#

def check_upgrade_340_350_cmf_catalog(portal):
    cat = getToolByName(portal, 'portal_catalog', None)
    return cat.meta_type == 'CPS Lucene Catalog Tool'

def upgrade_340_350_cmf_catalog(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    # XXX
    return "CPS Lucene Catalog migration done"
