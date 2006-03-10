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
# $Id: catalog.py 31175 2006-03-10 14:57:43Z janguenot $
"""Patching CPSInstaller.CMFInstaller.

BBB for CPS 3.4.0
"""

import logging

from Products.CPSInstaller.CMFInstaller import CMFInstaller

def reindexCatalog(self):
    pass

CMFInstaller.reindexCatalog = reindexCatalog

def addZCTextIndexLexicon(self, id, title=''):
    pass

CMFInstaller.addZCTextIndexLexicon = addZCTextIndexLexicon

def addPortalCatalogIndex(self, id, type, extra=None, destructive=False):
    pass

CMFInstaller.addPortalCatalogIndex = addPortalCatalogIndex
    
def addPortalCatalogMetadata(self, id, default_value=None):
    pass

CMFInstaller.addPortalCatalogMetadata = addPortalCatalogIndex

def flagCatalogForReindex(self, indexid=None):
    pass

CMFInstaller.flagCatalogForReindex = flagCatalogForReindex


def flagCatalogForReindexMetadata(self, metadataid=None):
    pass

CMFInstaller.flagCatalogForReindexMetadata = flagCatalogForReindexMetadata

logger = logging.getLogger('CPSLuceneCatalog')
logger.info('Patching CPSInstaller.CMFInstaller for BBB for CPS <= 3.4.0')
