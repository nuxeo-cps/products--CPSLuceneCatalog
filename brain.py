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
"""

import zope.interface
from interfaces import ICPSBrain

class CPSBrain(dict):
    """Simple light brain
    """

    zope.interface.implements(ICPSBrain)

    def __init__(self, dict):
        for k, v in dict.items():
            self[k] = v

    # XXX implements the whole ZCatalog brains interface for BBB
