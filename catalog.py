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

import time
import logging
import gc

import transaction

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.CMFCore.utils import SimpleItemWithProperties
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import _getAuthenticatedUser
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.CatalogTool import CatalogTool

import zope.interface
from zope.component.interfaces import ComponentLookupError
from zope.app import zapi

from nuxeo.lucene.interfaces import ILuceneCatalog
from nuxeo.lucene.catalog import LuceneCatalog

from Products.CPSCore.ProxyBase import ProxyBase
from Products.CPSCore import utils as cpsutils

from Products.CPSUtil.timer import Timer

from zcatalogquery import ZCatalogQuery
from brain import CPSBrain
from wrapper import IndexableObjectWrapper

from interfaces import ICPSLuceneCatalogTool

LOG = logging.getLogger("CPSLuceneCatalog")

class CPSLuceneCatalogTool(CatalogTool):
    """CPS Lucene Catalog
    """

    zope.interface.implements(ICPSLuceneCatalogTool)

    id = "portal_catalog"
    meta_type = "CPS Lucene Catalog Tool"

    server_url = 'http://localhost:9180'

    security = ClassSecurityInfo()

    def __init__(self):
        utility = LuceneCatalog(self.server_url)
        self._setOb('_catalog', utility)

        # BBB for CPS <= 3.4
        self.Indexes = self

    def  __setattr__(self, id, value):
        if id == 'server_url':
            if not value.startswith('http://'):
                value = 'http://' + value
            LOG.info("Update nuxeo.lucene.catalog properties")
            setattr(self.getCatalog(), id, value)
            self._refreshCatalogProxy()
        CatalogTool.__setattr__(self, id, value)

    def __url(self, ob):
        # XXX It would be better to have uid instead of rpath here.
        return '/'.join( ob.getPhysicalPath() )

    def __len__(self):
        return len(self.getCatalog())

    def _refreshCatalogProxy(self):
        """Refresh the cached proxy
        """
        # Activate persistency
        self.getCatalog()._p_changed = 1
        # Remove cached proxy
        self.getCatalog()._v_proxy = None

    def getCatalog(self):
#        portal = aq_parent(aq_inner(self))
#        return zapi.getUtility(ILuceneCatalog, context=portal)
       return self._catalog

    #
    # API : Column
    #

    security.declareProtected(ManagePortal, 'addColumn')
    def addColumn(self, name, default_value=None):
        return self.getCatalog().addColumn(name, default_value)

    #
    # API : Fields

    security.declareProtected(ManagePortal, 'addField')
    def addField(self, **kw):
        self.getCatalog().addFieldFor(iface=None, **kw)

    security.declareProtected(ManagePortal, 'getFieldTypes')
    def getFieldTypes(self):
        # XXX : hardcoded for now and not complete
        fields =  (
            'Keyword',
            'MultiKeyword', # XXX will disappear in the future.
            'Text',
            'UnStored',
            'UnIndexed',
            'Date',
            'Path',
            'Sort',
            )
        return fields

    security.declareProtected(ManagePortal, 'getFieldConfs')
    def getFieldConfs(self):
        # It applies globally for now. nuxeo.lucene can discriminate
        # by iface though.
        cpsres = ()
        fieldconfs = self.getCatalog().getFieldConfigurationsFor()
        for each in fieldconfs:
            cpsres += (
                {'name' : each.name,
                 'attribute' : each.attribute,
                 'type' : each.type,
                 'analyzer' : each.analyzer,
                 },)
        return cpsres

    def clean(self):
        return self.getCatalog().clean()

    def _search(self, REQUEST=None, **kw):

        t = Timer('CPSLuceneCatalog._search', level=logging.DEBUG)

        # Construct query for nuxeo.lucene.catalog
        query = ZCatalogQuery(self, REQUEST, **kw)

        t.mark('Convert Query')

        results, nb_results = self.getCatalog().searchResults(
            search_fields=query.getFieldsMap(),
            options=query.getQueryOptions(),
            )

        t.mark('NXLucene query request')

        # Construct lite brains for BBB
        brains = []
        for mapping in results:
            one = CPSBrain(mapping).__of__(self)
            setattr(one, 'out_of', nb_results)
            brains.append(one)
        t.mark('Construct %s brain(s)' % str(len(brains)))
