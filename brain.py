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

import datetime
import logging

from ZODB.loglevels import TRACE

from AccessControl import ClassSecurityInfo
from AccessControl.Role import RoleManager
import Acquisition
from Globals import InitializeClass
from OFS.SimpleItem import Item
from DateTime import DateTime

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

            # CPS and Zope2 doesn't like unicode...
            value = v
            if isinstance(value, unicode):
                value = self._convertUnicodeForCPS(value)

            if isinstance(value, list) or isinstance(value, tuple):
                value = map(self._convertUnicodeForCPS, value)

            if isinstance(value, datetime.datetime):
                # Convert datetime.datetime to DateTime.DateTime for BBB
                ttime = value.timetuple()
                value = DateTime(*ttime[:6])

            logger.log(TRACE, "Add attribute %s to brain with value : %s"
                       % (k, v))
            self.__dict__[k] = value

    def _convertUnicodeForCPS(self, value):
        """Convert Unicode to ISO-8859-15
        """
        try:
            value = str(value)
        except UnicodeEncodeError:
            try:
                value = str(value.encode('ISO-8859-15'))
            except UnicodeEncodeError:
                value = repr(value)
        return value

    def getPath(self):
        return str(self.uid)

    def getRID(self):
        return str(self.uid)

    def getPhysicalPath(self):
        return str(self.uid).split('/')

    def getObject(self, REQUEST=None):
        if getattr(self.aq_base, '_getObject_failed', False):
            return None
        t = Timer('CPSBrain.getObject', level=logging.DEBUG)
        path = self.getPath().split('/')
        if len(path) < 2:
            logger.error("getObject: path too short. __dict__:\n   %s",
                         self.__dict__)
            self._getObject_failed = True
            return None
        parent = self.aq_parent

        try:
            target = parent.restrictedTraverse(path)
        except (KeyError, AttributeError,):
            self._getObject_failed = True
            logger.error("getObject: traversal failed. __dict__:\n   %s",
                         self.__dict__)
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
