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

import gc
import logging

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

    server_url = 'http://localhost'
    server_port = 9180

    security = ClassSecurityInfo()

    def __init__(self):
        utility = LuceneCatalog(self.server_url, self.server_port)
        self._setOb('_catalog', utility)

        # BBB for CPS <= 3.4
        self.Indexes = self

    def __url(self, ob):
        # XXX It would be better to have uid instead of rpath here.
        return '/'.join( ob.getPhysicalPath() )

    def __len__(self):
        return len(self.getCatalog())

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
            'Text',
            'UnStored',
            'UnIndexed',
            'Date',
            'Path',
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
                {'attribute' : each.attribute,
                 'type' : each.type,
                 'analyzer' : each.analyzer,
                 },)
        return cpsres

    def clean(self):
        return self.getCatalog().clean()

    def searchResults(self, REQUEST=None, **kw):
        """Searching...
        """

        user = _getAuthenticatedUser(self)
        kw[ 'allowedRolesAndUsers' ] = self._listAllowedRolesAndUsers(user)

        from Products.CPSUtil.timer import Timer
        t = Timer('CPSLuceneCatalog.searchResults()', level=logging.DEBUG)

        LOG.debug("SeachResults %s" % str(kw))

        query = ZCatalogQuery(REQUEST, **kw)

        # XXX this sucks
        kw = query.get()
        t.mark('Convert Query')

        # Get the name of the fields that need to be returned.
        return_fields = tuple(self.getCatalog().schema.keys())
        return_fields += ('uid',)

        results = self.getCatalog().searchResults(return_fields, kw)
        t.mark('NXLucene query request')

        # Construct lite brains for BBB
        brains = []
        for mapping in results:
            brains.append(CPSBrain(mapping).__of__(self))
        t.mark('Construct brains')
        t.log()
        return brains

    # Override CMFCore.CatalogTool alias
    __call__ = searchResults

    def unrestrictedSearchResults(self, REQUEST=None, **kw):
        """Calls ZCatalog.searchResults() without any CMF-specific processing.

        o Permission:  Private (Python only)
        """
        LOG.debug("unrestrictedSearchResults %s" % str(kw))

        query = ZCatalogQuery(REQUEST, **kw)

        # XXX this sucks
        kw = query.get()

        # Get the name of the fields that need to be returned.
        return_fields = tuple(self.getCatalog().schema.keys())
        return_fields += ('uid',)

        results = self.getCatalog().searchResults(return_fields, kw)

        # Construct lite brains for BBB
        brains = []
        for mapping in results:
            brains.append(CPSBrain(mapping).__of__(self))
        return brains

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

    manage_options = (SimpleItemWithProperties.manage_options[0]
                      ,) + \
                      ({ 'label' : 'Advanced',
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

    security.declareProtected(ManagePortal, 'manage_reindex')
    def manage_reindex(self, REQUEST=None):
        """Reindex an existing instance.
        """

        # XXX rough implementation for tests.

        from zLOG import LOG, INFO
        from Products.CPSUtil.timer import Timer

        def reindexContainer(container):
            """Reindex the container and its direct children
            """
            timer = Timer('indexObject', level=INFO)

            LOG("Index object", INFO, container.absolute_url())
            try:
                container._reindexObject()
            except AttributeError:
                # Not a CPS Proxy
                container.reindexObject()

            timer.mark('Indexation')

            timer.log()

            # Flush mem
#            transaction.commit()
            gc.collect()

            if hasattr(container, 'objectIds'):
                for id_ in container.objectIds():
                    reindexContainer(getattr(container, id_))

        portal = getToolByName(self, 'portal_url').getPortalObject()
        areas = (
                'workspaces',
                'sections',
                'members',
                )
        for each in areas:
            each = getattr(portal, each)
            reindexContainer(each)

        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(
                self.absolute_url() + '/manage_advancedForm')

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
