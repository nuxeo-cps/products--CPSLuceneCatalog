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
# $Id: catalog.py 30034 2006-02-10 15:19:53Z janguenot $
"""CPS Brain

Provides a Zope BBB brain tyxpe.
"""

import logging

from AccessControl import ClassSecurityInfo
from AccessControl.Role import RoleManager
import Acquisition
from Globals import InitializeClass
from OFS.SimpleItem import Item

import zope.interface
from interfaces import ICPSBrain

from Products.CPSUtil.timer import Timer

logger = logging.getLogger("CPSBrain")

class CPSBrain(Item, Acquisition.Explicit):
    """Simple light brain.

    Provides a Zope BBB brain type.
    """

    zope.interface.implements(ICPSBrain)

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    def __init__(self, mapping):
        for k, v in mapping.items():
            self.__dict__[k] = v

    def getPath(self):
        return str(self.uid)

    def getRID(self):
        return str(self.uid)

    def getPhysicalPath(self):
        return str(self.uid).split('/')

    def getObject(self, REQUEST=None):
        t = Timer('CPSBrain.getObject', level=logging.DEBUG)
        path = self.getPath().split('/')
        if not path:
            return None
        parent = self.aq_parent
        if len(path) > 1:
            try:
                target = parent.restrictedTraverse(path)
            except (KeyError, AttributeError,):
                return None
        t.mark('found !')
#        t.log()
        return target

    def __getitem__(self, key):
        return getattr(self, key, None)

    def getURL(self, relative=0):
        return self.getPath()

    def has_key(self, key):
        return getattr(self, key, None) is not None
    
InitializeClass(CPSBrain)
