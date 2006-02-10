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

import logging

from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from Globals import InitializeClass
from Acquisition import aq_parent
from Acquisition import aq_inner

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CatalogTool import CatalogTool

import zope.interface
from zope.component.interfaces import ComponentLookupError
from zope.app import zapi

from nuxeo.lucene.interfaces import ILuceneCatalog
from nuxeo.lucene.catalog import LuceneCatalog

from Products.CPSCore.ProxyBase import ProxyBase
from Products.CPSCore.PatchCatalogTool import IndexableObjectWrapper
from Products.CPSCore import utils as cpsutils

from zcatalogquery import ZCatalogQuery
from interfaces import ICPSLuceneCatalogTool

LOG = logging.getLogger("CPSLuceneCatalog")

class CPSLuceneCatalogTool(CatalogTool):
    """CPS Lucene Catalog
    """


    _properties = CatalogTool._properties + \
                  ({'id':'server_url',
                    'type':'string',
                    'mode':'w',
                    'label':'xml-rpc server URL',
                    },
                   {'id':'server_port',
                    'type':'string',
                    'mode': 'w',
                    'label':'xml-rpc server port',
                    },
                   )

    zope.interface.implements(ICPSLuceneCatalogTool)

    id = "portal_catalog"
    meta_type = "CPS Lucene Catalog Tool"

    server_url = 'http://localhost'
    server_port = 9180

    def __init__(self):
        utility = LuceneCatalog(self.server_url, self.server_port)
        self._setOb('_catalog', utility)

    def __url(self, ob):
        # XXX It would be better to have uid instead of rpath here.
        return '/'.join( ob.getPhysicalPath() )

    def getCatalog(self):
#        portal = aq_parent(aq_inner(self))
#        return zapi.getUtility(ILuceneCatalog, context=portal)
         return self._catalog

    def __len__(self):
        return 1

    def searchResults(self, REQUEST=None, **kw):
        """ Decorate ZCatalog.searchResults() with extra arguments

        o The extra arguments that the results to what the user would be
        allowed to see.
        """
        LOG.debug("SeachResults %s" % str(kw))
        query = ZCatalogQuery(REQUEST, **kw)
        return_fields, kw = query.get() 
        return self.getCatalog().searchResults(return_fields, **kw)

    def unrestrictedSearchResults(self, REQUEST=None, **kw):
        """Calls ZCatalog.searchResults() without any CMF-specific processing.

        o Permission:  Private (Python only)
        """
        LOG.debug("unrestrictedSearchResults %s" % str(kw))
        return []

    def reindexObject(self, object, idxs=[], update_metadata=1, uid=None):
        """ Update 'object' in catalog.

        o 'idxs', if passed, is a list of specific indexes to update
          (by default, all indexes are updated).

        o If 'update_metadata' is True, then update the metadata record
          in the catalog as well.

        o Permission:  Private (Python only)
        """
        LOG.debug("reindexObject %s idxs=%s update_metdata=%s" % (
            str(object), str(idxs), str(update_metadata)))

        if uid is None:
            uid = self.__url(object)
        if idxs != []:
            # Filter out invalid indexes.
            # XXX implement me nuxeo.lucene side
            #valid_indexes = self._catalog.indexes.keys()
            valid_indexes = idxs
            idxs = [i for i in idxs if i in valid_indexes]
        self.catalog_object(object, uid, idxs, update_metadata)

    def unindexObject(self, object):
        """ Remove 'object' from the catalog.

        o Permission:  Private (Python only)
        """
        LOG.debug("unindexObject %s" % str(object))
        return 
        default_uid = self._CatalogTool__url(object)
        proxy = None
        if isinstance(object, ProxyBase):
            proxy = object
            languages = proxy.getProxyLanguages()
        if proxy is None or len(languages) == 1:
            self.uncatalog_object(default_uid)
        else:
            for language in languages:
                # remove all translation of the proxy
                uid = default_uid + '/%s/%s' % (cpsutils.KEYWORD_VIEW_LANGUAGE,
                                                language)
                self.uncatalog_object(uid)

    def catalog_object(self, object, uid, idxs=[], update_metadata=1,
                       pghandler=None):

        LOG.debug("cat_catalog_object %s" % str(object))

        # Don't index repository objects or anything under them.
        repotool = getToolByName(self, 'portal_repository', None)
        if repotool is not None and repotool.isObjectUnderRepository(object):
            return
        
        # BBB: for Zope 2.7, which doesn't take a pghandler
        if pghandler is None:
            pgharg = ()
        else:
            pgharg = (pghandler,)
        
        wf = getattr(self, 'portal_workflow', None)
        if wf is not None:
            vars = wf.getCatalogVariablesFor(object)
        else:
            vars = {}
        
        # Filter out invalid indexes.
        # TODO : implement the API on nuxeo.lucene side
##        if idxs != []:
##            idxs = [i for i in idxs if self._catalog.indexes.has_key(i)]

        ### Not a proxy.
        if not isinstance(object, ProxyBase):
            w = IndexableObjectWrapper(vars, object)
            self.getCatalog().index(uid, w, idxs)
            return

        # Proxy with a viewLanguage uid.
        # Happens when the catalog is reindexed (refreshCatalog)
        # or when called by reindexObjectSecurity.
        path = uid.split('/')
        if cpsutils.KEYWORD_VIEW_LANGUAGE in path:
            if path.index(cpsutils.KEYWORD_VIEW_LANGUAGE) == len(path)-2:
                lang = path[-1]
            else:
                # Weird, but don't crash
                lang = None
            w = IndexableObjectWrapper(vars, object, lang, uid)
            self.getCatalog().index(uid, w, idxs)
            return
        
        # We reindex a normal proxy.
        # Find what languages are in the catalog for this proxy
        uid_view = uid + '/' + cpsutils.KEYWORD_VIEW_LANGUAGE
        had_languages = []
        for brain in self.unrestrictedSearchResults(path=uid_view):
            path = brain.getPath()
            had_languages.append(path[path.rindex('/')+1:])
        
        # Do we now have only one language?
        languages = object.getProxyLanguages()
        if len(languages) == 1:
            # Remove previous languages
            for lang in had_languages:
                self.uncatalog_object(uid_view+'/'+lang)
            # Index normal proxy
            w = IndexableObjectWrapper(vars, object)
            self.getCatalog().index(uid, w, idxs)
            return
        
        # We now have several languages (or none).
        # Remove old base proxy path
        if self.getCatalog().hasUID(uid):
            self.uncatalog_object(uid)
        # Also remove old languages
        for lang in had_languages:
            if lang not in languages:
                self.uncatalog_object(uid_view+'/'+lang)
        # Index all available translations of the proxy
        # with uid/viewLanguage/language for path
        for lang in languages:
            uid = uid_view + '/' + lang
            w = IndexableObjectWrapper(vars, object, lang, uid)
            self.getCatalog().index(uid, w, idxs)

    def uncatalog_object(self, uid):
        self.getCatalog().unindex(uid)

InitializeClass(CPSLuceneCatalogTool)
