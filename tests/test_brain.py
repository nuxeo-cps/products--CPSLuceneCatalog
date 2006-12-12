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

    def test_empty_string(self):
        mapping = {'v': ''}
        bra = CPSBrain(mapping)
        self.assertEquals(bra.v, '')

    def test_getObject(self):
        class FakeParent:
            def restrictedTraverse(self, path):
                if path == ['correct', 'path']:
                    return 'Some object'
                elif path == ['key', 'error']:
                    raise KeyError(path)
                else:
                    raise AttributeError(path)

        def new_brain(uid):
            bra = CPSBrain({'uid' : uid})
            bra.aq_base = bra
            bra.aq_parent = FakeParent()
            return bra

        # invalid paths
        bra = new_brain('too_short_path')
        self.assertEquals(bra.getObject(), None)
        self.assert_(getattr(bra, '_getObject_failed', None))

        bra = new_brain('')
        self.assertEquals(bra.getObject(), None)
        self.assert_(getattr(bra, '_getObject_failed', None))

        # if the brain remembers getObject failed, it won't get called again
        bra = new_brain('correct/path')
        bra._getObject_failed = True
        self.assertEquals(bra.getObject(), None)

        # succeeding call
        delattr(bra, '_getObject_failed')
        self.assertEquals(bra.getObject(), 'Some object')

        # wrong call resulting in KeyError
        bra = new_brain('key/error')
        self.assertEquals(bra.getObject(), None)
        self.assert_(getattr(bra, '_getObject_failed', None))

        # wrong call resulting in AttributeError
        bra = new_brain('other/error')
        self.assertEquals(bra.getObject(), None)
        self.assert_(getattr(bra, '_getObject_failed', None))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CPSBrainTestCase))
    return suite
