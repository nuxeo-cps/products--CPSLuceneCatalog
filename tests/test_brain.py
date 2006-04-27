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
# $Id: test_cpslucenecatalog.py 44415 2006-04-12 15:18:17Z atchertchian $
"""CPS Brain test
"""

import unittest
import datetime
import DateTime

from Products.CPSLuceneCatalog.brain import CPSBrain

class CPSBrainTestCase(unittest.TestCase):

    # Tests for CPSBrain

    def test_date(self):

        cdate = datetime.datetime.now()

        mapping = {
            'date' : cdate,
            }

        bra = CPSBrain(mapping)

        expected = DateTime.DateTime(*cdate.timetuple()[:6])

        self.assertEqual(bra.date, expected)

    def test_unicode(self):

        v = u'Nuxéo rulez'

        mapping = {
            'v' : v
            }

        bra = CPSBrain(mapping)

        self.assert_(not isinstance(bra.v, unicode))

    def test_list(self):

        v = [u'a', u'b']

        mapping = {
            'v' : v
            }

        bra = CPSBrain(mapping)

        for v in bra.v:
            self.assert_(not isinstance(v, unicode))

        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CPSBrainTestCase))
    return suite
