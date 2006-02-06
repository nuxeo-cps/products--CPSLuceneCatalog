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
"""CPS Lucene Catalog tests
"""

import unittest
import CPSLuceneCatalogTestCase

from Products.CMFCore.utils import getToolByName

from nuxeo.lucene.interfaces import ILuceneCatalog
from Products.CPSLuceneCatalog.catalog import CPSLuceneCatalogTool

class LuceneCatalogTestCase(CPSLuceneCatalogTestCase.CPSLuceneCatalogTestCase):

    def afterSetup(self):
        from Products.CPSCore.tests.setup import fullFiveSetup
        fullFiveSetup()
        CPSLuceneCatalogTestCase.CPSLuceneCatalogTestCase.afterSetup(self)

    def test_implementation(self):
        from zope.interface.verify import verifyClass
        from Products.CMFCore.interfaces import ICatalogTool
        self.assert_(verifyClass(ICatalogTool, CPSLuceneCatalogTool))

    def test_fixture(self):
        cpscatalog = getToolByName(self.portal, 'portal_catalog')
        self.assert_(cpscatalog)
        self.assertEqual(cpscatalog.meta_type, 'CPS Lucene Catalog Tool')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LuceneCatalogTestCase))
    return suite

