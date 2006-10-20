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

To run this test, you'll need to
  - have a real, **DEDICATED** NXLucene server responding at the url
    specified in default profile (running the test will wipe the store !)
  - uncomment a line in test_suite()
"""

import unittest
import time

import transaction

import CPSLuceneCatalogTestCase

from Products.CMFCore.utils import getToolByName

from nuxeo.lucene.interfaces import ILuceneCatalog
from Products.CPSLuceneCatalog.catalog import CPSLuceneCatalogTool

class CPSLuceneCatalogTest(
    CPSLuceneCatalogTestCase.CPSLuceneCatalogTestCase):

    def afterSetup(self):
        from Products.CPSCore.tests.setup import fullFiveSetup
        fullFiveSetup()
        CPSLuceneCatalogTestCase.CPSLuceneCatalogTestCase.afterSetup(self)

    def beforeTearDown(self):
        cpscatalog = getToolByName(self.portal, 'portal_catalog')
        cpscatalog.manage_clean()
        self.logout()

    def test_implementation(self):
        from zope.interface.verify import verifyClass
        from Products.CMFCore.interfaces import ICatalogTool
        self.assert_(verifyClass(ICatalogTool, CPSLuceneCatalogTool))

    def test_fixture(self):

        # Test the CPS catalog tool fixtures
        cpscatalog = getToolByName(self.portal, 'portal_catalog')
        self.assertEqual(cpscatalog.meta_type, 'CPS Lucene Catalog Tool')

        # Test the zope3 catalog fixtures
        # This will be a registred local utility in the future.
        catalog = cpscatalog.getCatalog()
        from zope.interface.verify import verifyObject
        self.assert_(verifyObject(ILuceneCatalog, catalog))

        # Security indexes
        from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
        self.assertEqual(CMFCatalogAware._cmf_security_indexes,
                         ('allowedRolesAndUsers', 'localUsersWithRoles'))

    def test_indexObject(self):

        self.login('manager')

        transaction.begin()

        cpscatalog = getToolByName(self.portal, 'portal_catalog')

        # Create a new object within the workspaces area
        id_ = self._makeOne(self.portal.workspaces, 'File')

        object_ = getattr(self.portal.workspaces, id_)
        cpscatalog.indexObject(object_)

        transaction.commit()
        time.sleep(0.1)

        # Search it back
        kw = {
            # This is hindexObjectow the CatalogTool compute it.
            'path' : '/'.join(object_.getPhysicalPath())
            }

        results = cpscatalog.searchResults(**kw)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].uid, kw['path'])

        self.logout()

    def test_unindexObject(self):

        self.login('manager')

        transaction.begin()

        cpscatalog = getToolByName(self.portal, 'portal_catalog')

        # Create a new object within the workspaces area
        id_ = self._makeOne(self.portal.workspaces, 'File')

        object_ = getattr(self.portal.workspaces, id_)
        object_.reindexObject()

        transaction.commit()
        time.sleep(0.1)

        # Search it back
        kw = {
            # This is how the CatalogTool compute it.
            'path' : '/'.join(object_.getPhysicalPath())
            }

        # Search after indexation. Should match.
        results = cpscatalog.searchResults(**kw)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].uid, kw['path'])

        cpscatalog.unindexObject(object_)

        transaction.commit()
        time.sleep(0.1)

        # Find object back. Should be gone.
        results = cpscatalog.searchResults(**kw)
        self.assertEqual(len(results), 0)

        self.logout()

    def test_reindexObject(self):

        self.login('manager')

        transaction.begin()

        cpscatalog = getToolByName(self.portal, 'portal_catalog')

        # Create a new object within the workspaces area
        id_ = self._makeOne(self.portal.workspaces, 'File', title="The title",
                            Description="This is the description of the file")
        object_ = getattr(self.portal.workspaces, id_)
        cpscatalog.indexObject(object_)

        transaction.commit()
        time.sleep(0.1)

        # Search it back on path
        uid = '/'.join(object_.getPhysicalPath())
        kw = {
            # This is how the CatalogTool compute it.
            'path' : uid
            }

        results = cpscatalog.searchResults(**kw)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].uid, kw['path'])

        # Search on fulltext
        results = cpscatalog.searchResults(SearchableText="description")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].uid, uid)

        cpscatalog.reindexObject(object_)

        transaction.commit()
        time.sleep(0.1)
        
        # Search on uid
        kw = {
            # This is how the CatalogTool compute it.
            'uid' : uid
            }
        results = cpscatalog.searchResults(**kw)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].uid, uid)

        # Search on fulltext
        results = cpscatalog.searchResults(SearchableText="description")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].uid, uid)

        # Index just one field.
        cpscatalog.reindexObject(object_, idxs=('Title'))

        transaction.commit()
        time.sleep(0.1)

        # Search on uid
        results = cpscatalog.searchResults(**kw)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].uid, uid)

        # Search on fulltext
        results = cpscatalog.searchResults(SearchableText="description")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].uid, uid)

        self.logout()


    def test_basic_searchResults(self):

        self.login('manager')

        transaction.begin()

        cpscatalog = getToolByName(self.portal, 'portal_catalog')
        utool = getToolByName(self.portal, 'portal_url')

        # Create a new object within the workspaces area
        id_ = self._makeOne(self.portal.workspaces, 'File',
                            Description="test_basic_searchResults")

        object_ = getattr(self.portal.workspaces, id_)
        cpscatalog.indexObject(object_)

        transaction.commit()
        time.sleep(0.1)

        kw = {
            # This is how the CatalogTool compute it.
            'path' : '/'.join(object_.getPhysicalPath())
            }

        results = cpscatalog.searchResults(**kw)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].uid, kw['path'])

        # test return_fields, aka columns
        _marker = object()
        # check that the test is meaningful (depends on current profile)
        self.failIf(getattr(results[0], 'expires', _marker) is _marker)
        results = cpscatalog.searchResults(columns=('Description',), **kw)
        self.assertEqual(results[0].Description, "test_basic_searchResults")
        self.assertEqual(getattr(results[0], 'expires', None), None)

    def notest_removeDefunctEntries(self):

        self.login('manager')

        transaction.begin()

        cpscatalog = getToolByName(self.portal, 'portal_catalog')

        # Create a new object within the workspaces area
        id_ = self._makeOne(self.portal.workspaces, 'File')

        object_ = getattr(self.portal.workspaces, id_)
        object_.reindexObject()

        transaction.commit()
        time.sleep(0.1)

        # Search it back
        kw = {
            # This is how the CatalogTool compute it.
            'path' : '/'.join(object_.getPhysicalPath())
            }

        # Search after indexation. Should match.
        results = cpscatalog.searchResults(**kw)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].uid, kw['path'])

        # Delete without unindexing:
        self.portal.workspaces._delOb(id_)
        transaction.commit()
        time.sleep(0.1)

        # Find object back. Should still be there
        results = cpscatalog.searchResults(**kw)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].uid, kw['path'])

        cpscatalog.removeDefunctEntries()

        results = cpscatalog.searchResults(**kw)
        self.assertEqual(len(results), 0)

        self.logout()

    #
    # PRIVATE
    #

    def _makeOne(self, context, type_name, **kw):
        wftool = getToolByName(self.portal, 'portal_workflow')
        id_ = context.computeId()
        id_ = wftool.invokeFactoryFor(context, type_name, id_, **kw)
        return id_

def test_suite():
    suite = unittest.TestSuite()
    # This test is disabled by default, see note at top of this file.
    # suite.addTest(unittest.makeSuite(CPSLuceneCatalogTest))
    return suite

