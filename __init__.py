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
"""CPS Lucene Catalog
"""

import BBB.PatchCPSInstallerCMFInstaller

from Products.GenericSetup import profile_registry
from Products.GenericSetup import EXTENSION

from Products.CMFCore.utils import ToolInit
from Products.CMFCore.DirectoryView import registerDirectory

from Products.CPSCore.interfaces import ICPSSite

import brain

registerDirectory('skins', globals())

def initialize(registrar):

    import catalog

    ToolInit(
        meta_type="CPS Lucene Catalog Tool",
        tools=(catalog.CPSLuceneCatalogTool,),
        icon="tool.png",
        ).initialize(registrar)

    try:
        profile_registry.registerProfile(
            'default',
            'CPS Lucene Catalog',
            "Lucene based catalog for CPS",
            'profiles/default',
            'CPSLuceneCatalog',
            EXTENSION,
            for_=ICPSSite)
    except KeyError:
        # Allow the use of refresh
        # Already registred
        pass
