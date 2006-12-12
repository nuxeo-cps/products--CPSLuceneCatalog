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
"""zcatalog query tests.
"""

import unittest

from DateTime import DateTime

from Products.CPSLuceneCatalog.zcatalogquery import ZCatalogQuery

class FakeCatalog(object):

    def __init__(self, field_ids=()):
        self._field_ids = field_ids

    def getCatalog(self):
        return self

    def getFieldNamesFor(self):
        return self._field_ids

class ZQueryTestCase(unittest.TestCase):

    def test_simple_query(self):
        cat = FakeCatalog(field_ids=('Title', 'Description'))
        zq = ZCatalogQuery(cat, REQUEST=None, Title='foo', Description='Bar')
        self.assertEqual(zq.getFieldsMap(),
                         ({'id': 'Description', 'value': 'Bar'},
                          {'id': 'Title', 'value': 'foo'})
                         )
        self.assertEqual(zq.getQueryOptions(), {})

    def test_bbb_zctitle(self):

        # CPS BBB tests

        cat = FakeCatalog(field_ids=('Title',))
        zq = ZCatalogQuery(cat, REQUEST=None, ZCTitle='foo')
        self.assertEqual(zq.getFieldsMap(),
                         ({'id': 'Title', 'value': 'foo'},)
                         )
        self.assertEqual(zq.getQueryOptions(), {})

    def test_internal_condition(self):
        cat = FakeCatalog(field_ids=('subject', 'Title'))
        zq = ZCatalogQuery(cat, REQUEST=None, subject={
            'query': ['Arts', 'Computers'], 'insert_condition': 'NOT'})
        self.assertEqual(zq.getFieldsMap(),
                         ({'id': 'subject',
                           'value': ['Arts', 'Computers'],
                           'condition': 'NOT'},))

        # Works with ZCTitle BBB too
        zq = ZCatalogQuery(cat, REQUEST=None, ZCTitle={
            'query': 'foo', 'insert_condition': 'OR'})
        self.assertEqual(zq.getFieldsMap(),
                         ({'id': 'Title',
                           'value': 'foo',
                           'condition': 'OR'},))

    def test_simple_date(self):
        cat = FakeCatalog(field_ids=('Date',))
        cdate = DateTime()
        zq = ZCatalogQuery(cat, REQUEST=None, Date=cdate)
        self.assertEqual(zq.getFieldsMap(),
                         ({'id': 'Date', 'value': cdate.ISO()},
                         ))

    def test_range_date_min(self):

        cat = FakeCatalog(field_ids=('Date',))
        cdate = DateTime()
        zq = ZCatalogQuery(cat, REQUEST=None, Date={'query':cdate, 'range': 'min'})
        self.assertEqual(zq.getFieldsMap(),
                         ({'usage': 'range:min', 'id': 'Date', 'value': cdate.ISO()},),
                         )

    def test_range_date_max(self):

        cat = FakeCatalog(field_ids=('Date',))
        cdate = DateTime()
        zq = ZCatalogQuery(cat, REQUEST=None, Date={'query':cdate, 'range': 'max'})
        self.assertEqual(zq.getFieldsMap(),
                         ({'usage': 'range:max', 'id': 'Date', 'value': cdate.ISO()},),
                         )

    def test_range_date_minmax(self):

        cat = FakeCatalog(field_ids=('Date',))
        cdate1 = DateTime()
        cdate2 = DateTime()
        zq = ZCatalogQuery(cat, REQUEST=None, Date={'query':[cdate1, cdate2],
                                                    'range': 'min:max'})
        self.assertEqual(zq.getFieldsMap(),
                         ({'usage': 'range:min:max', 'id': 'Date',
                           'value': [cdate1.ISO(), cdate2.ISO()]},),
                         )

    def test_range_string_minmax(self):

        cat = FakeCatalog(field_ids=('Title',))
        zq = ZCatalogQuery(cat, REQUEST=None, Title={'query':['a', 'z'],
                                                     'range': 'min:max'})
        self.assertEqual(zq.getFieldsMap(),
                         ({'usage': 'range:min:max', 'id': 'Title', 'value': ['a', 'z']},),
                         )

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ZQueryTestCase))
    return suite