#        t.log()
        return brains

    def searchResults(self, REQUEST=None, **kw):
        """Searching with CPS security indexes.
        """

        LOG.debug("SeachResults %s" % str(kw))

        user = _getAuthenticatedUser(self)
        kw[ 'allowedRolesAndUsers' ] = self._listAllowedRolesAndUsers(user)

        return self._search(REQUEST, **kw)

    # Override CMFCore.CatalogTool alias
    __call__ = searchResults

    def unrestrictedSearchResults(self, REQUEST=None, **kw):
        """Calls ZCatalog.searchResults() without any CMF-specific processing.

        o Permission:  Private (Python only)
        """

        LOG.debug("unrestrictedSearchResults %s" % str(kw))

        return self._search(REQUEST, **kw)

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

        # Filter out invalid indexes will be done at nuxeo.lucene level.
        self.catalog_object(object, uid, idxs, update_metadata)

    def unindexObject(self, object):
        """ Remove 'object' from the catalog.

        o Permission:  Private (Python only)
        """

        # Don't index repository objects or anything under them.
        repotool = getToolByName(self, 'portal_repository', None)
        if repotool is not None and repotool.isObjectUnderRepository(object):
            return

        LOG.debug("unindexObject %s" % str(object))

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

        # Filter out invalid indexes will be done at nuxeo.lucene level.

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

    #
    # BBB for CPS <= 3.4
    #

    def objectValues(self, spec=None):
        return []

    def indexes(self):
        return []

    def addIndex(self, name, type,extra=None):
        pass

    #
    # ZMI
    #

    # Those properties are here only to display the values in ZMI.
    # The actual used properties are on the nuxeo.lucene catalog
    # utility
    _properties = CatalogTool._properties + \
                  ({'id':'server_url',
                    'type':'string',
                    'mode':'w',
                    'label':'xml-rpc server URL',
                    },
                   )

    manage_options = (CatalogTool.manage_options[2],
                      { 'label' : 'Manage XML-RPC Server',
                        'action' : 'manage_advancedForm',
                        },
                      { 'label' : 'Schema',
                        'action' : 'manage_catalogSchema',
                        },
                      { 'label' : 'Fields',
                        'action' : 'manage_catalogFields',
                        },
                      )

    security.declareProtected(ManagePortal, 'manage_advancedForm')
    manage_advancedForm = PageTemplateFile(
        'zmi/manage_advancedForm.pt', globals())

    security.declareProtected(ManagePortal, 'manage_catalogFields')
    manage_catalogFields = PageTemplateFile(
        'zmi/manage_catalogFields.pt', globals())

    security.declareProtected(ManagePortal, 'manage_catalogSchema')
    manage_catalogSchema = PageTemplateFile(
        'zmi/manage_catalogSchema.pt', globals())

    security.declareProtected(ManagePortal, 'manage_reindexProxies')
    def manage_reindexProxies(self, idxs=(), REQUEST=None):
        """Reindex  an existing complete CPS instance with content.

        It checks all the CPS proxies from the proxies tool.
        """

        start = time.time()

        grabbed = 0
        reindexed = 0

        pxtool = getToolByName(self, 'portal_proxies')
        utool = getToolByName(self, 'portal_url')

        rpaths = pxtool._rpath_to_infos

        portal = utool.getPortalObject()

#        rpaths = ('/gcac_preprod/sections/ouvrages/ouvrage-test-eba',)
        for rpath in rpaths:
            timer = Timer("Get proxy information", level=20)

            proxy = portal.unrestrictedTraverse(rpath)
            timer.mark("Get proxy from rpath")

            self.reindexObject(proxy, idxs=list(idxs))
            timer.mark('Scheduled for reindexation')

            transaction.commit()
            timer.mark('Reindexation')

            grabbed +=1

            proxy._p_deactivate()
            timer.mark("ghostification")

            if grabbed % 100 == 0:

                gc.collect()
                timer.mark("gc.collect()")

#"            if grabbed >= 100:
#"                break

            LOG.info("Proxy number %s grabbed !" %str(grabbed))
            timer.log()

        # If less than 100 proxies reindexed.
        if grabbed < 100:
            gc.collect()

        stop = time.time()
        LOG.info("Reindexation done in %s secondes" % str(stop-start))

        # Optimize the store
        self.getCatalog().optimize()

        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(
                self.absolute_url() + '/manage_advancedForm')

    security.declareProtected(ManagePortal, 'manage_reindexSelectedFields')
    def manage_reindexSelectedFields(self, fields=(), REQUEST=None):
        """Reindex selected fields.
        """

        if fields:
            self.manage_reindexProxies(idxs=fields, REQUEST=REQUEST)

        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(
                self.absolute_url() + '/manage_catalogFields')

    security.declareProtected(ManagePortal, 'manage_optimize')
    def manage_optimize(self):
        """Optimier the indexes store
        """
        self.getCatalog().optimize()

    security.declareProtected(ManagePortal, 'manage_clean')
    def manage_clean(self):
        """CLean the indexes store.
        """
        self.clean()

InitializeClass(CPSLuceneCatalogTool)
